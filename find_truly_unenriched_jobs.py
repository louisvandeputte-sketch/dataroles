#!/usr/bin/env python3
"""Find jobs that are truly not enriched (no enrichment record OR incomplete)."""

from database.client import db

print("=== FINDING TRULY UNENRICHED JOBS ===\n")

# Get all active Data jobs
all_data = db.client.table("job_postings")\
    .select("id, title", count="exact")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .execute()

print(f"Total active Data jobs: {all_data.count}")

# Get jobs WITH enrichment records (completed)
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

enriched_ids = {e["job_posting_id"] for e in enriched.data}
print(f"Jobs with completed enrichment: {len(enriched_ids)}")

# Find jobs WITHOUT any enrichment record OR with incomplete enrichment
unenriched_jobs = []
for job in all_data.data:
    if job["id"] not in enriched_ids:
        unenriched_jobs.append(job)

print(f"Jobs WITHOUT completed enrichment: {len(unenriched_jobs)}")

# Check if these have enrichment records at all
print(f"\n=== CHECKING ENRICHMENT RECORDS ===")
no_record = 0
has_record_incomplete = 0

for job in unenriched_jobs[:20]:  # Check first 20
    enrichment = db.client.table("llm_enrichment")\
        .select("enrichment_completed_at, enrichment_error")\
        .eq("job_posting_id", job["id"])\
        .maybe_single()\
        .execute()
    
    if not enrichment.data:
        no_record += 1
        print(f"NO RECORD: {job['title'][:60]}")
    else:
        has_record_incomplete += 1
        error = enrichment.data.get("enrichment_error")
        print(f"INCOMPLETE: {job['title'][:60]}")
        if error:
            print(f"  Error: {error[:100]}")

print(f"\n=== SUMMARY ===")
print(f"Total unenriched: {len(unenriched_jobs)}")
print(f"  - No enrichment record: {no_record}")
print(f"  - Has record but incomplete: {has_record_incomplete}")

# Check why the service is skipping these
print(f"\n=== WHY ARE THESE BEING SKIPPED? ===")

# The service query
print("Service query:")
print("1. Get all Data jobs (limit 500, sorted by posted_date DESC)")
print("2. Get all enriched IDs (WHERE completed_at IS NOT NULL)")
print("3. Filter to jobs NOT in enriched_ids")
print("4. Take first 30")

# Simulate the service query
service_query = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(500)\
    .execute()

print(f"\nService would fetch: {len(service_query.data)} jobs")

# Filter to unenriched
service_unenriched = []
for job in service_query.data:
    if job["id"] not in enriched_ids:
        service_unenriched.append(job)
        if len(service_unenriched) >= 30:
            break

print(f"Service would find: {len(service_unenriched)} unenriched jobs")

if service_unenriched:
    print(f"\nFirst 10 jobs service would try to enrich:")
    for i, job in enumerate(service_unenriched[:10], 1):
        print(f"{i}. {job['title'][:60]}")
        
        # Check enrichment status
        enrichment = db.client.table("llm_enrichment")\
            .select("enrichment_completed_at, enrichment_error, type_datarol")\
            .eq("job_posting_id", job["id"])\
            .maybe_single()\
            .execute()
        
        if enrichment.data:
            e = enrichment.data
            print(f"   completed_at: {e.get('enrichment_completed_at')}")
            print(f"   type_datarol: {e.get('type_datarol')}")
            print(f"   error: {e.get('enrichment_error')}")
        else:
            print(f"   NO ENRICHMENT RECORD")
else:
    print("\n✅ Service found NO unenriched jobs!")
    print("This means ALL active Data jobs are enriched.")
