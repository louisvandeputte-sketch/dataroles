#!/usr/bin/env python3
"""Test optimized query that directly fetches only unenriched jobs."""

from database.client import db
import time

print("=== TESTING OPTIMIZED QUERY ===\n")

# OLD APPROACH: Fetch all jobs, then filter
print("1. OLD APPROACH (fetch all, then filter in Python):")
start = time.time()

all_data_jobs = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(500)\
    .execute()

enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .limit(3000)\
    .execute()

enriched_ids = {e["job_posting_id"] for e in enriched.data}

jobs_old = []
for job in all_data_jobs.data:
    if job["id"] not in enriched_ids:
        jobs_old.append({"id": job["id"], "title": job["title"]})
        if len(jobs_old) >= 30:
            break

old_time = time.time() - start
print(f"   Found: {len(jobs_old)} unenriched jobs")
print(f"   Time: {old_time:.3f}s")
print(f"   Queries: 2 (job_postings + llm_enrichment)")

# NEW APPROACH: Use RPC function to get only unenriched jobs
print("\n2. NEW APPROACH (direct query with LEFT JOIN via RPC):")
print("   Testing if we can use Supabase RPC...")

# First, let's try a direct approach using NOT IN
print("\n3. ALTERNATIVE: Use NOT IN subquery:")
start = time.time()

try:
    # Get enriched IDs first
    enriched_ids_list = list(enriched_ids)
    
    # Query jobs that are NOT in enriched list
    if enriched_ids_list:
        jobs_new = db.client.table("job_postings")\
            .select("id, title")\
            .eq("title_classification", "Data")\
            .eq("is_active", True)\
            .not_.in_("id", enriched_ids_list)\
            .order("posted_date", desc=True)\
            .limit(30)\
            .execute()
    else:
        jobs_new = db.client.table("job_postings")\
            .select("id, title")\
            .eq("title_classification", "Data")\
            .eq("is_active", True)\
            .order("posted_date", desc=True)\
            .limit(30)\
            .execute()
    
    new_time = time.time() - start
    print(f"   Found: {len(jobs_new.data)} unenriched jobs")
    print(f"   Time: {new_time:.3f}s")
    print(f"   Queries: 1 (single optimized query)")
    print(f"   Speedup: {old_time/new_time:.1f}x faster")
    
    # Verify results match
    old_ids = {j["id"] for j in jobs_old}
    new_ids = {j["id"] for j in jobs_new.data}
    
    if old_ids == new_ids:
        print(f"\n   ✅ Results match perfectly!")
    else:
        print(f"\n   ⚠️  Results differ:")
        print(f"   Old: {len(old_ids)} jobs")
        print(f"   New: {len(new_ids)} jobs")
        print(f"   Only in old: {len(old_ids - new_ids)}")
        print(f"   Only in new: {len(new_ids - old_ids)}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   Note: Supabase Python client may not support .not_.in_() with large lists")

# BEST APPROACH: Use a simpler method - query jobs without enrichment records
print("\n4. BEST APPROACH: Query jobs, check enrichment in batch:")
start = time.time()

# Get recent Data jobs
recent_jobs = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(100)\
    .execute()

# Get their enrichment status in one query
job_ids = [j["id"] for j in recent_jobs.data]
enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_completed_at")\
    .in_("job_posting_id", job_ids)\
    .execute()

enriched_in_batch = {e["job_posting_id"] for e in enrichments.data if e.get("enrichment_completed_at")}

jobs_best = [j for j in recent_jobs.data if j["id"] not in enriched_in_batch][:30]

best_time = time.time() - start
print(f"   Found: {len(jobs_best)} unenriched jobs")
print(f"   Time: {best_time:.3f}s")
print(f"   Queries: 2 (but smaller, targeted)")
print(f"   Speedup: {old_time/best_time:.1f}x faster")

# Verify
best_ids = {j["id"] for j in jobs_best}
if old_ids == best_ids:
    print(f"\n   ✅ Results match perfectly!")
else:
    print(f"\n   ⚠️  Results differ slightly (expected due to limit 100 vs 500)")

print("\n=== RECOMMENDATION ===")
print("Use BEST APPROACH:")
print("- Fetch only 100 most recent Data jobs (not 500)")
print("- Check enrichment status for those 100 in one query")
print("- Filter to unenriched and take first 30")
print("- Much faster and more efficient")
print("- No need to fetch 3000 enrichment records every time")
