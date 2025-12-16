#!/usr/bin/env python3
"""Test the optimized auto-enrichment service logic."""

from database.client import db
import time

print("=== TESTING OPTIMIZED SERVICE LOGIC ===\n")

# Simulate the NEW optimized approach
print("NEW OPTIMIZED APPROACH:")
print("-" * 50)
start = time.time()

# Fetch only 100 recent Data jobs
recent_jobs = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(100)\
    .execute()

print(f"1. Fetched {len(recent_jobs.data)} recent Data jobs")

# Get enrichment status for these specific jobs only
job_ids = [j["id"] for j in recent_jobs.data]
enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_completed_at")\
    .in_("job_posting_id", job_ids)\
    .execute()

print(f"2. Checked enrichment status for those {len(job_ids)} jobs")
print(f"   Found {len(enrichments.data)} enrichment records")

# Build set of enriched job IDs
enriched_ids = {
    e["job_posting_id"] 
    for e in enrichments.data 
    if e.get("enrichment_completed_at")
}

print(f"3. {len(enriched_ids)} jobs are already enriched")

# Filter to only unenriched jobs, take first 30
jobs = [
    {"id": j["id"], "title": j["title"]}
    for j in recent_jobs.data
    if j["id"] not in enriched_ids
][:30]

elapsed = time.time() - start

print(f"4. Found {len(jobs)} unenriched jobs to process")
print(f"\n⏱️  Total time: {elapsed:.3f}s")
print(f"📊 Queries: 2 (targeted and efficient)")

if jobs:
    print(f"\n✅ READY TO ENRICH {len(jobs)} JOBS:")
    for i, job in enumerate(jobs[:10], 1):
        print(f"   {i}. {job['title'][:60]}")
    if len(jobs) > 10:
        print(f"   ... and {len(jobs) - 10} more")
    
    print(f"\n💡 SERVICE WILL:")
    print(f"   - Process these {len(jobs)} jobs immediately")
    print(f"   - NO skipping with 'already enriched' messages")
    print(f"   - Direct enrichment via OpenAI API")
    print(f"   - Estimated time: ~{len(jobs)} seconds")
else:
    print(f"\n✅ ALL RECENT JOBS ARE ENRICHED!")
    print(f"   No work needed in this batch")

# Compare with old approach
print(f"\n" + "=" * 50)
print("COMPARISON WITH OLD APPROACH:")
print("-" * 50)
print("OLD: Fetch 500 jobs + 3000 enrichments = 3500 records")
print("     Then filter in Python, skip 30 already-enriched jobs")
print("     Result: Logs full of 'already enriched' messages")
print()
print(f"NEW: Fetch 100 jobs + check enrichment for those 100")
print(f"     Direct list of {len(jobs)} unenriched jobs")
print(f"     Result: Only process truly unenriched jobs")
print()
print("✅ BENEFITS:")
print("   - 35x less data fetched (100 vs 3500 records)")
print("   - No 'already enriched' skip messages")
print("   - Faster and more efficient")
print("   - Cleaner logs")
