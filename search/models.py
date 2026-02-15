from django.db import models
import uuid


class SearchAnalytics(models.Model):
    """Unmanaged model for search_analytics table."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(blank=True, null=True)
    query = models.TextField()
    result_count = models.IntegerField()
    filters = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'search_analytics'
