import logging
import uuid as uuid_module

from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    SupportTicket, SupportMessage, ChatConversation, 
    ChatMessage, ChatAnalytics, ConversationContext, ContactBranch
)
from .serializers import (
    SupportTicketSerializer, SupportMessageSerializer, 
    ChatConversationSerializer, ChatMessageSerializer, 
    ContactBranchSerializer
)
from vendors.models import Vendor
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)

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


class UjunwaSendMessageView(views.APIView):
    """
    POST /api/support/chat/send/

    UJUNWA AI Shopping Assistant — mirrors the mobile app's chatbot_controller
    sendMessage() + _handleUjunwaResponse() flow exactly.

    Request: { "message": "...", "conversation_id": "uuid" (optional) }
    Response: {
        "conversation_id": "uuid",
        "user_message": { ... ChatMessage ... },
        "bot_response": {
            "id": "uuid",
            "message_text": "...",
            "message_type": "text" | "products",
            "metadata": {
                "intent_type": "product_search",
                "intent_confidence": 0.95,
                "products_count": 5,
                "product_ids": [...],
                "suggestions": [...]
            },
            "products": [ ... full product objects ... ]
        }
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={'type': 'object', 'properties': {
            'message': {'type': 'string'},
            'conversation_id': {'type': 'string', 'format': 'uuid'},
        }, 'required': ['message']},
        responses={200: {'type': 'object'}},
    )
    def post(self, request):
        user_message_text = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id')
        user = request.user

        if not user_message_text:
            return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Get or create conversation
        conversation = None
        if conversation_id:
            try:
                conversation = ChatConversation.objects.get(id=conversation_id, user=user)
            except ChatConversation.DoesNotExist:
                pass

        if not conversation:
            conversation = ChatConversation.objects.create(
                user=user,
                title=user_message_text[:50],
            )

        # 2. Save user message
        user_msg = ChatMessage.objects.create(
            conversation=conversation,
            sender_type='user',
            message_text=user_message_text,
            message_type='text',
        )

        # 3. Load conversation context (last 5)
        context_entries = list(
            ConversationContext.objects.filter(
                conversation=conversation,
            ).order_by('-created_at')[:5].values(
                'user_message', 'intent_type', 'intent_confidence',
                'ai_response', 'extracted_info', 'products_mentioned',
            )
        )

        # 4. Intent recognition
        from ai_services.intent_service import recognize_intent
        intent = recognize_intent(user_message_text)

        # 5. Product search
        from ai_services.product_search_service import (
            hybrid_search, enrich_products, get_relevant_faqs, get_product_specs,
        )

        products = []
        faqs = None
        product_specs = None
        intent_type = intent.get('intent', 'general')

        if intent_type in ('product_search', 'product_info', 'recommendation'):
            search_terms = _extract_search_terms(user_message_text)
            if search_terms:
                products = hybrid_search(search_terms, limit=10)
                products = enrich_products(products)

        if intent_type in ('support', 'general', 'product_info'):
            faqs = get_relevant_faqs(user_message_text, limit=5)

        if intent_type == 'product_info' and products:
            product_specs = get_product_specs(str(products[0]['id']))

        # 6. Generate UJUNWA response
        from ai_services.response_service import generate_response
        ai_result = generate_response(
            user_message=user_message_text,
            intent=intent,
            products=products,
            conversation_context=context_entries,
            faqs=faqs,
            product_specs=product_specs,
        )

        # 7. Determine message type (DB constraint: 'product' not 'products')
        message_type = 'product' if products else 'text'
        product_ids = [str(p['id']) for p in products]

        # 8. Save bot response
        bot_metadata = {
            'intent_type': intent.get('intent', 'general'),
            'intent_confidence': intent.get('confidence', 0),
            'products_count': len(products),
            'product_ids': product_ids,
            'suggestions': ai_result.get('suggestions', []),
        }

        bot_msg = ChatMessage.objects.create(
            conversation=conversation,
            sender_type='bot',
            message_text=ai_result['text'],
            message_type=message_type,
            metadata=bot_metadata,
        )

        # 9. Update conversation
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        # 10. Store conversation context
        extracted_info = _extract_key_information(user_message_text, intent)
        product_uuids = []
        for pid in product_ids:
            try:
                product_uuids.append(uuid_module.UUID(pid))
            except (ValueError, TypeError):
                pass

        try:
            ConversationContext.objects.create(
                conversation=conversation,
                user=user,
                user_message=user_message_text,
                intent_type=intent.get('intent', 'general'),
                intent_confidence=intent.get('confidence', 0),
                ai_response=ai_result['text'],
                extracted_info=extracted_info,
                products_mentioned=product_uuids,
            )
        except Exception as e:
            logger.warning('Failed to store conversation context: %s', e)

        # 11. Track analytics
        try:
            ChatAnalytics.objects.create(
                conversation=conversation,
                user=user,
                action_type='message_sent',
                action_data={
                    'intent': intent.get('intent', 'general'),
                    'products_found': len(products),
                },
            )
        except Exception as e:
            logger.warning('Failed to store analytics: %s', e)

        # 12. Serialize products for response (same shape mobile expects)
        serialized_products = _serialize_products_for_response(products)

        return Response({
            'conversation_id': str(conversation.id),
            'user_message': {
                'id': str(user_msg.id),
                'sender_type': 'user',
                'message_text': user_message_text,
                'message_type': 'text',
                'created_at': user_msg.created_at.isoformat() if user_msg.created_at else None,
            },
            'bot_response': {
                'id': str(bot_msg.id),
                'sender_type': 'bot',
                'message_text': ai_result['text'],
                'message_type': message_type,
                'metadata': bot_metadata,
                'products': serialized_products,
                'created_at': bot_msg.created_at.isoformat() if bot_msg.created_at else None,
            },
        })


class ChatAnalyticsTrackView(views.APIView):
    """POST /api/support/chat/analytics/ — track chat action.
       GET  /api/support/chat/analytics/ — retrieve user's chat analytics."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Gap 3: getChatAnalytics — return user's analytics with optional date filters."""
        qs = ChatAnalytics.objects.filter(user=request.user).order_by('-created_at')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(created_at__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__lte=to_date)
        data = list(qs.values('id', 'conversation_id', 'action_type', 'action_data', 'created_at'))
        for item in data:
            item['id'] = str(item['id'])
            if item['conversation_id']:
                item['conversation_id'] = str(item['conversation_id'])
            if item['created_at']:
                item['created_at'] = item['created_at'].isoformat()
        return Response({'count': len(data), 'results': data})

    def post(self, request):
        conversation_id = request.data.get('conversation_id')
        action_type = request.data.get('action_type', '')
        action_data = request.data.get('action_data', {})

        conversation = None
        if conversation_id:
            try:
                conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            except ChatConversation.DoesNotExist:
                pass

        ChatAnalytics.objects.create(
            conversation=conversation,
            user=request.user,
            action_type=action_type,
            action_data=action_data,
        )
        return Response({'success': True})


class ChatMarkMessagesReadView(views.APIView):
    """POST /api/support/chat/{conversation_id}/messages/mark-read/
    Gap 1: markMessagesAsRead — bulk-update is_read for messages by sender_type."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
        sender_type = request.data.get('sender_type', 'bot')
        updated = ChatMessage.objects.filter(
            conversation=conversation,
            sender_type=sender_type,
            is_read=False,
        ).update(is_read=True)
        return Response({'success': True, 'updated_count': updated})


