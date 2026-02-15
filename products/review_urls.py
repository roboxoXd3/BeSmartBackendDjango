from django.urls import path
from . import review_views

urlpatterns = [
    path('<uuid:id>/helpful/', review_views.ReviewHelpfulView.as_view(), name='review-helpful'),
    path('<uuid:id>/report/', review_views.ReviewReportView.as_view(), name='review-report'),
]
