import uuid as uuid_module
from rest_framework import generics, filters, status, views, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import connection
from .models import Product, ProductReview, ProductQuestion
from .serializers import ProductListSerializer, ProductDetailSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

class ProductListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all().filter(status='active', approval_status='approved')
    serializer_class = ProductListSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = {
        'category_id': ['exact'],
        'is_featured': ['exact'],
        'is_new_arrival': ['exact'],
        'is_on_sale': ['exact'],
        'price': ['gte', 'lte'],
        'brand': ['exact', 'icontains'],
        'vendor_id': ['exact'],
    }
    
    # Search fields (Search vector in DB is more complex, using simple icontains for now)
    search_fields = ['name', 'description', 'brand', 'sku']
    
    # Ordering fields
    ordering_fields = ['price', 'added_date', 'rating', 'orders_count']
    ordering = ['-added_date']

    @extend_schema(
        summary="List all products",
        description="Get a list of products with filtering, searching and sorting capabilities.",
        parameters=[
            OpenApiParameter(name='price__gte', description='Minimum price', required=False, type=float),
            OpenApiParameter(name='price__lte', description='Maximum price', required=False, type=float),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_field = 'id'

class FeaturedProductsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_featured=True, status='active', approval_status='approved')
    serializer_class = ProductListSerializer
    pagination_class = None

class NewArrivalsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_new_arrival=True, status='active', approval_status='approved').order_by('-added_date')
    serializer_class = ProductListSerializer
    pagination_class = None

class OnSaleProductsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_on_sale=True, status='active', approval_status='approved')
    serializer_class = ProductListSerializer

class ProductSearchView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'brand']
    
    def get_queryset(self):
        return Product.objects.filter(status='active', approval_status='approved')


class ProductSizeChartView(views.APIView):
    """GET /api/products/{id}/size-chart/"""
    permission_classes = []
    authentication_classes = []

    @extend_schema(responses={200: {'type': 'object'}, 404: None})
    def get(self, request, id):
        product = get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT t.id, t.name, t.category_id, t.subcategory, t.measurement_types, 
                       t.measurement_instructions, t.template_data, t.size_recommendations
                FROM product_size_chart_assignments a
                JOIN vendor_size_chart_templates t ON (a.template_id = t.id OR a.vendor_template_id = t.id)
                WHERE a.product_id = %s AND t.is_active = true AND t.approval_status = 'approved'
                LIMIT 1
            """, [str(product.id)])
            row = c.fetchone()
            cols = [col[0] for col in c.description] if c.description else []
        if not row:
            return Response({"detail": "No size chart for this product."}, status=404)
        data = dict(zip(cols, row)) if cols else {}
        for k, v in list(data.items()):
            if hasattr(v, 'isoformat'): data[k] = v.isoformat()
            elif isinstance(v, uuid_module.UUID): data[k] = str(v)
        template_data = data.get('template_data')
        data['entries'] = template_data.get('entries', []) if isinstance(template_data, dict) else []
        return Response(data)


class ProductViewTrackView(views.APIView):
    """POST /api/products/{id}/view/ — track product view"""
    permission_classes = []

    @extend_schema(responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}})
    def post(self, request, id):
        product = get_object_or_404(Product, id=id, status='active', approval_status='approved')
        try:
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO product_views (id, product_id, user_id, created_at)
                    VALUES (gen_random_uuid(), %s, %s, NOW())
                """, [str(product.id), str(request.user.id) if request.user.is_authenticated else None])
        except Exception:
            pass
        return Response({"success": True})


class ProductReviewsListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/products/{id}/reviews/"""
    permission_classes = []
    authentication_classes = []

    def get_serializer_class(self):
        from .serializers import ProductReviewSerializer, ProductReviewCreateSerializer
        return ProductReviewCreateSerializer if self.request.method == 'POST' else ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return []  # GET is public

    def get_queryset(self):
        return ProductReview.objects.filter(product_id=self.kwargs['id'], status='published').select_related('user').order_by('-created_at')

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs['id'], status='active', approval_status='approved')
        if ProductReview.objects.filter(product=product, user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "You have already reviewed this product."})
        d = serializer.validated_data
        self.created_review = ProductReview.objects.create(
            product=product, user=self.request.user, order_id=d.get('order_id'),
            rating=d['rating'], title=d.get('title', ''), content=d.get('content', ''),
            images=d.get('images', []), verified_purchase=True
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        from .serializers import ProductReviewSerializer
        return Response(ProductReviewSerializer(self.created_review).data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=self.kwargs['id'], status='active', approval_status='approved')
        reviews = ProductReview.objects.filter(product=product, status='published').select_related('user')

        # Gap 9: Rating filter
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            try:
                reviews = reviews.filter(rating=int(rating_filter))
            except (ValueError, TypeError):
                pass

        # Gap 8: has_media filter (getReviewsWithMedia)
        has_media = request.query_params.get('has_media')
        if has_media and has_media.lower() == 'true':
            from django.db.models import Q
            reviews = reviews.exclude(images=[]).exclude(images__isnull=True)

        # Gap 9: Sort support
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        allowed_sorts = {'created_at', 'rating', 'helpful_count'}
        if sort_by not in allowed_sorts:
            sort_by = 'created_at'
        order_prefix = '-' if sort_order == 'desc' else ''
        reviews = reviews.order_by(f'{order_prefix}{sort_by}')

        from .serializers import ProductReviewSerializer
        from django.db.models import Avg, Count
        agg = ProductReview.objects.filter(product=product, status='published').aggregate(avg=Avg('rating'), total=Count('id'))

        # Compute histogram
        histogram = [0, 0, 0, 0, 0]
        from django.db.models import Count as DjCount
        rating_counts = ProductReview.objects.filter(
            product=product, status='published'
        ).values('rating').annotate(cnt=DjCount('id'))
        for rc in rating_counts:
            idx = rc['rating'] - 1
            if 0 <= idx < 5:
                histogram[idx] = rc['cnt']

        return Response({
            "count": reviews.count(),
            "results": ProductReviewSerializer(reviews, many=True).data,
            "summary": {
                "average_rating": float(agg['avg'] or 0),
                "total_reviews": agg['total'] or 0,
                "histogram": histogram,
            }
        })


class CanReviewProductView(views.APIView):
    """GET /api/products/{id}/can-review/
    Gaps 6+7: canUserReviewProduct + getUserOrderForProduct.
    Checks if the user has a delivered/completed order for this product
    and whether they've already reviewed it."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        product = get_object_or_404(Product, id=id, status='active', approval_status='approved')
        user = request.user

        has_existing_review = ProductReview.objects.filter(product=product, user=user).exists()

        # Check for a delivered/completed order containing this product
        from orders.models import OrderItem, Order
        order_item = OrderItem.objects.filter(
            product=product,
            order__user=user,
            order__status__in=['delivered', 'completed'],
        ).select_related('order').first()

        can_review = order_item is not None and not has_existing_review

        return Response({
            'can_review': can_review,
            'has_existing_review': has_existing_review,
            'order_id': str(order_item.order_id) if order_item else None,
        })


class ProductQAListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/products/{id}/qa/"""
    permission_classes = []
    authentication_classes = []

    def get_serializer_class(self):
        from .serializers import ProductQuestionSerializer, ProductQuestionCreateSerializer
        return ProductQuestionCreateSerializer if self.request.method == 'POST' else ProductQuestionSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return []

    def get_queryset(self):
        return ProductQuestion.objects.filter(product_id=self.kwargs['id'], status='published').order_by('-created_at')

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs['id'], status='active', approval_status='approved')
        d = serializer.validated_data
        self.created_qa = ProductQuestion.objects.create(
            product=product, user=self.request.user, question=d['question']
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        from .serializers import ProductQuestionSerializer
        return Response(ProductQuestionSerializer(self.created_qa).data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        from .serializers import ProductQuestionSerializer
        from django.db.models import Q
        product = get_object_or_404(Product, id=self.kwargs['id'], status='active', approval_status='approved')
        qa = ProductQuestion.objects.filter(product=product, status='published').select_related('user')

        # Gap 11: searchQuestions
        search = request.query_params.get('search', '').strip()
        if search:
            qa = qa.filter(
                Q(question__icontains=search) |
                Q(answer__icontains=search) |
                Q(vendor_response__icontains=search)
            )

        # Gap 12: hasAnswer filter
        has_answer = request.query_params.get('has_answer')
        if has_answer is not None:
            if has_answer.lower() == 'true':
                qa = qa.filter(
                    Q(answer__isnull=False) & ~Q(answer='') |
                    Q(vendor_response__isnull=False) & ~Q(vendor_response='')
                )
            elif has_answer.lower() == 'false':
                qa = qa.filter(
                    (Q(answer__isnull=True) | Q(answer='')) &
                    (Q(vendor_response__isnull=True) | Q(vendor_response=''))
                )

        qa = qa.order_by('-created_at')
        answered = ProductQuestion.objects.filter(product=product, status='published').exclude(answer__isnull=True).exclude(answer='').count()
        total = ProductQuestion.objects.filter(product=product, status='published').count()
        return Response({
            "count": qa.count(),
            "results": ProductQuestionSerializer(qa, many=True).data,
            "stats": {"total": total, "answered": answered, "unanswered": total - answered}
        })


class ProductQAAnswerView(views.APIView):
    """POST /api/products/{id}/qa/{qa_id}/answer/
    Gap 10: submitAnswer — vendor answers a customer question."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, qa_id):
        qa = get_object_or_404(ProductQuestion, id=qa_id, product_id=id, status='published')
        answer_text = request.data.get('answer', '').strip()
        if not answer_text:
            return Response({'error': 'Answer text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify user is the vendor for this product
        from vendors.models import Vendor
        product = get_object_or_404(Product, id=id)
        try:
            vendor = Vendor.objects.get(user=request.user, status='approved')
            if str(product.vendor_id) != str(vendor.id):
                return Response({'error': 'Only the product vendor can answer questions.'}, status=status.HTTP_403_FORBIDDEN)
        except Vendor.DoesNotExist:
            return Response({'error': 'Only vendors can answer questions.'}, status=status.HTTP_403_FORBIDDEN)

        from django.utils import timezone as tz
        qa.answer = answer_text
        qa.answered_by = request.user.id
        qa.answered_at = tz.now()
        qa.status = 'published'
        qa.save(update_fields=['answer', 'answered_by', 'answered_at', 'status', 'updated_at'])

        from .serializers import ProductQuestionSerializer
        return Response(ProductQuestionSerializer(qa).data)


class ProductQAHelpfulView(views.APIView):
    """POST /api/products/{id}/qa/{qa_id}/helpful/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def post(self, request, id, qa_id):
        qa = get_object_or_404(ProductQuestion, id=qa_id, product_id=id, status='published')
        qa.is_helpful_count = (qa.is_helpful_count or 0) + 1
        qa.save(update_fields=['is_helpful_count'])
        return Response({"success": True, "is_helpful_count": qa.is_helpful_count})


class ImageSearchView(views.APIView):
    """
    POST /api/products/search-by-image/

    Accepts an image file, analyzes it with OpenAI Vision, and returns matching products.
    Mirrors mobile's chatbot_controller._processImageSearch() flow.

    Request: multipart/form-data with 'image' file field
    Response: {
        "description": "AI description of the product in the image",
        "products": [ ... product objects ... ],
        "count": int
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={'type': 'object', 'properties': {
            'image': {'type': 'string', 'format': 'binary'},
        }},
        responses={200: {'type': 'object'}},
    )
    def post(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate image type
        content_type = image_file.content_type or 'image/jpeg'
        if not content_type.startswith('image/'):
            return Response({'error': 'File must be an image.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate size (max 20MB, matching mobile)
        if image_file.size > 20 * 1024 * 1024:
            return Response({'error': 'Image file too large (max 20MB).'}, status=status.HTTP_400_BAD_REQUEST)

        # Read image bytes
        image_bytes = image_file.read()

        # Analyze image
        from ai_services.image_analysis_service import analyze_image
        description = analyze_image(image_bytes, content_type)

        # Search products
        from ai_services.product_search_service import search_by_image_description
        products = search_by_image_description(description, limit=10)

        # Serialize products
        serialized = []
        for p in products:
            serialized.append({
                'id': str(p.get('id', '')),
                'name': p.get('name', ''),
                'description': p.get('description', ''),
                'price': float(p.get('price', 0)) if p.get('price') is not None else 0,
                'images': p.get('images', ''),
                'sizes': p.get('sizes', []),
                'rating': float(p.get('rating', 0)) if p.get('rating') is not None else 0,
                'reviews': p.get('reviews', 0),
                'in_stock': p.get('in_stock', True),
                'category_id': str(p.get('category_id', '')) if p.get('category_id') else None,
                'brand': p.get('brand', ''),
                'discount_percentage': float(p.get('discount_percentage', 0)) if p.get('discount_percentage') is not None else None,
                'is_on_sale': p.get('is_on_sale', False),
                'sale_price': float(p.get('sale_price', 0)) if p.get('sale_price') is not None else None,
                'is_featured': p.get('is_featured', False),
                'is_new_arrival': p.get('is_new_arrival', False),
                'vendor_id': str(p.get('vendor_id', '')) if p.get('vendor_id') else None,
                'vendor_name': p.get('vendor_name', ''),
                'sku': p.get('sku', ''),
                'status': p.get('status', 'active'),
                'colors': p.get('colors', {}),
            })

        return Response({
            'description': description,
            'products': serialized,
            'count': len(serialized),
        })


class ProductDeliveryInfoView(views.APIView):
    """GET /api/products/{id}/delivery-info/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, return_window_days, cod_eligible, free_delivery,
                       shipping_fee, eta_min_days, eta_max_days, delivery_notes, 
                       created_at, updated_at
                FROM delivery_info WHERE product_id = %s LIMIT 1
            """, [str(id)])
            row = c.fetchone()
            cols = [col[0] for col in c.description] if c.description else []
        if not row:
            return Response({"detail": "No delivery info for this product."}, status=404)
        data = dict(zip(cols, row))
        for k, v in list(data.items()):
            if hasattr(v, 'isoformat'):
                data[k] = v.isoformat()
            elif isinstance(v, uuid_module.UUID):
                data[k] = str(v)
        return Response(data)


class ProductWarrantyInfoView(views.APIView):
    """GET /api/products/{id}/warranty-info/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, type, duration, description, terms_url,
                       coverage_details, exclusions, created_at, updated_at
                FROM warranty_info WHERE product_id = %s LIMIT 1
            """, [str(id)])
            row = c.fetchone()
            cols = [col[0] for col in c.description] if c.description else []
        if not row:
            return Response({"detail": "No warranty info for this product."}, status=404)
        data = dict(zip(cols, row))
        for k, v in list(data.items()):
            if hasattr(v, 'isoformat'):
                data[k] = v.isoformat()
            elif isinstance(v, uuid_module.UUID):
                data[k] = str(v)
        return Response(data)


class ProductOffersView(views.APIView):
    """GET /api/products/{id}/offers/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, type, code, description, expiry_date,
                       icon_url, is_active, sort_order, created_at, updated_at
                FROM product_offers
                WHERE product_id = %s AND is_active = true
                ORDER BY sort_order
            """, [str(id)])
            rows = _dictfetchall(c)
        return Response({"count": len(rows), "results": rows})


class ProductHighlightsView(views.APIView):
    """GET /api/products/{id}/highlights/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, label, icon_url, sort_order, created_at
                FROM product_highlights
                WHERE product_id = %s ORDER BY sort_order
            """, [str(id)])
            rows = _dictfetchall(c)
        return Response({"count": len(rows), "results": rows})


class FeaturePostersView(views.APIView):
    """GET /api/products/{id}/feature-posters/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, title, subtitle, media_url, aspect_ratio,
                       cta_label, sort_order, is_active, created_at
                FROM feature_posters
                WHERE product_id = %s AND is_active = true
                ORDER BY sort_order
            """, [str(id)])
            rows = _dictfetchall(c)
        return Response({"count": len(rows), "results": rows})


