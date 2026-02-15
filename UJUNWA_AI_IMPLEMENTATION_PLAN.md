# UJUNWA AI & Image Search - Django Implementation Plan

**Date:** February 14, 2026  
**Status:** Ready for implementation  
**OpenAI API:** Already configured in `.env`

---

## Executive Summary

Implement UJUNWA AI chat assistant and image-based product search in Django backend. All AI processing moves server-side for security (API key protection, rate limiting, cost control). Mobile app will call Django API instead of OpenAI/Supabase directly.

---

## Phase 0: Pre-requisites & Configuration

### 0.1 Add OpenAI to Django Settings
- [ ] Add `OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')` to `besmart_backend/settings.py`
- [ ] Add `openai` to `requirements.txt` if not present
- [ ] Verify `.env` has `OPENAI_API_KEY` (✅ already present)

### 0.2 Install Dependencies
```bash
pip install openai
```

---

## Phase 1: AI Services Layer (~2–3 hours)

### 1.1 Create `ai_services` App
```bash
python manage.py startapp ai_services
```
Add to `INSTALLED_APPS`.

### 1.2 Add ConversationContext Model to Support
The `conversation_context` table exists in DB but has no Django model. Add to `support/models.py`:

```python
from django.contrib.postgres.fields import ArrayField

class ConversationContext(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_message = models.TextField()
    intent_type = models.CharField(max_length=50)
    intent_confidence = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    ai_response = models.TextField()
    extracted_info = models.TextField(null=True, blank=True)
    products_mentioned = ArrayField(models.UUIDField(), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation_context'
        managed = False  # Table exists in Supabase
```

**Note:** `products_mentioned` is `uuid[]` in PostgreSQL. Use `ArrayField(models.UUIDField())`.

### 1.3 Create AI Services (in `ai_services/`)

| File | Purpose | Depends On |
|------|---------|------------|
| `intent_service.py` | IntentRecognitionService – classify user message via OpenAI | openai, settings.OPENAI_API_KEY |
| `response_service.py` | ResponseGenerationService – generate UJUNWA reply | intent_service, openai |
| `context_service.py` | ContextManagementService – get/store conversation context | support.models |
| `image_search_service.py` | ImageSearchService – analyze image via Vision API | openai, Product search |

**Intent types:** `product_search`, `product_info`, `order_inquiry`, `comparison`, `recommendation`, `support`, `greeting`, `general`

**Key methods:**
- `IntentRecognitionService.recognize_intent(message)` → `{intent, confidence, entities}`
- `ResponseGenerationService.generate_response(user_message, intent, products, context, preferences)` → `{text, suggestions, products}`
- `ContextManagementService.get_conversation_context(conversation_id)`, `store_conversation_context(...)`, `get_user_preferences(user_id)`
- `ImageSearchService.search_by_image(image_base64, limit)` → analyze with Vision → search products

---

## Phase 2: Product Search Service (~1 hour)

### 2.1 Create `products/services/product_search_service.py`

Product search used by both chat and image search:

```python
# products/services/product_search_service.py
class ProductSearchService:
    def hybrid_search(self, query: str, limit: int = 10) -> List[Product]:
        """Keyword search (no vector/semantic for now - add later if needed)"""
        # Use Product.objects.filter + Q(name__icontains) | Q(description__icontains) | Q(brand__icontains)
        # Filter: status='active', approval_status='approved'
        # Order by: rating desc, then added_date desc
        # [:limit]
        pass

    def get_trending_products(self, limit: int = 5) -> List[Product]:
        """Fallback when search returns nothing"""
        # Featured or high-rated, recent
        pass
```

**Phase 2B (Optional):** Add semantic/vector search later (requires embeddings table, OpenAI embeddings API, or pgvector).

---

## Phase 3: Chat API Endpoints (~2 hours)

### 3.1 Extend Support App or Add Chat Module

**Option A (Recommended):** Add UJUNWA actions to existing support chat.

Create `support/chat_views.py` with:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `POST /api/support/chat/send/` | POST | Send message to UJUNWA, get AI response |

**Request:**
```json
{
  "conversation_id": "uuid (optional)",
  "message": "show me running shoes",
  "message_type": "text",
  "image_data": "base64 string (optional, for image search)"
}
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "uuid",
  "user_message": {...},
  "bot_response": {
    "id": "uuid",
    "text": "I found 5 great running shoes...",
    "products": [...],
    "suggestions": ["Show me Nike", "Under 15k"],
    "created_at": "..."
  }
}
```

### 3.2 Flow in `send_message` View
1. Validate JWT, check rate limit (e.g. 30 msg/hour)
2. Get or create ChatConversation
3. Save user ChatMessage
4. Log ChatAnalytics (message_sent)
5. If `message_type == 'image'` and `image_data`:
   - Call ImageSearchService.search_by_image(image_data)
   - Use products as context for response
