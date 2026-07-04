#!/usr/bin/env python3
"""
Diagnostic script - check product count and query patterns via raw SQL on the database.
This bypasses Django entirely to measure pure database performance.
"""
import psycopg2
import time
import os
from dotenv import load_dotenv

load_dotenv('/home/unthinkable/Projects/BeSmartBackend/.env')

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
}

print(f"Connecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("\n" + "="*60)
print("  DATABASE DIAGNOSTIC")
print("="*60)

# 1. Check total product count
print("\n--- Product Counts ---")
queries = [
    ("Total products", "SELECT COUNT(*) FROM products"),
    ("Active + Approved products", "SELECT COUNT(*) FROM products WHERE status='active' AND approval_status='approved'"),
    ("Featured products", "SELECT COUNT(*) FROM products WHERE is_featured=true AND status='active' AND approval_status='approved'"),
    ("New arrival products", "SELECT COUNT(*) FROM products WHERE is_new_arrival=true AND status='active' AND approval_status='approved'"),
    ("On sale products", "SELECT COUNT(*) FROM products WHERE is_on_sale=true AND status='active' AND approval_status='approved'"),
]

for label, sql in queries:
    start = time.time()
    cur.execute(sql)
    count = cur.fetchone()[0]
    elapsed = time.time() - start
    print(f"  {label}: {count} ({elapsed:.3f}s)")

# 2. Check category counts  
print("\n--- Category Counts ---")
cat_queries = [
    ("Total categories", "SELECT COUNT(*) FROM categories"),
    ("Active categories", "SELECT COUNT(*) FROM categories WHERE is_active=true"),
    ("Total subcategories", "SELECT COUNT(*) FROM subcategories"),
    ("Active subcategories", "SELECT COUNT(*) FROM subcategories WHERE is_active=true"),
]

for label, sql in cat_queries:
    start = time.time()
    cur.execute(sql)
    count = cur.fetchone()[0]
    elapsed = time.time() - start
    print(f"  {label}: {count} ({elapsed:.3f}s)")

# 3. Measure raw product query times (no serialization, no Django)
print("\n--- Raw Query Benchmarks ---")
benchmark_queries = [
    ("All products (raw SELECT *)", "SELECT * FROM products WHERE status='active' AND approval_status='approved'"),
    ("All products (id, name, price only)", "SELECT id, name, price FROM products WHERE status='active' AND approval_status='approved'"),
    ("All categories with subcategories", """
        SELECT c.*, s.id as sub_id, s.name as sub_name
        FROM categories c 
        LEFT JOIN subcategories s ON c.id = s.category_id AND s.is_active = true
        WHERE c.is_active = true 
        ORDER BY c.name
    """),
    ("Products with category name (JOIN)", """
        SELECT p.id, p.name, p.price, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.status='active' AND p.approval_status='approved'
    """),
]

for label, sql in benchmark_queries:
    start = time.time()
    cur.execute(sql)
    rows = cur.fetchall()
    elapsed = time.time() - start
    print(f"  {label}: {len(rows)} rows ({elapsed:.3f}s)")

# 4. Check for N+1 - simulate what the serializer does
print("\n--- N+1 Query Simulation ---")
start = time.time()
cur.execute("SELECT id, category_id FROM products WHERE status='active' AND approval_status='approved'")
products = cur.fetchall()
product_fetch_time = time.time() - start
print(f"  Fetch all products: {len(products)} rows ({product_fetch_time:.3f}s)")

# Now simulate N+1: for each product, query category
start = time.time()
category_queries = 0
for pid, cat_id in products[:50]:  # limit to 50 to not take forever
    if cat_id:
        cur.execute("SELECT name FROM categories WHERE id = %s", (str(cat_id),))
        cur.fetchone()
        category_queries += 1
n_plus_1_time = time.time() - start
print(f"  50 individual category lookups: {category_queries} queries ({n_plus_1_time:.3f}s)")
estimated_full = (n_plus_1_time / 50) * len(products) if products else 0
print(f"  Estimated time for ALL {len(products)} product category lookups: {estimated_full:.1f}s ⚠️")

# 5. Check indexes
print("\n--- Index Analysis ---")
cur.execute("""
    SELECT tablename, indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename IN ('products', 'categories', 'subcategories') 
    ORDER BY tablename, indexname
""")
indexes = cur.fetchall()
for table, name, defn in indexes:
    print(f"  [{table}] {name}: {defn[:100]}")

# 6. Check table sizes
print("\n--- Table Sizes ---")
cur.execute("""
    SELECT relname, pg_size_pretty(pg_total_relation_size(c.oid))
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE relname IN ('products', 'categories', 'subcategories', 'product_reviews', 
                       'product_qa', 'delivery_info', 'warranty_info')
    AND n.nspname = 'public'
    ORDER BY pg_total_relation_size(c.oid) DESC
""")
for name, size in cur.fetchall():
    print(f"  {name}: {size}")

# 7. Test connection latency
print("\n--- Connection Latency ---")
times = []
for i in range(5):
    start = time.time()
    cur.execute("SELECT 1")
    cur.fetchone()
    elapsed = time.time() - start
    times.append(elapsed)
    
avg_latency = sum(times) / len(times)
print(f"  Ping (SELECT 1): avg {avg_latency*1000:.1f}ms, min {min(times)*1000:.1f}ms, max {max(times)*1000:.1f}ms")

cur.close()
conn.close()

print(f"\n{'='*60}")
print("  DIAGNOSTIC COMPLETE")
print(f"{'='*60}\n")
