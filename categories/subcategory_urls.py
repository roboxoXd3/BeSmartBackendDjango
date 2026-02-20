from django.urls import path
from .views import SubcategoryListView

urlpatterns = [
    path('', SubcategoryListView.as_view(), name='subcategory-list'),
]
