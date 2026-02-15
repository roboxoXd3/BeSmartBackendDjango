from django.db import models
import uuid

class Category(models.Model):
    SIZE_CHART_APPLICABILITY_CHOICES = (
        ('always', 'Always'),
        ('conditional', 'Conditional'),
        ('never', 'Never'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Size Chart Logic
    requires_size_chart = models.BooleanField(default=False)
    default_size_chart_template_id = models.UUIDField(null=True, blank=True) # Foreign Key to be linked later
    size_chart_applicability = models.CharField(
        max_length=20, 
        choices=SIZE_CHART_APPLICABILITY_CHOICES, 
        default='never'
    )

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subcategories'
        ordering = ['name']
