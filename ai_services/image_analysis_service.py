"""
Image Analysis Service — mirrors mobile ImageSearchService.

Sends base64 image to OpenAI GPT-4o-mini Vision API and returns a product
description string suitable for search.
"""
import base64
import logging
import time

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

IMAGE_ANALYSIS_PROMPT = """Analyze this image and describe what product the user is looking for. 
Focus on:
- Product type (clothing, electronics, shoes, etc.)
- Key features (color, style, material, brand if visible)
- Specific details that would help find similar products

Provide a concise description in 1-2 sentences that would work well for product search.
Example: "Black leather boots with zipper closure and medium heel"
"""

MAX_RETRIES = 3


def analyze_image(image_bytes: bytes, content_type: str = 'image/jpeg') -> str:
    """
    Analyze an image and return a product-search-friendly description.
    Implements retry with exponential backoff (matches mobile behavior).

    Args:
        image_bytes: Raw image bytes
        content_type: MIME type of the image

    Returns:
        Product description string, or 'product search' as fallback.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        logger.error('OPENAI_API_KEY not configured')
        return 'product search'

    b64 = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f'data:{content_type};base64,{b64}'

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': IMAGE_ANALYSIS_PROMPT},
                            {'type': 'image_url', 'image_url': {'url': data_url}},
                        ],
                    }
                ],
                max_tokens=100,
                temperature=0.3,
            )
            description = response.choices[0].message.content.strip()
            logger.info('Image analysis result: %s', description)
            return description

        except Exception as e:
            logger.warning('Image analysis attempt %d/%d failed: %s', attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(1 * attempt)  # exponential backoff

    logger.error('All image analysis attempts failed, returning fallback')
    return 'product search'
