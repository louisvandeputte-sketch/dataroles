#!/usr/bin/env python3
"""Check which jobs are not enriched and why."""

from database.client import db
from loguru import logger

# Get total Data jobs
total_data = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .execute()

print(f"Total Data jobs: {total_data.count}")

# Get active Data jobs
active_data = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .execute()

print(f"Active Data jobs: {active_data.count}")

# Get enriched jobs
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id, job_postings!inner(title_classification, is_active)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"Enriched Data jobs: {enriched.count}")

# Get enriched ACTIVE jobs
enriched_active = db.client.table("llm_enrichment")\
    .select("job_posting_id, job_postings!inner(title_classification, is_active)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .eq("job_postings.is_active", True)\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"Enriched ACTIVE Data jobs: {enriched_active.count}")

# Calculate unenriched
unenriched_total = total_data.count - enriched.count
unenriched_active = active_data.count - enriched_active.count

print(f"\nUnenriched Data jobs (total): {unenriched_total}")
print(f"Unenriched ACTIVE Data jobs: {unenriched_active}")

# Get sample of unenriched active jobs
print("\n--- Sample of unenriched ACTIVE jobs ---")

# Get all active Data job IDs
all_active = db.client.table("job_postings")\
    .select("id, title, posted_date_corrected")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date_corrected", desc=True)\
    .limit(1000)\
    .execute()

# Get enriched job IDs
enriched_ids = {e["job_posting_id"] for e in enriched_active.data}

# Find unenriched
unenriched_jobs = []
for job in all_active.data:
    if job["id"] not in enriched_ids:
        unenriched_jobs.append(job)

print(f"Found {len(unenriched_jobs)} unenriched active jobs")

# Show first 20
for i, job in enumerate(unenriched_jobs[:20], 1):
    print(f"{i}. {job['title'][:60]} - Posted: {job.get('posted_date_corrected', 'N/A')}")

# Check if they have enrichment records at all
if unenriched_jobs:
    sample_ids = [j["id"] for j in unenriched_jobs[:20]]
    enrichment_records = db.client.table("llm_enrichment")\
        .select("job_posting_id, enrichment_error, enrichment_completed_at")\
        .in_("job_posting_id", sample_ids)\
        .execute()
    
    print(f"\n--- Enrichment records for sample ---")
    print(f"Found {len(enrichment_records.data)} enrichment records for {len(sample_ids)} jobs")
    
    for rec in enrichment_records.data:
        print(f"Job {rec['job_posting_id']}: completed={rec.get('enrichment_completed_at')}, error={rec.get('enrichment_error')}")
