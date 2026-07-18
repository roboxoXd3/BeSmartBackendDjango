"""
AI Services API Views
Exposes UJUNWA chatbot and image search to the Flutter app,
keeping the OpenAI API key server-side.
"""
import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from . import intent_service, product_search_service, response_service, image_analysis_service

from besmart_backend.utils.logger import get_logger
logger = get_logger(__name__)

@extend_schema(
    summary="AI Chat endpoint",
    request=inline_serializer("AIChatReq", {"message": serializers.CharField(), "conversation_context": serializers.ListField(child=serializers.DictField(), required=False)}),
    responses={200: inline_serializer("AIChatRes", {"text": serializers.CharField(), "products": serializers.ListField(child=serializers.DictField()), "suggestions": serializers.ListField(child=serializers.CharField()), "intent": serializers.DictField()})}
)
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
    
    logger.info("ai_chat_started")

    try:
        # Step 1: Classify intent
        intent = intent_service.recognize_intent(user_message)
        logger.info('ai_chat_intent_recognized', intent=intent.get('intent'))

        # Step 2: Search products if needed
        products = []
        if intent.get('intent') in ('product_search', 'product_info', 'recommendation', 'comparison'):
            entities = intent.get('entities', [])
            query = ' '.join(entities) if entities else user_message
            logger.info('ai_search_query_parsed', query=query)
            raw_products = product_search_service.hybrid_search(query, limit=20)
            products = product_search_service.enrich_products(raw_products)
            logger.info('ai_search_completed', results_count=len(products))

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

        logger.info('ai_chat_response_generated', intent=intent.get('intent'), product_count=len(serialized_products))
        return Response({
            'text': result['text'],
            'products': serialized_products,
            'suggestions': result.get('suggestions', []),
            'intent': intent,
        })

    except Exception as e:
        logger.error('ai_chat_error', error=str(e), exc_info=True)
        return Response(
            {'error': 'Failed to process message. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary="AI Image Analysis",
    request=inline_serializer("AIImageReq", {"image": serializers.FileField()}),
    responses={200: inline_serializer("AIImageRes", {"description": serializers.CharField(), "products": serializers.ListField(child=serializers.DictField())})}
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
        
    logger.info("ai_image_analysis_started")

    try:
        image_bytes = image_file.read()
        content_type = image_file.content_type or 'image/jpeg'

        # Step 1: Analyze image with OpenAI Vision
        description = image_analysis_service.analyze_image(image_bytes, content_type)
        logger.info('ai_image_analyzed', description=description)

        # Step 2: Search products based on description
        logger.info('ai_image_search_started')
        raw_products = product_search_service.search_by_image_description(description, limit=20)
        products = product_search_service.enrich_products(raw_products)
        serialized_products = [_serialize_product(p) for p in products[:8]]
        logger.info('ai_image_search_completed', results_count=len(products))

        return Response({
            'description': description,
            'products': serialized_products,
        })

    except Exception as e:
        logger.error('ai_image_analysis_error', error=str(e), exc_info=True)
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
