from rest_framework import serializers
from .models import (
    SupportTicket, SupportMessage, ChatConversation, 
    ChatMessage, ChatAnalytics, ContactBranch
)
from users.serializers import UserSerializer
from admin_api.serializers import AdminUserSerializer

class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True) # Hypothetical field

    class Meta:
        model = SupportMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'ticket', 'sender']

class SupportTicketSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)
    assigned_to_details = AdminUserSerializer(source='assigned_to', read_only=True)
    resolved_by_details = AdminUserSerializer(source='resolved_by', read_only=True)

    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = [
            'vendor', 'status', 'assigned_to', 'resolved_by', 
            'resolved_at', 'created_at', 'updated_at', 'last_updated'
        ]

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'conversation']

class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = ChatConversation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user', 'last_message_at']

class ContactBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactBranch
        fields = '__all__'
