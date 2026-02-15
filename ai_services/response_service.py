"""
Response Generation Service — mirrors mobile UjunwaAIService._generateStructuredResponse()
and _generateAIResponse().

Builds prompts with product context, FAQs, specs, and conversation history,
then calls OpenAI GPT-4o-mini. Static responses for greeting / order / support intents.
"""
import logging

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Static responses (same as mobile)
# ---------------------------------------------------------------------------
GREETING_TEXT = (
    "Hello there! 👋 Welcome to **Be Smart**!\n\n"
    "I'm **UJUNWA**, your personal shopping assistant. I'm here to help you:\n\n"
    "🔍 **Find products** you're looking for\n"
    "📦 **Track your orders** and deliveries\n"
    "💡 **Get recommendations** based on your preferences\n"
    "🛠️ **Answer questions** about products and services\n\n"
    "What can I help you with today? 😊"
)
GREETING_SUGGESTIONS = [
    'Show me trending products',
    'Find products on sale',
    'Browse categories',
    'Track my order',
]

ORDER_INQUIRY_TEXT = (
    "I'd be happy to help you with your order! Could you please provide your "
    "order number or email address so I can look up your order details?"
)
ORDER_INQUIRY_SUGGESTIONS = [
    'Track another order',
    'Contact support',
    'View order history',
    'Return an item',
]

SUPPORT_TEXT = (
    "I'm here to help! What specific issue are you experiencing? I can assist with:\n\n"
    "• Product questions\n• Order issues\n• Returns and refunds\n"
    "• Account problems\n• Technical support"
)
SUPPORT_SUGGESTIONS = [
    'Contact live support',
    'View FAQ',
    'Return policy',
    'Shipping information',
]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_response(
    user_message: str,
    intent: dict,
    products: list,
    conversation_context: list | None = None,
    faqs: list | None = None,
    product_specs: list | None = None,
) -> dict:
    """
    Generate the UJUNWA response.
    Returns {'text': str, 'suggestions': list[str]}
    """
    intent_type = intent.get('intent', 'general')

    # Static responses for certain intents
    if intent_type == 'greeting':
        return {'text': GREETING_TEXT, 'suggestions': GREETING_SUGGESTIONS}
    if intent_type == 'order_inquiry':
        return {'text': ORDER_INQUIRY_TEXT, 'suggestions': ORDER_INQUIRY_SUGGESTIONS}
    if intent_type == 'support' and not products:
        return {'text': SUPPORT_TEXT, 'suggestions': SUPPORT_SUGGESTIONS}

    # AI-powered response for everything else
    return _generate_ai_response(
        user_message=user_message,
        intent=intent,
        products=products,
        conversation_context=conversation_context,
        faqs=faqs,
        product_specs=product_specs,
    )


# ---------------------------------------------------------------------------
# AI response generation
# ---------------------------------------------------------------------------
def _generate_ai_response(
    user_message: str,
    intent: dict,
    products: list,
    conversation_context: list | None = None,
    faqs: list | None = None,
    product_specs: list | None = None,
) -> dict:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError('OPENAI_API_KEY not configured')

    system_prompt = _build_system_prompt(intent, products)
    user_prompt = _build_user_prompt(
        user_message, intent, products, conversation_context, faqs, product_specs,
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        max_tokens=300,
        temperature=0.7,
    )

    ai_text = response.choices[0].message.content.strip()
    suggestions = _generate_suggestions(intent, products)

    return {'text': ai_text, 'suggestions': suggestions}


# ---------------------------------------------------------------------------
# Prompt builders (match mobile exactly)
# ---------------------------------------------------------------------------
def _build_system_prompt(intent: dict, products: list) -> str:
    intent_type = intent.get('intent', 'general')
    return f"""You are UJUNWA, an intelligent AI shopping assistant for Be Smart e-commerce platform. You are helpful, friendly, knowledgeable, and professional.

Your capabilities include:
- Helping customers find products using semantic understanding
- Providing detailed product information including specifications, highlights, and reviews
- Making personalized recommendations based on user preferences
- Assisting with orders and support
- Comparing products with detailed analysis
- Answering questions about policies, returns, shipping, and FAQs

Your personality:
- Warm and approachable
- Expert knowledge about products and e-commerce
- Patient and understanding
- Proactive in offering help and suggestions
- Always honest about limitations
- Enthusiastic but not pushy

Current context:
- User intent: {intent_type}
- Available products: {len(products)}

Guidelines:
- Keep responses conversational and natural (2-4 sentences typically)
- When showing products, highlight key features, benefits, and why they match the user's needs
- Compare products when multiple options are available, highlighting differences
- Include pricing, ratings, availability, and key specifications when relevant
- Reference product highlights and unique selling points
- If FAQs or policies are relevant, incorporate that information naturally
- Always offer to help further with specific actions
- If you don't know something, be honest and offer alternatives
- Use emojis sparingly (1-2 per response max) and appropriately
- For product searches with no results, suggest alternatives and help refine the search
- For product info queries, provide comprehensive details including specs, highlights, and reviews summary
- For recommendations, explain why products match the user's needs
"""


