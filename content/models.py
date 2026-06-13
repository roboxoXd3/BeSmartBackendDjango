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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    subtitle = models.TextField(null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_type = models.TextField(null=True, blank=True)
    coupon_code = models.TextField(null=True, blank=True)
    background_image_url = models.TextField(null=True, blank=True)
    show_title = models.BooleanField(null=True, blank=True)
    show_description = models.BooleanField(null=True, blank=True)
    show_subtitle = models.BooleanField(null=True, blank=True)
    show_discount = models.BooleanField(null=True, blank=True)
    show_coupon_code = models.BooleanField(null=True, blank=True)
    show_background_image = models.BooleanField(null=True, blank=True)
    title_color = models.TextField(null=True, blank=True)
    description_color = models.TextField(null=True, blank=True)
    subtitle_color = models.TextField(null=True, blank=True)
    discount_color = models.TextField(null=True, blank=True)
    coupon_code_color = models.TextField(null=True, blank=True)
    background_color = models.TextField(null=True, blank=True)
    overlay_color = models.TextField(null=True, blank=True)
    text_alignment = models.TextField(null=True, blank=True)
    banner_height = models.TextField(null=True, blank=True)
    padding = models.TextField(null=True, blank=True)
    border_radius = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(null=True, blank=True)
    is_template = models.BooleanField(null=True, blank=True)
    template_name = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    custom_styles = models.JSONField(null=True, blank=True)
    button_text = models.TextField(null=True, blank=True)
    button_url = models.TextField(null=True, blank=True)
    button_color = models.TextField(null=True, blank=True)
    button_text_color = models.TextField(null=True, blank=True)
    show_button = models.BooleanField(null=True, blank=True)
    banner_size = models.TextField(null=True, blank=True)

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

class PlatformSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.TextField()
    key = models.TextField()
    value = models.JSONField()
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'platform_settings'