class ProductSpecificationsView(views.APIView):
    """GET /api/products/{id}/specifications/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, group_name, spec_name, spec_value, sort_order, created_at
                FROM product_specifications
                WHERE product_id = %s ORDER BY sort_order
            """, [str(id)])
            rows = _dictfetchall(c)

        # Group by group_name (mobile expects this format)
        groups = {}
        for spec in rows:
            gn = spec.get('group_name', 'General')
            if gn not in groups:
                groups[gn] = {'group': gn, 'rows': []}
            groups[gn]['rows'].append({
                'name': spec.get('spec_name', ''),
                'value': spec.get('spec_value', ''),
            })

        return Response({
            "count": len(rows),
            "groups": list(groups.values()),
            "raw": rows,
        })


class ProductRecommendationsView(views.APIView):
    """GET /api/products/{id}/recommendations/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        product = get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, similar_products, from_seller_products,
                       you_might_also_like, algorithm_version, confidence_score, last_updated
                FROM product_recommendations
                WHERE product_id = %s LIMIT 1
            """, [str(id)])
            row = c.fetchone()
            cols = [col[0] for col in c.description] if c.description else []

        if not row:
            # Fallback: return products from same category
            with connection.cursor() as c:
                c.execute("""
                    SELECT id, name, price, images, rating, reviews, in_stock,
                           discount_percentage, is_on_sale, sale_price, brand
                    FROM products
                    WHERE category_id = %s AND id != %s
                      AND status = 'active' AND approval_status = 'approved' AND in_stock = true
                    ORDER BY rating DESC LIMIT 10
                """, [str(product.category_id), str(id)])
                fallback_rows = _dictfetchall(c)
            return Response({
                "similar_products": fallback_rows,
                "from_seller_products": [],
                "you_might_also_like": [],
            })

        data = dict(zip(cols, row))
        for k, v in list(data.items()):
            if hasattr(v, 'isoformat'):
                data[k] = v.isoformat()
            elif isinstance(v, uuid_module.UUID):
                data[k] = str(v)
            elif isinstance(v, list):
                data[k] = [str(x) if isinstance(x, uuid_module.UUID) else x for x in v]

        # Fetch actual product objects for similar_products
        similar_ids = data.get('similar_products', []) or []
        from_seller_ids = data.get('from_seller_products', []) or []
        you_might_ids = data.get('you_might_also_like', []) or []

        def _fetch_products_by_ids(ids):
            if not ids:
                return []
            str_ids = [str(i) for i in ids]
            placeholders = ','.join(['%s'] * len(str_ids))
            with connection.cursor() as c:
                c.execute(f"""
                    SELECT id, name, price, images, rating, reviews, in_stock,
                           discount_percentage, is_on_sale, sale_price, brand
                    FROM products
                    WHERE id::text IN ({placeholders})
                      AND status = 'active' AND approval_status = 'approved'
                """, str_ids)
                return _dictfetchall(c)

        return Response({
            "similar_products": _fetch_products_by_ids(similar_ids),
            "from_seller_products": _fetch_products_by_ids(from_seller_ids),
            "you_might_also_like": _fetch_products_by_ids(you_might_ids),
        })


