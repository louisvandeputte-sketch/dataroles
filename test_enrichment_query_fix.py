#!/usr/bin/env python3
"""Test the enrichment query fix to verify it now fetches all enriched jobs."""

from database.client import db

print("=== TESTING ENRICHMENT QUERY FIX ===\n")

# Test OLD query (without limit)
print("1. OLD query (no explicit limit - Supabase default 1000):")
enriched_old = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"   Fetched: {len(enriched_old.data)} enriched jobs")

# Test NEW query (with limit 3000)
print("\n2. NEW query (explicit limit 3000):")
enriched_new = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .limit(3000)\
    .execute()

print(f"   Fetched: {len(enriched_new.data)} enriched jobs")

# Show difference
difference = len(enriched_new.data) - len(enriched_old.data)
print(f"\n3. Difference: {difference} additional enriched jobs fetched")

if difference > 0:
    print(f"   ✅ FIX WORKS: {difference} jobs were missing from the old query!")
    print(f"   These jobs were incorrectly marked as 'unenriched'")
else:
    print(f"   ⚠️  No difference - all enriched jobs fit in 1000 limit")

# Now test the actual service logic
print("\n=== SIMULATING SERVICE LOGIC ===\n")

# Get all Data jobs
all_data_jobs = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(500)\
    .execute()

print(f"Total Data jobs in query: {len(all_data_jobs.data)}")

# OLD logic
enriched_ids_old = {e["job_posting_id"] for e in enriched_old.data}
unenriched_old = [j for j in all_data_jobs.data if j["id"] not in enriched_ids_old]
print(f"\nOLD logic: {len(unenriched_old)} unenriched jobs found")

# NEW logic
enriched_ids_new = {e["job_posting_id"] for e in enriched_new.data}
unenriched_new = [j for j in all_data_jobs.data if j["id"] not in enriched_ids_new]
print(f"NEW logic: {len(unenriched_new)} unenriched jobs found")

# Show impact
impact = len(unenriched_old) - len(unenriched_new)
print(f"\nImpact: {impact} fewer jobs incorrectly marked as unenriched")

if impact > 0:
    print(f"\n✅ FIX CONFIRMED!")
    print(f"   {impact} jobs will now be correctly skipped (already enriched)")
    print(f"   Service will focus on truly unenriched jobs")
    
    # Show examples of jobs that were incorrectly marked
    incorrectly_marked = [j for j in unenriched_old if j["id"] not in [u["id"] for u in unenriched_new]]
    if incorrectly_marked:
        print(f"\n   Examples of jobs that were incorrectly marked as unenriched:")
        for i, job in enumerate(incorrectly_marked[:5], 1):
            print(f"   {i}. {job['title'][:60]}")

# Check if there are truly unenriched jobs now
if unenriched_new:
    print(f"\n=== TRULY UNENRICHED JOBS (first 10) ===")
    for i, job in enumerate(unenriched_new[:10], 1):
        print(f"{i}. {job['title'][:60]}")
        
        # Verify they're truly unenriched
        enrichment = db.client.table("llm_enrichment")\
            .select("enrichment_completed_at, type_datarol")\
            .eq("job_posting_id", job["id"])\
            .maybe_single()\
            .execute()
        
        if enrichment.data:
            print(f"   ⚠️  Has enrichment record: completed_at={enrichment.data.get('enrichment_completed_at')}, type={enrichment.data.get('type_datarol')}")
        else:
            print(f"   ✅ No enrichment record (truly unenriched)")
else:
    print(f"\n✅ NO UNENRICHED JOBS!")
    print("   All active Data jobs are enriched.")
