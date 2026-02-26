from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ProductReview
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers


class ReviewHelpfulView(views.APIView):
    """POST /api/reviews/{id}/helpful/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(
        summary="Mark a review as helpful",
        responses={200: inline_serializer(name="ReviewHelpfulRes", fields={"success": serializers.BooleanField(), "helpful_count": serializers.IntegerField()})}
    )
    def post(self, request, id):
        review = get_object_or_404(ProductReview, id=id, status='published')
        review.helpful_count = (review.helpful_count or 0) + 1
        review.save(update_fields=['helpful_count'])
        return Response({"success": True, "helpful_count": review.helpful_count})


class ReviewReportView(views.APIView):
    """POST /api/reviews/{id}/report/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(
        summary="Report a review",
        request=inline_serializer(name="ReviewReportReq", fields={"reason": serializers.CharField()}),
        responses={200: inline_serializer(name="ReviewReportRes", fields={"success": serializers.BooleanField()})}
    )
    def post(self, request, id):
        review = get_object_or_404(ProductReview, id=id, status='published')
        review.reported_count = (review.reported_count or 0) + 1
        review.save(update_fields=['reported_count'])
        return Response({"success": True})
