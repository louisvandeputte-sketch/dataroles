#!/usr/bin/env python3
"""Check for dedup_key issues."""

from database.client import db
from collections import Counter

print("Checking dedup_key Issues")
print("=" * 80)

# 1. Check for NULL dedup_keys
print("\n1. Checking for NULL dedup_keys...")
null_keys = db.client.table("job_postings")\
    .select("id, title, company_id")\
    .is_("dedup_key", "null")\
    .execute()

print(f"   Jobs with NULL dedup_key: {len(null_keys.data)}")
if null_keys.data:
    print(f"   First 5 examples:")
    for job in null_keys.data[:5]:
        print(f"      {job['id']} - {job['title'][:50]} (company_id: {job.get('company_id')})")

# 2. Check for empty dedup_keys
print("\n2. Checking for empty dedup_keys...")
empty_keys = db.client.table("job_postings")\
    .select("id, title, dedup_key")\
    .eq("dedup_key", "")\
    .execute()

print(f"   Jobs with empty dedup_key: {len(empty_keys.data)}")

# 3. Get ALL dedup_keys and check for duplicates
print("\n3. Checking ALL jobs for duplicates...")
all_jobs = db.client.table("job_postings")\
    .select("id, title, dedup_key, created_at")\
    .execute()

print(f"   Total jobs: {len(all_jobs.data)}")

# Count dedup_keys
key_counts = Counter([j['dedup_key'] for j in all_jobs.data if j.get('dedup_key')])
duplicates = {k: v for k, v in key_counts.items() if v > 1}

print(f"   Unique dedup_keys: {len(key_counts)}")
print(f"   Duplicate dedup_keys: {len(duplicates)}")

if duplicates:
    print(f"\n   Top 10 duplicates:")
    for key, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      {key[:70]:70} → {count} jobs")
    
    # Show details of first duplicate
    first_dup_key = list(duplicates.keys())[0]
    print(f"\n   Details of '{first_dup_key}':")
    dup_jobs = [j for j in all_jobs.data if j.get('dedup_key') == first_dup_key]
    for job in dup_jobs:
        print(f"      ID: {job['id']}")
        print(f"      Title: {job['title']}")
        print(f"      Created: {job['created_at']}")
        print()

# 4. Check specific problematic key
print("\n4. Checking specific key: 'full stack developer|dxc technology'")
specific = db.client.table("job_postings")\
    .select("id, title, created_at, source")\
    .eq("dedup_key", "full stack developer|dxc technology")\
    .execute()

print(f"   Found {len(specific.data)} jobs with this key:")
for job in specific.data:
    print(f"      {job['id']} - {job['title']} ({job['source']}, created {job['created_at'][:10]})")

print("\n" + "=" * 80)
