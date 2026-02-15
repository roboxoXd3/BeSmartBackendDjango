"""
Intent Recognition Service — mirrors mobile UjunwaAIService._recognizeIntent()
Uses OpenAI GPT-4o-mini for intent classification with keyword fallback.
"""
import json
import logging

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

INTENT_TYPES = [
    'product_search',
    'product_info',
    'order_inquiry',
    'comparison',
    'recommendation',
    'support',
    'greeting',
    'general',
]

SYSTEM_PROMPT = """You are an expert e-commerce intent classifier. Analyze user messages and classify their intent.

Return ONLY a JSON object with this exact format:
{
  "intent": "intent_type",
  "confidence": 0.95,
  "entities": ["extracted", "entities"]
}

Intent types (use exactly these values):
- "product_search": Looking for products, asking about availability, wanting to buy something
- "order_inquiry": Asking about orders, delivery, tracking, shipping status
- "product_info": Asking for product details, specifications, features, prices
- "comparison": Comparing products, asking which is better
- "recommendation": Asking for suggestions, recommendations, what to buy
- "support": Need help, returns, refunds, issues, problems
- "greeting": Hello, hi, general greetings
- "general": Everything else

Examples:
"dont you have any yoga pant" → {"intent": "product_search", "confidence": 0.95, "entities": ["yoga", "pant"]}
"show me running shoes" → {"intent": "product_search", "confidence": 0.98, "entities": ["running", "shoes"]}
"track my order" → {"intent": "order_inquiry", "confidence": 0.97, "entities": ["order", "track"]}"""


def recognize_intent(message: str) -> dict:
    """
    Recognize intent using OpenAI, with keyword fallback.
    Returns: {'intent': str, 'confidence': float, 'entities': list}
    """
    try:
        return _recognize_with_ai(message)
    except Exception as e:
        logger.warning('AI intent recognition failed, using keyword fallback: %s', e)
        return _recognize_with_keywords(message)


def _recognize_with_ai(message: str) -> dict:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError('OPENAI_API_KEY not configured')

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Classify this message: {message}'},
        ],
        temperature=0.1,
        max_tokens=100,
    )

    content = response.choices[0].message.content.strip()
    result = json.loads(content)

    intent_type = result.get('intent', 'general')
    if intent_type not in INTENT_TYPES:
        intent_type = 'general'

    return {
        'intent': intent_type,
        'confidence': float(result.get('confidence', 0.5)),
        'entities': result.get('entities', []),
    }


def _recognize_with_keywords(message: str) -> dict:
    lower = message.lower()

    search_kw = ['find', 'search', 'show', 'need', 'want', 'buy', 'have', 'got', 'any',
                 'yoga', 'pant', 'shoes', 'clothes']
    order_kw = ['order', 'track', 'delivery', 'shipping']
    greeting_kw = ['hello', 'hi', 'hey']
    support_kw = ['help', 'support', 'problem', 'return', 'refund']

    if any(kw in lower for kw in search_kw):
        return {'intent': 'product_search', 'confidence': 0.7, 'entities': []}
    if any(kw in lower for kw in order_kw):
        return {'intent': 'order_inquiry', 'confidence': 0.7, 'entities': []}
    if any(kw in lower for kw in greeting_kw):
        return {'intent': 'greeting', 'confidence': 0.8, 'entities': []}
    if any(kw in lower for kw in support_kw):
        return {'intent': 'support', 'confidence': 0.7, 'entities': []}

    return {'intent': 'general', 'confidence': 0.5, 'entities': []}
