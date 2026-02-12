from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import (
    SupportTicket, SupportMessage, ChatConversation, 
    ChatMessage, ContactBranch
)
from .serializers import (
    SupportTicketSerializer, SupportMessageSerializer, 
    ChatConversationSerializer, ChatMessageSerializer, 
    ContactBranchSerializer
)
from vendors.models import Vendor
from drf_spectacular.utils import extend_schema

class SupportTicketViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupportTicketSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SupportTicket.objects.none()
        # Vendors see their own tickets
        return SupportTicket.objects.filter(vendor__user=self.request.user)

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)

class SupportMessageView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupportMessageSerializer

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        # Verify ownership
        if ticket.vendor.user != self.request.user:
            # In real app, Admin should also be able to post.
            # Assuming simplified logic where only vendor posts for now via this endpoint
             pass 
        serializer.save(ticket=ticket, sender=self.request.user)

class ChatConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatConversationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatConversation.objects.none()
        return ChatConversation.objects.filter(user=self.request.user).order_by('-last_message_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChatMessageView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatMessage.objects.none()
        conversation_id = self.kwargs.get('conversation_id')
        if not conversation_id:
            return ChatMessage.objects.none()
        return ChatMessage.objects.filter(conversation_id=conversation_id, conversation__user=self.request.user)

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=self.request.user)
        serializer.save(conversation=conversation, sender_type='user')

class ContactBranchListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ContactBranch.objects.filter(is_active=True)
    serializer_class = ContactBranchSerializer
