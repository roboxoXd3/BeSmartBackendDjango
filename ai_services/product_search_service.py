"""
Product Search Service — mirrors mobile ProductSearchService.

Implements:
- hybridSearch (keyword + vector similarity)
- searchProducts (PostgreSQL full-text search)
- semanticSearch (pgvector via match_products RPC)
- enhancedKeywordSearch (ILIKE multi-field with synonym expansion)
- searchByImage (OpenAI Vision → hybrid search)
- getTrendingProducts

All queries hit the same Supabase PostgreSQL DB Django is connected to.
"""
import logging
import uuid as uuid_module

from django.db import connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hybrid_search(query: str, limit: int = 20) -> list[dict]:
    """
    Combine keyword + semantic search, score and rank.
    Mirrors mobile's ProductSearchService.hybridSearch().
    """
    try:
        semantic_results = semantic_search(query, limit=limit, threshold=0.3)
        keyword_results = search_products(query, limit=limit)

        product_scores: dict[str, float] = {}
        all_products: dict[str, dict] = {}
        query_terms = _extract_key_terms(query)

        # Keyword results get higher base score
        for i, p in enumerate(keyword_results):
            pid = str(p['id'])
            all_products[pid] = p
            score = 20.0 - (i * 0.5)
            score += _calculate_relevance(p, query_terms)
            product_scores[pid] = score

        # Semantic results — filter out irrelevant
        for i, p in enumerate(semantic_results):
            pid = str(p['id'])
            if pid in all_products:
                continue
            relevance = _calculate_relevance(p, query_terms)
            if relevance > 0:
                all_products[pid] = p
                product_scores[pid] = (10.0 - i) + relevance

        sorted_products = sorted(
            all_products.values(),
            key=lambda p: product_scores.get(str(p['id']), 0),
            reverse=True,
        )
        return sorted_products[:limit]

    except Exception as e:
        logger.error('Hybrid search failed: %s', e)
        return search_products(query, limit=limit)


def search_products(query: str, limit: int = 20) -> list[dict]:
    """
    PostgreSQL full-text search on search_vector with ILIKE fallback.
    Mirrors mobile's searchProducts().
    """
    try:
        with connection.cursor() as c:
            # Try full-text search first
            c.execute("""
                SELECT p.*, v.business_name AS vendor_name
                FROM products p
                LEFT JOIN vendors v ON v.id = p.vendor_id
                WHERE p.in_stock = true
                  AND p.approval_status = 'approved'
                  AND p.status = 'active'
                  AND p.search_vector @@ plainto_tsquery('english', %s)
                ORDER BY ts_rank(p.search_vector, plainto_tsquery('english', %s)) DESC
                LIMIT %s
            """, [query, query, limit])
            rows = _dictfetchall(c)

            if rows:
                return rows

            # Fallback: ILIKE
            like_q = f'%{query}%'
            c.execute("""
                SELECT p.*, v.business_name AS vendor_name
                FROM products p
                LEFT JOIN vendors v ON v.id = p.vendor_id
                WHERE p.in_stock = true
                  AND p.approval_status = 'approved'
                  AND p.status = 'active'
                  AND (p.name ILIKE %s OR p.description ILIKE %s OR p.brand ILIKE %s)
                ORDER BY p.rating DESC
                LIMIT %s
            """, [like_q, like_q, like_q, limit])
            return _dictfetchall(c)

    except Exception as e:
        logger.error('search_products error: %s', e)
        return []


def semantic_search(query: str, limit: int = 10, threshold: float = 0.3) -> list[dict]:
    """
    Vector similarity search using the match_products RPC function in the DB.
    Mirrors mobile's semanticSearch().
    """
    try:
        # Generate embedding via OpenAI
        from openai import OpenAI
        from django.conf import settings

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            return enhanced_keyword_search(query, limit=limit)

        client = OpenAI(api_key=api_key)
        embedding_response = client.embeddings.create(
            model='text-embedding-3-small',
            input=query,
        )
        query_embedding = embedding_response.data[0].embedding

        # Call the match_products RPC
        with connection.cursor() as c:
            c.execute("""
                SELECT * FROM match_products(%s::vector, %s, %s)
            """, [str(query_embedding), threshold, limit])
            cols = [col[0] for col in c.description] if c.description else []
            rows = []
            for row in c.fetchall():
                d = {}
                for i, col_name in enumerate(cols):
                    val = row[i]
                    if isinstance(val, uuid_module.UUID):
                        val = str(val)
                    d[col_name] = val
                rows.append(d)

        # Add approval_status defaults for products from RPC
        for r in rows:
            r.setdefault('approval_status', 'approved')
            r.setdefault('status', 'active')

        return rows

    except Exception as e:
        logger.warning('Semantic search failed, falling back to keyword: %s', e)
        return enhanced_keyword_search(query, limit=limit)