class ProductReviewsSummaryView(views.APIView):
    """GET /api/products/{id}/reviews-summary/"""
    permission_classes = []
    authentication_classes = []

    def get(self, request, id):
        get_object_or_404(Product, id=id, status='active', approval_status='approved')
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, with_media, histogram, total_reviews,
                       average_rating, last_updated
                FROM product_reviews_summary
                WHERE product_id = %s LIMIT 1
            """, [str(id)])
            row = c.fetchone()
            cols = [col[0] for col in c.description] if c.description else []

        if not row:
            return Response({
                "total_reviews": 0, "average_rating": 0.0,
                "with_media": 0, "histogram": [0, 0, 0, 0, 0],
            })

        data = dict(zip(cols, row))
        for k, v in list(data.items()):
            if hasattr(v, 'isoformat'):
                data[k] = v.isoformat()
            elif isinstance(v, uuid_module.UUID):
                data[k] = str(v)
        return Response(data)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _dictfetchall(cursor) -> list:
    cols = [col[0] for col in cursor.description] if cursor.description else []
    rows = []
    for row in cursor.fetchall():
        d = {}
        for i, col_name in enumerate(cols):
            val = row[i]
            if isinstance(val, uuid_module.UUID):
                val = str(val)
            elif hasattr(val, 'isoformat'):
                val = val.isoformat()
            d[col_name] = val
        rows.append(d)
    return rows
