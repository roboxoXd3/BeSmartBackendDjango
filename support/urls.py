from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupportTicketViewSet, SupportMessageView,
    ChatConversationViewSet, ChatMessageView,
    ContactBranchListView, UjunwaSendMessageView,
    ChatAnalyticsTrackView,
    ChatMarkMessagesReadView, ChatUnreadCountView,
    ChatClearHistoryView, ChatSearchMessagesView,
)

router = DefaultRouter()
router.register(r'tickets', SupportTicketViewSet, basename='support-tickets')
router.register(r'chat', ChatConversationViewSet, basename='support-chat')

urlpatterns = [
    # Support tickets
    path('tickets/<uuid:ticket_id>/messages/', SupportMessageView.as_view(), name='support-ticket-messages'),

    # Chat — static paths first
    path('chat/send/', UjunwaSendMessageView.as_view(), name='support-chat-send'),
    path('chat/analytics/', ChatAnalyticsTrackView.as_view(), name='support-chat-analytics'),
    path('chat/unread-count/', ChatUnreadCountView.as_view(), name='support-chat-unread-count'),
    path('chat/clear-history/', ChatClearHistoryView.as_view(), name='support-chat-clear-history'),
    path('chat/messages/search/', ChatSearchMessagesView.as_view(), name='support-chat-search-messages'),

    # Chat — parameterized paths
    path('chat/<uuid:conversation_id>/messages/mark-read/', ChatMarkMessagesReadView.as_view(), name='support-chat-mark-read'),
    path('chat/<uuid:conversation_id>/messages/', ChatMessageView.as_view(), name='support-chat-messages'),

    # Other
    path('branches/', ContactBranchListView.as_view(), name='support-branches'),
    path('', include(router.urls)),
]
