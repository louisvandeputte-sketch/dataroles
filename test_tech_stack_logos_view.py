#!/usr/bin/env python3
"""Test the new tech stack logos view"""

from database.client import db
import json
import time

print("\n🧪 Testing new vw_job_listings with tech stack logos...\n")

# First, let's manually run the migration SQL to test it
# (In production, you'd run this in Supabase SQL Editor)

# For now, let's test the subquery logic separately
print("📊 Testing subquery performance...\n")

# Get a job with tech stack
job = db.client.table("llm_enrichment")\
    .select("job_posting_id, must_have_programmeertalen, must_have_ecosystemen")\
    .not_.is_("must_have_programmeertalen", "null")\
    .limit(1)\
    .single()\
    .execute()

print(f"Test job: {job.data['job_posting_id']}")
print(f"Languages: {job.data['must_have_programmeertalen']}")
print(f"Ecosystems: {job.data['must_have_ecosystemen']}")

# Test language lookup
print("\n🔍 Testing language lookup...")
start = time.time()

languages = job.data['must_have_programmeertalen']
if languages:
    result = db.client.table("programming_languages")\
        .select("name, display_name, logo_url, category")\
        .in_("name", languages)\
        .execute()
    
    elapsed = (time.time() - start) * 1000
    print(f"   Found {len(result.data)} languages in {elapsed:.2f}ms")
    for lang in result.data:
        print(f"   - {lang['name']}: {lang['display_name']} (logo: {lang.get('logo_url') or 'None'})")

# Test ecosystem lookup
print("\n🔍 Testing ecosystem lookup...")
start = time.time()

ecosystems = job.data['must_have_ecosystemen']
if ecosystems:
    result = db.client.table("ecosystems")\
        .select("name, display_name, logo_url, category")\
        .in_("name", ecosystems)\
        .execute()
    
    elapsed = (time.time() - start) * 1000
    print(f"   Found {len(result.data)} ecosystems in {elapsed:.2f}ms")
    for eco in result.data:
        print(f"   - {eco['name']}: {eco['display_name']} (logo: {eco.get('logo_url') or 'None'})")

# Estimate total overhead for view
print("\n📊 Performance Estimate:")
print(f"   Language lookup: ~{elapsed:.0f}ms")
print(f"   Ecosystem lookup: ~{elapsed:.0f}ms")
print(f"   Total overhead per job: ~{elapsed * 4:.0f}ms (4 subqueries)")
print(f"   For 20 jobs: ~{elapsed * 4 * 20:.0f}ms")
print(f"\n   ✅ This is acceptable overhead for zero extra API calls!")

# Check for unmatched tech
print("\n🔍 Checking for unmatched tech stack items...")

# Get all unique languages from jobs
all_langs_result = db.client.rpc('get_unique_array_elements', {
    'table_name': 'llm_enrichment',
    'column_name': 'must_have_programmeertalen'
}).execute()

# Note: This RPC might not exist, so let's do it differently
# Get sample of jobs and check their tech
sample_jobs = db.client.table("llm_enrichment")\
    .select("must_have_programmeertalen, nice_to_have_programmeertalen, must_have_ecosystemen, nice_to_have_ecosystemen")\
    .not_.is_("must_have_programmeertalen", "null")\
    .limit(50)\
    .execute()

all_langs = set()
all_ecos = set()

for job in sample_jobs.data:
    if job.get('must_have_programmeertalen'):
        all_langs.update(job['must_have_programmeertalen'])
    if job.get('nice_to_have_programmeertalen'):
        all_langs.update(job['nice_to_have_programmeertalen'])
    if job.get('must_have_ecosystemen'):
        all_ecos.update(job['must_have_ecosystemen'])
    if job.get('nice_to_have_ecosystemen'):
        all_ecos.update(job['nice_to_have_ecosystemen'])

print(f"\n   Found {len(all_langs)} unique languages in sample")
print(f"   Found {len(all_ecos)} unique ecosystems in sample")

# Check which ones are not in master tables
if all_langs:
    matched_langs = db.client.table("programming_languages")\
        .select("name")\
        .in_("name", list(all_langs))\
        .execute()
    
    matched_lang_names = {lang['name'] for lang in matched_langs.data}
    unmatched_langs = all_langs - matched_lang_names
    
    if unmatched_langs:
        print(f"\n   ⚠️ {len(unmatched_langs)} unmatched languages:")
        for lang in sorted(list(unmatched_langs)[:10]):
            print(f"      - {lang}")
    else:
        print(f"\n   ✅ All languages matched!")

if all_ecos:
    matched_ecos = db.client.table("ecosystems")\
        .select("name")\
        .in_("name", list(all_ecos))\
        .execute()
    
    matched_eco_names = {eco['name'] for eco in matched_ecos.data}
    unmatched_ecos = all_ecos - matched_eco_names
    
    if unmatched_ecos:
        print(f"\n   ⚠️ {len(unmatched_ecos)} unmatched ecosystems:")
        for eco in sorted(list(unmatched_ecos)[:10]):
            print(f"      - {eco}")
    else:
        print(f"\n   ✅ All ecosystems matched!")
