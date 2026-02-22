"""
AI Services API Views
Exposes UJUNWA chatbot and image search to the Flutter app,
keeping the OpenAI API key server-side.
"""
import json
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import intent_service, product_search_service, response_service, image_analysis_service

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    POST /api/ai/chat/
    Body: { "message": str, "conversation_context": list (optional) }
    Returns: { "text": str, "products": list, "suggestions": list, "intent": dict }
    """
    user_message = request.data.get('message', '').strip()
    if not user_message:
        return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

    conversation_context = request.data.get('conversation_context', [])

    try:
        # Step 1: Classify intent
        intent = intent_service.recognize_intent(user_message)
        logger.info('Chat intent: %s for user %s', intent.get('intent'), request.user)

        # Step 2: Search products if needed
        products = []
        if intent.get('intent') in ('product_search', 'product_info', 'recommendation', 'comparison'):
            entities = intent.get('entities', [])
            query = ' '.join(entities) if entities else user_message
            raw_products = product_search_service.hybrid_search(query, limit=20)
            products = product_search_service.enrich_products(raw_products)

        # Step 3: Fetch relevant FAQs
        faqs = product_search_service.get_relevant_faqs(user_message, limit=3)

        # Step 4: Generate response
        result = response_service.generate_response(
            user_message=user_message,
            intent=intent,
            products=products,
            conversation_context=conversation_context,
            faqs=faqs,
        )

        # Serialize products to JSON-safe dicts
        serialized_products = [_serialize_product(p) for p in products[:8]]

        return Response({
            'text': result['text'],
            'products': serialized_products,
            'suggestions': result.get('suggestions', []),
            'intent': intent,
        })

    except Exception as e:
        logger.error('Chat endpoint error: %s', e, exc_info=True)
        return Response(
            {'error': 'Failed to process message. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_image(request):
    """
    POST /api/ai/image-search/
    Body: multipart/form-data with 'image' file field
    Returns: { "description": str, "products": list }
    """
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'image file is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        image_bytes = image_file.read()
        content_type = image_file.content_type or 'image/jpeg'

        # Step 1: Analyze image with OpenAI Vision
        description = image_analysis_service.analyze_image(image_bytes, content_type)
        logger.info('Image analysis result: %s', description)

        # Step 2: Search products based on description
        raw_products = product_search_service.search_by_image_description(description, limit=20)
        products = product_search_service.enrich_products(raw_products)
        serialized_products = [_serialize_product(p) for p in products[:8]]

        return Response({
            'description': description,
            'products': serialized_products,
        })

    except Exception as e:
        logger.error('Image analysis endpoint error: %s', e, exc_info=True)
        return Response(
            {'error': 'Failed to analyze image. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _serialize_product(p: dict) -> dict:
    """Convert a raw DB product dict to a JSON-safe response dict."""
    import uuid
    result = {}
    for k, v in p.items():
        if isinstance(v, uuid.UUID):
            result[k] = str(v)
        elif hasattr(v, 'isoformat'):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result
