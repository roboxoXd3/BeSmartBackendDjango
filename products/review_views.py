from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ProductReview
from drf_spectacular.utils import extend_schema


class ReviewHelpfulView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def post(self, request, id):
        review = get_object_or_404(ProductReview, id=id, status='published')
        review.helpful_count = (review.helpful_count or 0) + 1
        review.save(update_fields=['helpful_count'])
        return Response({"success": True, "helpful_count": review.helpful_count})


class ReviewReportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request={'type': 'object', 'properties': {'reason': {'type': 'string'}}}, responses={200: {'type': 'object'}})
    def post(self, request, id):
        review = get_object_or_404(ProductReview, id=id, status='published')
        review.reported_count = (review.reported_count or 0) + 1
        review.save(update_fields=['reported_count'])
        return Response({"success": True})
