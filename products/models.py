from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Storing image URL as text to match existing DB schema initially
    images = models.TextField(default='https://example.com/default.jpg') 
    video_url = models.TextField(null=True, blank=True)
    # Use ArrayField because DB column is ARRAY type
    sizes = ArrayField(models.TextField(), default=list, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews = models.IntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    category_id = models.UUIDField(null=True, blank=True)
    subcategory_id = models.UUIDField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    added_date = models.DateTimeField(auto_now_add=True)
    vendor_id = models.UUIDField(null=True, blank=True) # Foreign key to Vendor
    approval_status = models.CharField(max_length=20, default='approved')
    sku = models.TextField(unique=True, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    colors = models.JSONField(default=dict)
    
    # Newly added fields from db.md
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    # search_vector is a generated column in DB, removed to avoid insert errors
    dimensions = models.JSONField(null=True, blank=True)
    shipping_required = models.BooleanField(null=True, blank=True)
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    tags = ArrayField(models.TextField(), default=list, null=True, blank=True)
    color_images = models.JSONField(null=True, blank=True)
    size_chart_template_id = models.UUIDField(null=True, blank=True)
    custom_size_chart_data = models.JSONField(null=True, blank=True)
    size_guide_type = models.TextField(null=True, blank=True)
    # embedding is a vector column in DB, removed to avoid insert errors
    subtitle = models.TextField(null=True, blank=True)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.TextField(null=True, blank=True)
    orders_count = models.IntegerField(null=True, blank=True)
    box_contents = ArrayField(models.TextField(), default=list, null=True, blank=True)
    usage_instructions = ArrayField(models.TextField(), default=list, null=True, blank=True)
    care_instructions = ArrayField(models.TextField(), default=list, null=True, blank=True)
    safety_notes = ArrayField(models.TextField(), default=list, null=True, blank=True)
    seo_data = models.JSONField(null=True, blank=True)
    base_currency = models.TextField(null=True, blank=True)
    converted_prices = models.JSONField(null=True, blank=True)
    product_type = models.TextField(null=True, blank=True)
    sizing_required = models.BooleanField(null=True, blank=True)
    size_chart_override = models.TextField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    cod_allowed = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['-added_date']

    def __str__(self):
        return self.name


class ProductReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.UUIDField(null=True, blank=True)
    rating = models.IntegerField()
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    images = ArrayField(models.TextField(), default=list, blank=True)
    verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    reported_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='published')
    vendor_response = models.TextField(null=True, blank=True)
    vendor_response_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_reviews'


class ProductQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_qa')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField(null=True, blank=True)
    answered_by = models.UUIDField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    is_helpful_count = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='published')
    vendor_response = models.TextField(null=True, blank=True)
    vendor_response_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vendor_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'product_qa'

class MediaUploadJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, default='pending') # pending, completed, failed
    result_url = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'media_upload_jobs'

class ProductApprovalQueue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    vendor_id = models.UUIDField()
    action_type = models.TextField()
    status = models.TextField()
    submitted_data = models.JSONField()
    admin_notes = models.TextField(null=True, blank=True)
    reviewed_by = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    priority = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_approval_queue'

class SizeChartTemplates(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    category_id = models.UUIDField(null=True, blank=True)
    subcategory = models.TextField(null=True, blank=True)
    measurement_types = models.JSONField()
    measurement_instructions = models.TextField(null=True, blank=True)
    size_recommendations = models.JSONField(null=True, blank=True)
    chart_type = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'size_chart_templates'

class SizeChartEntries(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_id = models.UUIDField(null=True, blank=True)
    size_name = models.TextField()
    measurements = models.JSONField()
    sort_order = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'size_chart_entries'

class ProductOffers(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    type = models.TextField()
    code = models.TextField(null=True, blank=True)
    description = models.TextField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    icon_url = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_offers'

class ProductHighlights(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    label = models.TextField()
    icon_url = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_highlights'

class FeaturePosters(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    title = models.TextField()
    subtitle = models.TextField()
    media_url = models.TextField()
    aspect_ratio = models.TextField(null=True, blank=True)
    cta_label = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'feature_posters'

class ProductSpecifications(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    group_name = models.TextField()
    spec_name = models.TextField()
    spec_value = models.TextField()
    sort_order = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_specifications'

class DeliveryInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True)
    return_window_days = models.IntegerField(null=True, blank=True)
    cod_eligible = models.BooleanField(null=True, blank=True)
    free_delivery = models.BooleanField(null=True, blank=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    eta_min_days = models.IntegerField(null=True, blank=True)
    eta_max_days = models.IntegerField(null=True, blank=True)
    delivery_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'delivery_info'

class WarrantyInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True)
    type = models.TextField()
    duration = models.TextField()
    description = models.TextField(null=True, blank=True)
    terms_url = models.TextField(null=True, blank=True)
    coverage_details = models.TextField(null=True, blank=True)
    exclusions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'warranty_info'

class ProductReviewsSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True)
    with_media = models.IntegerField(null=True, blank=True)
    histogram = ArrayField(models.IntegerField(), default=list, blank=True, null=True)
    total_reviews = models.IntegerField(null=True, blank=True)
    average_rating = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_reviews_summary'

class ProductRecommendations(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True)
    similar_products = ArrayField(models.UUIDField(), default=list, blank=True, null=True)
    from_seller_products = ArrayField(models.UUIDField(), default=list, blank=True, null=True)
    you_might_also_like = ArrayField(models.UUIDField(), default=list, blank=True, null=True)
    algorithm_version = models.TextField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_recommendations'

class ProductSizeChartAssignments(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    template_id = models.UUIDField(null=True, blank=True)
    vendor_template_id = models.UUIDField(null=True, blank=True)
    custom_data = models.JSONField(null=True, blank=True)
    assignment_type = models.TextField()
    assigned_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_size_chart_assignments'

class SizeChartAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    template_id = models.UUIDField(null=True, blank=True)
    vendor_template_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    action_type = models.TextField()
    selected_size = models.TextField(null=True, blank=True)
    session_id = models.TextField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'size_chart_analytics'

class DynamicSizeChartFields(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    size_chart_id = models.UUIDField()
    field_name = models.TextField()
    field_type = models.TextField()
    field_unit = models.TextField(null=True, blank=True)
    is_required = models.BooleanField(null=True, blank=True)
    field_options = models.JSONField(null=True, blank=True)
    placeholder_text = models.TextField(null=True, blank=True)
    help_text = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    validation_rules = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'dynamic_size_chart_fields'

class SizeChartMigrationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    size_chart_id = models.UUIDField()
    old_measurement_types = models.JSONField(null=True, blank=True)
    migration_status = models.TextField(null=True, blank=True)
    migration_notes = models.TextField(null=True, blank=True)
    migrated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'size_chart_migration_log'

class ProductViews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_views'
