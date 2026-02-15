import json
from rest_framework import views, status
from rest_framework.response import Response
from django.db import connection
from drf_spectacular.utils import extend_schema, OpenApiParameter


class SearchAnalyticsView(views.APIView):
    """GET /api/search/analytics/ - Popular/recent searches. POST - Log a search event."""
    permission_classes = []

    @extend_schema(
        request={
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'result_count': {'type': 'integer'},
                'filters': {'type': 'object'},
            },
            'required': ['query', 'result_count'],
        },
        responses={201: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
    )
    def post(self, request):
        query = (request.data.get('query') or '').strip()
        result_count = request.data.get('result_count')
        filters = request.data.get('filters')

        if not query:
            return Response({"detail": "query is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result_count = int(result_count) if result_count is not None else 0
        except (TypeError, ValueError):
            return Response({"detail": "result_count must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = str(request.user.id) if request.user.is_authenticated else None
        filters_json = json.dumps(filters) if filters is not None else None

        try:
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO search_analytics (id, user_id, query, result_count, filters, timestamp)
                    VALUES (uuid_generate_v4(), %s, %s, %s, %s::jsonb, NOW())
                """, [user_id, query, result_count, filters_json])
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"success": True}, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter('start_date', str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter('end_date', str, description='End date (YYYY-MM-DD)'),
            OpenApiParameter('limit', int, description='Limit (default 10)'),
        ],
        responses={200: {
            'type': 'object',
            'properties': {
                'popular_searches': {'type': 'array', 'items': {'type': 'string'}},
                'total_searches': {'type': 'integer'},
                'recent_searches': {'type': 'array'},
            },
        }},
    )
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            limit = int(request.query_params.get('limit', 10))
        except (TypeError, ValueError):
            limit = 10
        limit = min(max(limit, 1), 100)

        where, params = [], []
        if start_date:
            where.append("timestamp >= %s::date")
            params.append(start_date)
        if end_date:
            where.append("timestamp <= %s::date + interval '1 day'")
            params.append(end_date)
        where_sql = " AND ".join(where) if where else "1=1"

        popular, total, recent = [], 0, []

        try:
            with connection.cursor() as c:
                c.execute(f"SELECT COUNT(*) FROM search_analytics WHERE {where_sql}", params)
                total = c.fetchone()[0] or 0

                c.execute(f"""
                    SELECT query, COUNT(*) FROM search_analytics
                    WHERE {where_sql}
                    GROUP BY query ORDER BY COUNT(*) DESC LIMIT %s
                """, params + [limit])
                popular = [row[0] for row in c.fetchall()]

                c.execute(f"""
                    SELECT query, result_count, timestamp
                    FROM search_analytics WHERE {where_sql}
                    ORDER BY timestamp DESC LIMIT %s
                """, params + [limit])
                for row in c.fetchall():
                    ts = row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2])
                    recent.append({"query": row[0], "result_count": row[1], "timestamp": ts})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "popular_searches": popular,
            "total_searches": total,
            "recent_searches": recent,
        })
