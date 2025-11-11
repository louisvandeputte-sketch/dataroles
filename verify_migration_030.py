#!/usr/bin/env python3
"""Verify migration 030 - Multi-source implementation."""

from database.client import db

print("Verifying Migration 030")
print("=" * 80)

# 1. Check job_sources table exists
print("\n1. Checking job_sources table...")
try:
    result = db.client.table("job_sources").select("*", count="exact").limit(1).execute()
    print(f"   ✅ Table exists with {result.count} entries")
except Exception as e:
    print(f"   ❌ Table not found: {e}")
    exit(1)

# 2. Check data migration
print("\n2. Checking data migration...")
total_jobs = db.client.table("job_postings").select("id", count="exact").execute()
total_sources = db.client.table("job_sources").select("id", count="exact").execute()

print(f"   Total jobs: {total_jobs.count}")
print(f"   Total sources: {total_sources.count}")

if total_sources.count >= total_jobs.count:
    print(f"   ✅ Data migrated (ratio: {total_sources.count / total_jobs.count:.2f})")
else:
    print(f"   ⚠️  Some jobs missing sources")

# 3. Check dedup_key column
print("\n3. Checking dedup_key column...")
sample = db.client.table("job_postings")\
    .select("id, title, dedup_key")\
    .not_.is_("dedup_key", "null")\
    .limit(5)\
    .execute()

if sample.data:
    print(f"   ✅ dedup_key populated for {len(sample.data)} sample jobs")
    for job in sample.data[:3]:
        print(f"      {job['title'][:40]:40} → {job['dedup_key'][:50]}")
else:
    print(f"   ❌ dedup_key not populated")

# 4. Check for potential duplicates
print("\n4. Checking for duplicate dedup_keys...")
duplicates = db.client.rpc('check_duplicate_dedup_keys').execute()

# Alternative query if RPC doesn't exist
try:
    # Get all dedup_keys
    all_keys = db.client.table("job_postings")\
        .select("dedup_key")\
        .not_.is_("dedup_key", "null")\
        .execute()
    
    from collections import Counter
    key_counts = Counter([j['dedup_key'] for j in all_keys.data])
    duplicates = {k: v for k, v in key_counts.items() if v > 1}
    
    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} duplicate dedup_keys:")
        for key, count in list(duplicates.items())[:5]:
            print(f"      {key[:60]:60} → {count} jobs")
        print(f"\n   Note: Unique index creation will fail. Need to resolve duplicates first.")
    else:
        print(f"   ✅ No duplicates found")
except Exception as e:
    print(f"   ⚠️  Could not check duplicates: {e}")

# 5. Sample multi-source job (if any)
print("\n5. Looking for multi-source jobs...")
multi_source = db.client.rpc('find_multi_source_jobs').execute()

# Alternative: Check manually
try:
    # Get jobs with multiple sources
    all_sources = db.client.table("job_sources")\
        .select("job_posting_id")\
        .execute()
    
    from collections import Counter
    job_counts = Counter([s['job_posting_id'] for s in all_sources.data])
    multi = {k: v for k, v in job_counts.items() if v > 1}
    
    if multi:
        print(f"   ✅ Found {len(multi)} jobs with multiple sources")
        # Show example
        example_id = list(multi.keys())[0]
        job = db.client.table("job_postings")\
            .select("title, companies(name)")\
            .eq("id", example_id)\
            .single()\
            .execute()
        
        sources = db.client.table("job_sources")\
            .select("source")\
            .eq("job_posting_id", example_id)\
            .execute()
        
        source_list = [s['source'] for s in sources.data]
        company = job.data.get('companies', {}).get('name', 'N/A')
        print(f"      Example: {job.data['title']} at {company}")
        print(f"      Sources: {', '.join(source_list)}")
    else:
        print(f"   ℹ️  No multi-source jobs yet (expected)")
except Exception as e:
    print(f"   ⚠️  Could not check: {e}")

print("\n" + "=" * 80)
print("Migration verification complete!")
print("\nNext steps:")
print("  1. If duplicates found: Resolve them before creating unique index")
print("  2. If no duplicates: Migration successful, ready for code changes")
print("  3. Test by scraping same job from LinkedIn and Indeed")
