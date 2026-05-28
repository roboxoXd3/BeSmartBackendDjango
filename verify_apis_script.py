import os
import re
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'besmart_backend.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def get_all_urls(resolver=None, pre=''):
    if resolver is None:
        resolver = get_resolver()
    urls = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            try:
                pattern_str = str(pattern.pattern)
            except:
                pattern_str = ''
            urls.extend(get_all_urls(pattern, pre + pattern_str))
        elif isinstance(pattern, URLPattern):
            try:
                pattern_str = str(pattern.pattern)
            except:
                pattern_str = ''
            full_path = pre + pattern_str
            clean_path = re.sub(r'\^|\$', '', full_path)
            clean_path = re.sub(r'\(\?P<([^>]+)>[^)]+\)', r'{\1}', clean_path)
            clean_path = re.sub(r'<int:[^>]+>', '{id}', clean_path)
            clean_path = re.sub(r'<uuid:[^>]+>', '{id}', clean_path)
            clean_path = re.sub(r'<str:[^>]+>', '{id}', clean_path)
            clean_path = re.sub(r'<[^>]+>', '{id}', clean_path)
            urls.append(clean_path.replace('\\/', '/'))
    return urls

all_django_paths = get_all_urls()
all_django_paths = ['/' + p if not p.startswith('/') else p for p in all_django_paths]

def path_match(req_path, registered_paths):
    req_path = req_path.rstrip('/') + '/'
    req_path_segments = req_path.split('/')
    
    for r_path in registered_paths:
        r_path = r_path.rstrip('/') + '/'
        r_path_segments = r_path.split('/')
        
        if len(req_path_segments) != len(r_path_segments):
            continue
            
        match = True
        for req_seg, r_seg in zip(req_path_segments, r_path_segments):
            if req_seg.startswith('{') and req_seg.endswith('}'):
                if not (r_seg.startswith('{') and r_seg.endswith('}')):
                    match = False
                    break
            elif req_seg != r_seg:
                match = False
                break
        if match:
            return True
    return False

md_files = [
    'API_ENDPOINTS_BY_APPLICATION.md',
    'DJANGO_SQUAD_PAYMENT_INTEGRATION_GUIDE.md',
    'UJUNWA_AI_IMPLEMENTATION_PLAN.md',
    'missing_apis.md'
]

required_endpoints = []
# Match tables like | GET | `/api/cart/` | Description | Used By |
row_regex = re.compile(r'\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\s*\|(?:\s*([^|]+)\s*\|)?')

for md in md_files:
    if os.path.exists(md):
        with open(md, 'r') as f:
            for line in f:
                m = row_regex.search(line)
                if m:
                    required_endpoints.append({
                        'method': m.group(1).strip(),
                        'path': m.group(2).strip(),
                        'description': m.group(3).strip() if m.group(3) else 'N/A',
                        'used_by': m.group(4).strip() if m.group(4) else 'N/A',
                        'source': md
                    })

unique_reqs = {}
for req in required_endpoints:
    key = f"{req['method']} {req['path']}"
    if key not in unique_reqs:
        unique_reqs[key] = req

missing = []
for key, req in unique_reqs.items():
    if not path_match(req['path'], all_django_paths):
        missing.append(req)

print(f"Total required endpoints parsed: {len(unique_reqs)}")
print(f"Total Django paths registered: {len(all_django_paths)}")
print(f"Total missing: {len(missing)}")

with open('final_missing_apis.md', 'w') as f:
    f.write('# Final Missing APIs Verification Report\n\n')
    
    f.write('This document lists all the APIs defined in the technical specification documentation that currently have **NO exact match** in the implemented Django URL routing configurations (`urls.py`).\n')
    f.write('Some of these APIs might be completely unimplemented, while others may have been implemented under a divergent URL scheme causing a 404 mismatch for connecting clients.\n\n')
    
    if not missing:
        f.write('🎉 **All required APIs from the markdown specifications have been successfully implemented and registered in Django!**\n')
        f.write('No APIs are left unimplemented.\n')
    else:
        f.write(f'⚠️ **{len(missing)} APIs** require further implementation or URL correction:\n\n')
        f.write('| Method | Endpoint | Description | Used By | Source |\n')
        f.write('|--------|----------|-------------|---------|--------|\n')
        for req in missing:
            f.write(f"| {req['method']} | `{req['path']}` | {req['description']} | {req['used_by']} | {req['source']} |\n")

print("Done. Generated final_missing_apis.md")
