from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupportTicketViewSet, SupportMessageView, 
    ChatConversationViewSet, ChatMessageView, 
    ContactBranchListView
)

router = DefaultRouter()
router.register(r'tickets', SupportTicketViewSet, basename='support-tickets')
router.register(r'chat', ChatConversationViewSet, basename='support-chat')

urlpatterns = [
    path('tickets/<uuid:ticket_id>/messages/', SupportMessageView.as_view(), name='support-ticket-messages'),
    path('chat/<uuid:conversation_id>/messages/', ChatMessageView.as_view(), name='support-chat-messages'),
    path('branches/', ContactBranchListView.as_view(), name='support-branches'),
    path('', include(router.urls)),
]