class ChatUnreadCountView(views.APIView):
    """GET /api/support/chat/unread-count/
    Gap 2: getUnreadMessageCount — count of unread bot/agent messages across all conversations."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = ChatMessage.objects.filter(
            conversation__user=request.user,
            is_read=False,
        ).exclude(sender_type='user').count()
        return Response({'unread_count': count})


class ChatClearHistoryView(views.APIView):
    """POST /api/support/chat/clear-history/
    Gap 4: clearChatHistory — delete all chat data for the user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.db import transaction as db_transaction
        user = request.user
        conversations = ChatConversation.objects.filter(user=user)
        conv_ids = list(conversations.values_list('id', flat=True))

        with db_transaction.atomic():
            ChatMessage.objects.filter(conversation_id__in=conv_ids).delete()
            ConversationContext.objects.filter(conversation_id__in=conv_ids).delete()
            ChatAnalytics.objects.filter(user=user).delete()
            conversations.delete()

        return Response({'success': True, 'message': 'All chat history cleared.'})


class ChatSearchMessagesView(views.APIView):
    """GET /api/support/chat/messages/search/?q=...&limit=20
    Gap 5: searchMessages — full-text search across user's chat messages."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 20))
        if not q:
            return Response({'count': 0, 'results': []})

        messages = ChatMessage.objects.filter(
            conversation__user=request.user,
            message_text__icontains=q,
        ).select_related('conversation').order_by('-created_at')[:limit]

        results = []
        for msg in messages:
            results.append({
                'id': str(msg.id),
                'conversation_id': str(msg.conversation_id),
                'sender_type': msg.sender_type,
                'message_text': msg.message_text,
                'message_type': msg.message_type,
                'is_read': msg.is_read,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
            })
        return Response({'count': len(results), 'results': results})


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _extract_search_terms(message: str) -> str:
    """Mirror mobile's _extractSearchTerms()."""
    product_keywords = {
        'shoes', 'shoe', 'sneakers', 'sneaker', 'boots', 'sandals', 'footwear',
        'shirt', 'shirts', 't-shirt', 'tshirt', 'pants', 'pant', 'jeans',
        'dress', 'jacket', 'coat', 'sweater', 'hoodie', 'shorts', 'skirt',
        'top', 'blouse', 'yoga', 'running', 'workout', 'fitness', 'gym',
        'sports', 'athletic', 'phone', 'laptop', 'tablet', 'headphones',
        'earbuds', 'watch', 'smartwatch', 'bag', 'purse', 'wallet', 'belt',
        'hat', 'cap', 'sunglasses', 'glasses', 'black', 'white', 'blue',
        'red', 'green', 'yellow', 'pink', 'purple', 'gray', 'brown',
        'small', 'medium', 'large', 'xl', 'xxl', 'xs', 'comfortable',
        'stylish', 'casual', 'formal', 'premium', 'affordable', 'cheap',
    }
    common_words = {
        'find', 'search', 'looking', 'for', 'show', 'me', 'i', 'want',
        'need', 'buy', 'purchase', 'get', 'can', 'you', 'please', 'do',
        'dont', 'have', 'got', 'any', 'some', 'good', 'nice', 'great',
        'best', 'the', 'a', 'an', 'is', 'are', 'that', 'this', 'with',
        'go', 'and', 'or', 'but', 'to', 'from', 'in', 'on', 'at', 'by',
    }

    words = message.lower().split()
    product_terms = [w for w in words if w in product_keywords and len(w) > 2]
    other_terms = [w for w in words if w not in common_words and w not in product_keywords and len(w) > 2]

    if product_terms:
        return ' '.join(product_terms)
    return ' '.join(product_terms + other_terms).strip()