6. Else:
   - Call IntentRecognitionService.recognize_intent(message)
   - Get ContextManagementService.get_conversation_context()
   - Get ContextManagementService.get_user_preferences()
   - If product_search/product_info/recommendation: call ProductSearchService.hybrid_search(extracted_terms)
   - Call ResponseGenerationService.generate_response(...)
7. Store ContextManagementService.store_conversation_context(...)
8. Save bot ChatMessage with text, products, suggestions in metadata
9. Log ChatAnalytics (ai_response_generated)
10. Return response

### 3.3 Rate Limiting
- Use `django-ratelimit` or custom throttle: e.g. 30 messages per user per hour for `/api/support/chat/send/`

---

## Phase 4: Image Search API (~1 hour)

### 4.1 Endpoint
`POST /api/products/search-by-image/`

**Request:**
- `Content-Type: multipart/form-data` with `image` file, OR
- `Content-Type: application/json` with `image_data` (base64 string)

**Response:**
```json
{
  "products": [...],
  "description": "Blue running shoes, athletic style, mesh material",
  "count": 5
}
```

**Flow:**
1. Validate image (max 5MB, jpg/png)
2. If multipart: read file → base64
3. Call ImageSearchService.search_by_image(base64, limit=10)
4. Return products + AI description

---

## Phase 5: URL & Router Updates

### 5.1 Add Routes
In `support/urls.py`:
```python
path('chat/send/', UjunwaSendMessageView.as_view(), name='chat-send'),
```

In `products/urls.py`:
```python
path('search-by-image/', ProductSearchByImageView.as_view(), name='product-search-by-image'),
```

---

## Phase 6: Mobile App Integration (Post-Backend)

### 6.1 Chat
- Change `chat_repository` or equivalent to call `POST {{base_url}}/api/support/chat/send/` with JWT
- Remove client-side OpenAI calls for chat
- Keep UI flow: send message → show typing → receive bot_response

### 6.2 Image Search
- **Search screen:** Call `POST {{base_url}}/api/products/search-by-image/` with image file
- **Chatbot:** When user sends image, call same endpoint or use chat send with `message_type: 'image'`, `image_data: base64`
- Remove `ImageSearchService` OpenAI calls from mobile; remove `OPENAI_API_KEY` from mobile `.env`

---

## File Structure Summary

```
BeSmartBackendDjango/
├── ai_services/
│   ├── __init__.py
│   ├── apps.py
│   ├── intent_service.py
│   ├── response_service.py
│   ├── context_service.py
│   └── image_search_service.py
├── products/
│   ├── services/
│   │   ├── __init__.py
│   │   └── product_search_service.py
│   ├── views.py  # Add ProductSearchByImageView
│   └── urls.py   # Add search-by-image
├── support/
│   ├── models.py      # Add ConversationContext
│   ├── chat_views.py  # NEW: UjunwaSendMessageView
│   ├── serializers.py # Add SendMessageSerializer
│   └── urls.py        # Add chat/send/
└── besmart_backend/
    └── settings.py    # Add OPENAI_API_KEY
```

---

## Implementation Order

| Step | Task | Est. | Blocks |
|------|------|------|--------|
| 1 | Add OPENAI_API_KEY to settings, install openai | 15m | — |
| 2 | Create ai_services app, IntentRecognitionService | 45m | — |
| 3 | Create ResponseGenerationService | 45m | Step 2 |
| 4 | Add ConversationContext model, ContextManagementService | 30m | — |
| 5 | Create ProductSearchService (hybrid_search) | 45m | — |
| 6 | Create ImageSearchService | 30m | Step 5 |
| 7 | ProductSearchByImageView (POST /products/search-by-image/) | 45m | Step 6 |
| 8 | UjunwaSendMessageView (POST /support/chat/send/) | 1.5h | Steps 2–5 |
| 9 | Rate limiting for chat | 20m | Step 8 |
| 10 | Postman collection updates | 20m | — |
| 11 | Mobile app integration (separate task) | 2h | All |

**Total backend estimate:** ~6–7 hours

---

## Testing Checklist

- [ ] `POST /api/products/search-by-image/` with valid image returns products
- [ ] `POST /api/support/chat/send/` with text message returns AI response
- [ ] `POST /api/support/chat/send/` with image returns products in response
- [ ] New conversation created when no conversation_id
- [ ] Existing conversation continued when conversation_id provided
- [ ] Rate limit blocks after N messages
- [ ] OpenAI failure returns graceful fallback (no 500)
- [ ] Intent: greeting → welcome message
- [ ] Intent: product_search → products in response

---

## Security Notes

- OpenAI API key never leaves server
- Validate image size/type before processing
- Authenticate all chat and image-search requests (JWT)
- Log usage for cost monitoring
- Consider caching frequent product-search queries (optional)

---

## References

- `backend-documentation/CHAT_ASSISTANT_REQUIREMENTS.md`
- `backend-documentation/DJANGO_CHAT_ASSISTANT_IMPLEMENTATION_GUIDE.md`
- `support/models.py` (ChatConversation, ChatMessage, ChatAnalytics)
- `ecom_app/lib/features/data/services/image_search_service.dart` (current mobile impl)
