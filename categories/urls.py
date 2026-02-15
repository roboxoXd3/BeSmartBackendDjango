from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView,
    CategorySubcategoriesView, CategoryProductsView,
    CategorySizeChartView, CategoryHasSizeChartView,
)

urlpatterns = [
    path('', CategoryListView.as_view(), name='category-list'),
    path('<uuid:id>/subcategories/', CategorySubcategoriesView.as_view(), name='category-subcategories'),
    path('<uuid:id>/products/', CategoryProductsView.as_view(), name='category-products'),
    path('<uuid:id>/size-chart/', CategorySizeChartView.as_view(), name='category-size-chart'),
    path('<uuid:id>/has-size-chart/', CategoryHasSizeChartView.as_view(), name='category-has-size-chart'),
    path('<uuid:id>/', CategoryDetailView.as_view(), name='category-detail'),
]
