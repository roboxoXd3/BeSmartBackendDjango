from django.db import models
from django.contrib.auth import get_user_model
import uuid
from admin_api.models import AdminUser

User = get_user_model()


class HeroSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trusted_by_text = models.TextField(null=True, blank=True)
    headline = models.TextField()
    headline_highlight = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    media_type = models.CharField(max_length=50, null=True, blank=True)
    media_url = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    video_url = models.TextField(null=True, blank=True)
    primary_button = models.JSONField(default=dict)
    secondary_button = models.JSONField(default=dict)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hero_section'


class ContactInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.JSONField(default=dict)
    office = models.JSONField(default=dict)
    customer_service_promise = models.JSONField(default=dict)
    social_media = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_info'


class PromotionalBanner(models.Model):
    BANNER_SIZE_CHOICES = (
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image_url = models.TextField()
    link_url = models.TextField(null=True, blank=True)
    background_color = models.CharField(max_length=50, default='#FFFFFF')
    text_color = models.CharField(max_length=50, default='#000000')
    position = models.CharField(max_length=50, default='top')
    page_location = models.CharField(max_length=50, default='home')
    padding = models.CharField(max_length=50, default='20px')
    border_radius = models.CharField(max_length=50, default='8px')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_template = models.BooleanField(default=False)
    template_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    custom_styles = models.JSONField(default=dict)
    button_text = models.CharField(max_length=255, null=True, blank=True)
    button_url = models.TextField(null=True, blank=True)
    button_color = models.CharField(max_length=50, default='#007BFF')
    button_text_color = models.CharField(max_length=50, default='#FFFFFF')
    show_button = models.BooleanField(default=False)
    banner_size = models.CharField(max_length=20, choices=BANNER_SIZE_CHOICES, default='medium')

    class Meta:
        db_table = 'promotional_banners'

class SupportInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    subtitle = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=50) # faq, contact, policy
    icon = models.CharField(max_length=255)
    action_type = models.CharField(max_length=50, null=True, blank=True)
    action_value = models.TextField(null=True, blank=True)
    availability = models.CharField(max_length=100, null=True, blank=True)
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'support_info'