def _build_user_prompt(
    user_message: str,
    intent: dict,
    products: list,
    conversation_context: list | None = None,
    faqs: list | None = None,
    product_specs: list | None = None,
) -> str:
    parts = [f'User message: "{user_message}"']

    # Product context
    if products:
        parts.append(f'\nRelevant products found ({len(products)} total):')
        for i, p in enumerate(products[:8]):
            parts.append(f'\n{i+1}. {p.get("name", "")}')
            price = p.get('price', 0)
            sale_price = p.get('sale_price')
            price_str = f'   Price: ₦{price}'
            if sale_price:
                price_str += f' (Sale: ₦{sale_price})'
            parts.append(price_str)
            parts.append(f'   Rating: {p.get("rating", 0)}/5 ({p.get("reviews_count", 0)} reviews)')
            if p.get('brand'):
                parts.append(f'   Brand: {p["brand"]}')
            parts.append(f'   In Stock: {"Yes" if p.get("in_stock") else "No"}')
            if p.get('discount_percentage'):
                parts.append(f'   Discount: {p["discount_percentage"]}% off')
            if p.get('description'):
                parts.append(f'   Description: {p["description"]}')
            if p.get('highlights'):
                parts.append('   Key Highlights:')
                for h in p['highlights'][:5]:
                    parts.append(f'     - {h.get("label", "")}')
            if p.get('specifications'):
                parts.append('   Specifications:')
                for spec in p['specifications'][:3]:
                    parts.append(f'     {spec.get("group_name", "")}:')
                    parts.append(f'       - {spec.get("spec_name", "")}: {spec.get("spec_value", "")}')
    elif intent.get('intent') == 'product_search':
        parts.append('\nNo products found for this specific search.')
        parts.append('Please provide a helpful response explaining this and suggest alternatives or ways to refine the search.')

    # Conversation context
    if conversation_context:
        parts.append('\nRecent conversation context:')
        for ctx in conversation_context[:3]:
            parts.append(f'- User mentioned: {ctx.get("user_message", "")}')
            if ctx.get('extracted_info'):
                parts.append(f'  Preferences: {ctx["extracted_info"]}')

    # FAQ context
    if faqs:
        parts.append('\nRelevant FAQ information:')
        for faq in faqs[:3]:
            parts.append(f'Q: {faq.get("question", "")}')
            parts.append(f'A: {faq.get("answer", "")}')

    # Product specs context
    if product_specs:
        parts.append('\nProduct Specifications:')
        for spec in product_specs[:10]:
            parts.append(f'  - {spec.get("spec_name", "")}: {spec.get("spec_value", "")}')

    parts.append('\nPlease provide a helpful, natural response as UJUNWA. Be specific about product features and benefits when relevant.')

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Suggestions (match mobile exactly)
# ---------------------------------------------------------------------------
def _generate_suggestions(intent: dict, products: list) -> list:
    intent_type = intent.get('intent', 'general')

    if intent_type == 'product_search':
        if products:
            return [
                'Show me more details about these products',
                'Find similar products',
                'Compare these products',
                'Check if these are in stock',
            ]
        return [
            'Browse all products',
            'Show me trending items',
            'Find products in different categories',
            'Help me refine my search',
        ]
    if intent_type == 'product_info':
        return [
            'Show me similar products',
            'Check customer reviews',
            'Find products in my size',
            'Add to wishlist',
        ]
    if intent_type == 'recommendation':
        return [
            'Tell me more about your preferences',
            'Show me products in different price ranges',
            'Find trending products',
            'Browse by category',
        ]
    if intent_type == 'order_inquiry':
        return ORDER_INQUIRY_SUGGESTIONS
    if intent_type == 'support':
        return SUPPORT_SUGGESTIONS

    return [
        'Find products',
        'Track my orders',
        'Get recommendations',
        'Browse categories',
    ]
