#!/usr/bin/env python3
"""Check how many jobs are waiting for auto-enrichment."""

from database.client import db
from datetime import datetime, timedelta

print("=== AUTO-ENRICHMENT QUEUE STATUS ===\n")

# Get all Data jobs with title classification
all_data_jobs = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .execute()

print(f"Total active Data jobs: {all_data_jobs.count}")

# Get enriched jobs (completed)
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id, job_postings!inner(title_classification, is_active)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .eq("job_postings.is_active", True)\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"Enriched active Data jobs: {enriched.count}")

# Calculate pending
pending = all_data_jobs.count - enriched.count
print(f"Pending enrichment: {pending}")

# Get sample of pending jobs (most recent)
print(f"\n=== PENDING JOBS (most recent 10) ===")

# Get all active Data job IDs
all_ids_result = db.client.table("job_postings")\
    .select("id, title, posted_date_corrected")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date_corrected", desc=True)\
    .limit(200)\
    .execute()

# Get enriched IDs
enriched_ids = {e["job_posting_id"] for e in enriched.data}

# Find pending
pending_jobs = []
for job in all_ids_result.data:
    if job["id"] not in enriched_ids:
        pending_jobs.append(job)
        if len(pending_jobs) >= 10:
            break

for i, job in enumerate(pending_jobs, 1):
    posted = job.get("posted_date_corrected")
    if posted:
        # Calculate age
        posted_dt = datetime.fromisoformat(posted.replace('Z', '+00:00'))
        age = datetime.now(posted_dt.tzinfo) - posted_dt
        hours = age.total_seconds() / 3600
        age_str = f"{hours:.1f} hours ago"
    else:
        age_str = "unknown age"
    
    print(f"{i}. {job['title'][:60]} - {age_str}")

print(f"\n=== AUTO-ENRICHMENT SERVICE STATUS ===")
print("The auto-enrichment service processes 20 jobs every 60 seconds.")
print(f"With {pending} pending jobs, estimated time: {(pending / 20) * 60 / 60:.1f} hours")
print("\nTo manually enrich a specific job, use:")
print("  curl -X POST http://localhost:8000/api/jobs/{job_id}/enrich")