def enhanced_keyword_search(query: str, limit: int = 10) -> list[dict]:
    """
    Multi-field ILIKE search with synonym expansion.
    Mirrors mobile's enhancedKeywordSearch().
    """
    try:
        expanded = _expand_search_query(query)
        words = list(set(
            w for w in expanded.lower().split()
            if len(w) > 2
        ))

        if not words:
            return get_trending_products(limit=limit)

        seen = set()
        results = []

        for word in words[:8]:
            like_w = f'%{word}%'
            with connection.cursor() as c:
                c.execute("""
                    SELECT p.*, v.business_name AS vendor_name
                    FROM products p
                    LEFT JOIN vendors v ON v.id = p.vendor_id
                    WHERE p.in_stock = true
                      AND p.approval_status = 'approved'
                      AND p.status = 'active'
                      AND (p.name ILIKE %s OR p.description ILIKE %s OR p.brand ILIKE %s)
                    ORDER BY p.rating DESC
                    LIMIT %s
                """, [like_w, like_w, like_w, limit])
                for row in _dictfetchall(c):
                    pid = str(row['id'])
                    if pid not in seen:
                        seen.add(pid)
                        results.append(row)

        results.sort(key=lambda p: float(p.get('rating') or 0), reverse=True)
        return results[:limit]

    except Exception as e:
        logger.error('Enhanced keyword search failed: %s', e)
        return []


def get_trending_products(limit: int = 10) -> list[dict]:
    """Top-rated in-stock products."""
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT p.*, v.business_name AS vendor_name
                FROM products p
                LEFT JOIN vendors v ON v.id = p.vendor_id
                WHERE p.in_stock = true
                  AND p.approval_status = 'approved'
                  AND p.status = 'active'
                ORDER BY p.rating DESC, p.reviews DESC
                LIMIT %s
            """, [limit])
            return _dictfetchall(c)
    except Exception as e:
        logger.error('get_trending_products error: %s', e)
        return []


def search_by_image_description(description: str, limit: int = 10) -> list[dict]:
    """
    Given a text description from image analysis, search products.
    Mirrors mobile's searchByImage() flow (after image analysis).
    """
    if not description or description.lower().strip() == 'product search':
        return enhanced_keyword_search('product', limit=limit)

    # Semantic search with image-specific threshold
    semantic = semantic_search(description, limit=limit, threshold=0.2)

    if semantic:
        scored = _score_by_relevance(semantic, description)
        return scored[:limit]

    # Fallback to keyword
    keyword = enhanced_keyword_search(description, limit=limit)
    if keyword:
        scored = _score_by_relevance(keyword, description)
        return scored[:limit]

    return []


# ---------------------------------------------------------------------------
# Enrichment: Add highlights, specs, etc. to product dicts
# ---------------------------------------------------------------------------

def enrich_products(products: list[dict]) -> list[dict]:
    """Add highlights and specifications to product dicts for AI context."""
    if not products:
        return products

    product_ids = [str(p['id']) for p in products]
    highlights_map = {}
    specs_map = {}

    try:
        with connection.cursor() as c:
            # Product highlights
            placeholders = ','.join(['%s'] * len(product_ids))
            c.execute(f"""
                SELECT product_id, label, icon_url, sort_order
                FROM product_highlights
                WHERE product_id::text IN ({placeholders})
                ORDER BY sort_order
            """, product_ids)
            for row in c.fetchall():
                pid = str(row[0])
                highlights_map.setdefault(pid, []).append({
                    'label': row[1], 'icon_url': row[2],
                })

            # Product specifications
            c.execute(f"""
                SELECT product_id, group_name, spec_name, spec_value, sort_order
                FROM product_specifications
                WHERE product_id::text IN ({placeholders})
                ORDER BY sort_order
            """, product_ids)
            for row in c.fetchall():
                pid = str(row[0])
                specs_map.setdefault(pid, []).append({
                    'group_name': row[1], 'spec_name': row[2], 'spec_value': row[3],
                })
    except Exception as e:
        logger.warning('enrich_products failed: %s', e)

    for p in products:
        pid = str(p['id'])
        p['highlights'] = highlights_map.get(pid, [])
        p['specifications'] = specs_map.get(pid, [])

    return products


# ---------------------------------------------------------------------------
# Knowledge base helpers
# ---------------------------------------------------------------------------

def get_relevant_faqs(query: str, limit: int = 5) -> list[dict]:
    """Search FAQs by keyword (mirrors mobile KnowledgeBaseService)."""
    try:
        like_q = f'%{query.lower()}%'
        with connection.cursor() as c:
            c.execute("""
                SELECT id, question, answer, category, order_index
                FROM faqs
                WHERE question ILIKE %s OR answer ILIKE %s
                ORDER BY order_index
                LIMIT %s
            """, [like_q, like_q, limit])
            return _dictfetchall(c)
    except Exception as e:
        logger.warning('get_relevant_faqs error: %s', e)
        return []


def get_product_specs(product_id: str) -> list[dict]:
    """Get specifications for a product."""
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT id, product_id, group_name, spec_name, spec_value, sort_order
                FROM product_specifications
                WHERE product_id = %s
                ORDER BY sort_order
            """, [product_id])
            return _dictfetchall(c)
    except Exception as e:
        logger.warning('get_product_specs error: %s', e)
        return []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dictfetchall(cursor) -> list[dict]:
    """Convert cursor rows to list of dicts."""
    cols = [col[0] for col in cursor.description] if cursor.description else []
    rows = []
    for row in cursor.fetchall():
        d = {}
        for i, col_name in enumerate(cols):
            val = row[i]
            if isinstance(val, uuid_module.UUID):
                val = str(val)
            d[col_name] = val
        rows.append(d)
    return rows