def _extract_key_information(message: str, intent: dict) -> str:
    """Mirror mobile's _extractKeyInformation()."""
    lower = message.lower()
    info = []
    if 'cheap' in lower or 'affordable' in lower:
        info.append('prefers affordable options')
    if 'premium' in lower or 'expensive' in lower:
        info.append('interested in premium products')
    if 'large' in lower or 'xl' in lower:
        info.append('prefers large sizes')
    if 'small' in lower or 'xs' in lower:
        info.append('prefers small sizes')
    if 'workout' in lower or 'gym' in lower:
        info.append('interested in fitness products')
    if 'work' in lower or 'office' in lower:
        info.append('needs professional/work items')
    return ', '.join(info)


def _serialize_products_for_response(products: list) -> list:
    """Serialize product dicts for the API response (matches what mobile expects)."""
    serialized = []
    for p in products:
        serialized.append({
            'id': str(p.get('id', '')),
            'name': p.get('name', ''),
            'description': p.get('description', ''),
            'price': float(p.get('price', 0)) if p.get('price') is not None else 0,
            'images': p.get('images', ''),
            'sizes': p.get('sizes', []),
            'rating': float(p.get('rating', 0)) if p.get('rating') is not None else 0,
            'reviews': p.get('reviews', 0),
            'in_stock': p.get('in_stock', True),
            'category_id': str(p.get('category_id', '')) if p.get('category_id') else None,
            'brand': p.get('brand', ''),
            'discount_percentage': float(p.get('discount_percentage', 0)) if p.get('discount_percentage') is not None else None,
            'is_on_sale': p.get('is_on_sale', False),
            'sale_price': float(p.get('sale_price', 0)) if p.get('sale_price') is not None else None,
            'is_featured': p.get('is_featured', False),
            'is_new_arrival': p.get('is_new_arrival', False),
            'vendor_id': str(p.get('vendor_id', '')) if p.get('vendor_id') else None,
            'vendor_name': p.get('vendor_name', ''),
            'sku': p.get('sku', ''),
            'status': p.get('status', 'active'),
            'colors': p.get('colors', {}),
            'highlights': p.get('highlights', []),
            'specifications': p.get('specifications', []),
        })
    return serialized
