from rest_framework.pagination import CursorPagination

class ProductCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-added_date'

    def paginate_queryset(self, queryset, request, view=None):
        # Backward compatibility: if no pagination is explicitly requested via 'cursor'
        # or 'paginate=true', disable pagination and return the full list.
        if 'cursor' not in request.query_params and request.query_params.get('paginate', '').lower() != 'true':
            return None
        return super().paginate_queryset(queryset, request, view)
