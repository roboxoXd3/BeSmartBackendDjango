from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from vendors.models import Vendor
from admin_api.models import AdminUser
import uuid

User = get_user_model()

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='tickets')
    subject = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    category = models.CharField(max_length=50, default='general')
    assigned_to = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    resolved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets')
    resolved_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'support_tickets'

class SupportMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE) # Vendor user or Admin user
    message = models.TextField()
    is_internal = models.BooleanField(default=False)
    attachments = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'support_messages'

class ChatConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    title = models.CharField(max_length=255, default='New Conversation')
    last_message_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_conversations'

class ChatMessage(models.Model):
    SENDER_TYPE_CHOICES = (
        ('user', 'User'),
        ('bot', 'Bot'),
        ('agent', 'Agent'),
    )
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('product', 'Product'),       # singular — matches DB check constraint
        ('image', 'Image'),
        ('file', 'File'),
        ('quick_reply', 'Quick Reply'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    message_text = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    metadata = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'

class ChatAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(ChatConversation, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=100)
    action_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_analytics'

class ConversationContext(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, null=True, blank=True, related_name='context_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_message = models.TextField()
    intent_type = models.TextField()
    intent_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_response = models.TextField()
    extracted_info = models.TextField(null=True, blank=True)
    products_mentioned = ArrayField(models.UUIDField(), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'conversation_context'


class ContactBranch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch_name = models.CharField(max_length=255)
    mall_name = models.CharField(max_length=255, null=True, blank=True)
    address_line_1 = models.TextField()
    address_line_2 = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Nigeria')
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    opening_hours = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_branches'