def _extract_key_terms(query: str) -> list[str]:
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our',
        'their', 'show', 'if', 'got', 'any', 'some', 'find', 'search', 'looking',
        'want', 'need', 'buy', 'please', 'get',
    }
    return [w for w in query.lower().split() if w and w not in stop_words]


def _calculate_relevance(product: dict, query_terms: list[str]) -> float:
    if not query_terms:
        return 0.0
    score = 0.0
    name = (product.get('name') or '').lower()
    desc = (product.get('description') or '').lower()
    brand = (product.get('brand') or '').lower()

    for term in query_terms:
        if term in name:
            score += 5.0
        if term in desc:
            score += 2.0
        if term in brand:
            score += 1.0
    return score


SYNONYMS = {
    'shirt': 'shirts top tops blouse tee t-shirt',
    'pants': 'pant trousers jeans bottoms',
    'shoes': 'shoe sneakers boots sandals footwear',
    'sneakers': 'sneaker shoes boots running',
    'watch': 'watches smartwatch smartwatches timepiece',
    'bag': 'bags handbag purse backpack',
    'dress': 'dresses gown frock outfit',
    'jacket': 'jackets coat blazer outerwear',
    'cheap': 'affordable budget discounted',
    'expensive': 'premium luxury high-end',
}


def _expand_search_query(query: str) -> str:
    expanded = query.lower()
    for key, value in SYNONYMS.items():
        if key in expanded:
            expanded += ' ' + value
    return expanded


def _score_by_relevance(products: list[dict], description: str) -> list[dict]:
    """
    Score products by relevance to image description.
    Mirrors mobile's _scoreProductsByRelevance().
    """
    desc_lower = description.lower()

    category_bonuses = [
        (['shoes', 'sneakers', 'running shoes', 'athletic', 'footwear'],
         ['shoe', 'sneaker', 'running'], 100),
        (['smartwatch', 'smart watch', 'watch', 'wearable'],
         ['smart', 'watch'], 100),
        (['shirt', 't-shirt', 'top', 'clothing'],
         ['shirt', 't-shirt'], 100),
        (['yoga', 'pants', 'leggings', 'workout'],
         ['yoga', 'pants'], 100),
        (['sunglasses', 'glasses', 'eyewear'],
         ['sunglasses', 'glasses'], 100),
        (['wallet', 'leather'],
         ['wallet', 'leather'], 100),
        (['earbuds', 'headphones', 'wireless', 'bluetooth'],
         ['earbuds', 'headphones', 'wireless'], 100),
    ]

    colors = ['black', 'white', 'gray', 'grey', 'pink', 'blue', 'red',
              'green', 'silver', 'gold']
    materials = ['leather', 'fabric', 'cotton', 'silk', 'wool', 'denim',
                 'metal', 'steel', 'silicone', 'rubber']

    scored = []
    for p in products:
        score = 0.0
        name = (p.get('name') or '').lower()
        pdesc = (p.get('description') or '').lower()

        for desc_keywords, name_keywords, bonus in category_bonuses:
            if any(kw in desc_lower for kw in desc_keywords):
                if any(kw in name for kw in name_keywords):
                    score += bonus
                    break

        for color in colors:
            if color in desc_lower and (color in name or color in pdesc):
                score += 10.0

        for mat in materials:
            if mat in desc_lower and (mat in name or mat in pdesc):
                score += 15.0

        scored.append((p, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, s in scored if s > 0] or [p for p, _ in scored]
