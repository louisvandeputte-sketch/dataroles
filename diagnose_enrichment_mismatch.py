#!/usr/bin/env python3
"""Diagnose why jobs with completed enrichments are not in the enriched_ids set."""

from database.client import db

print("=== DIAGNOSING ENRICHMENT MISMATCH ===\n")

# Get the enriched IDs set (like the service does)
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .limit(3000)\
    .execute()

enriched_ids = {e["job_posting_id"] for e in enriched.data}
print(f"Enriched IDs set size: {len(enriched_ids)}")

# Check a specific job that's being skipped
job_id = "c0018464-49ab-4bb7-ad33-dd8a83810c8f"  # Anaplan Model Builder
job_title = "Anaplan Model Builder"

print(f"\n=== CHECKING: {job_title} ===")
print(f"Job ID: {job_id}")

# Is it in enriched_ids?
in_set = job_id in enriched_ids
print(f"In enriched_ids set: {in_set}")

# Get its enrichment record directly
enrichment = db.client.table("llm_enrichment")\
    .select("*")\
    .eq("job_posting_id", job_id)\
    .maybe_single()\
    .execute()

if enrichment.data:
    e = enrichment.data
    print(f"\nEnrichment record:")
    print(f"  ID: {e.get('id')}")
    print(f"  completed_at: {e.get('enrichment_completed_at')}")
    print(f"  type_datarol: {e.get('type_datarol')}")
    print(f"  error: {e.get('enrichment_error')}")
    
    # Check if it should be in the query
    has_completed = e.get('enrichment_completed_at') is not None
    print(f"\n  Should be in query (has completed_at): {has_completed}")
    
    if has_completed and not in_set:
        print(f"\n  🚨 MISMATCH DETECTED!")
        print(f"  Job has completed_at but is NOT in enriched_ids set")
else:
    print("\n❌ No enrichment record found")

# Now check ALL jobs in the first 30 that service tries to process
print(f"\n=== CHECKING ALL 30 JOBS SERVICE TRIES TO PROCESS ===\n")

all_data_jobs = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(500)\
    .execute()

# Filter to unenriched (like service does)
unenriched = []
for job in all_data_jobs.data:
    if job["id"] not in enriched_ids:
        unenriched.append(job)
        if len(unenriched) >= 30:
            break

print(f"Found {len(unenriched)} 'unenriched' jobs in batch")

# Check each one
truly_unenriched = 0
falsely_unenriched = 0

for i, job in enumerate(unenriched[:10], 1):
    enrichment = db.client.table("llm_enrichment")\
        .select("enrichment_completed_at, type_datarol")\
        .eq("job_posting_id", job["id"])\
        .maybe_single()\
        .execute()
    
    if enrichment.data:
        completed = enrichment.data.get("enrichment_completed_at")
        if completed:
            falsely_unenriched += 1
            print(f"{i}. ❌ {job['title'][:50]} - HAS completed_at but NOT in set!")
        else:
            truly_unenriched += 1
            print(f"{i}. ⚠️  {job['title'][:50]} - Has record but no completed_at")
    else:
        truly_unenriched += 1
        print(f"{i}. ✅ {job['title'][:50]} - No enrichment record")

print(f"\n=== SUMMARY ===")
print(f"Truly unenriched: {truly_unenriched}")
print(f"Falsely marked as unenriched: {falsely_unenriched}")

if falsely_unenriched > 0:
    print(f"\n🚨 ROOT CAUSE:")
    print(f"Jobs with completed enrichments are NOT in the enriched_ids set!")
    print(f"This means the query is not returning all enriched jobs.")
    
    # Check total count
    print(f"\n=== CHECKING TOTAL ENRICHED COUNT ===")
    
    # Count with filter
    total_enriched = db.client.table("llm_enrichment")\
        .select("job_posting_id", count="exact")\
        .not_.is_("enrichment_completed_at", "null")\
        .execute()
    
    print(f"Total enriched jobs (with completed_at): {total_enriched.count}")
    print(f"Fetched in query: {len(enriched_ids)}")
    print(f"Missing: {total_enriched.count - len(enriched_ids)}")
    
    if total_enriched.count > len(enriched_ids):
        print(f"\n💡 SOLUTION:")
        print(f"Increase query limit from {len(enriched_ids)} to {total_enriched.count + 500}")
