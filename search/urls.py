from django.urls import path
from .views import SearchAnalyticsView

urlpatterns = [
    path('', SearchAnalyticsView.as_view(), name='search-analytics'),
]
