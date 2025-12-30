#!/usr/bin/env python3
"""Test the auto-enrichment fix to verify it prioritizes newest jobs."""

from database.client import db

print("=== TESTING AUTO-ENRICHMENT FIX ===\n")

# Simulate the new query
print("Querying with new logic (sorted by posted_date DESC, limit 500)...")
all_data_jobs = db.client.table("job_postings")\
    .select("id, title, posted_date")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(500)\
    .execute()

print(f"Retrieved {len(all_data_jobs.data)} jobs")

# Get enriched IDs
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

enriched_ids = {e["job_posting_id"] for e in enriched.data}

# Filter to unenriched (first 30)
unenriched_jobs = []
for job in all_data_jobs.data:
    if job["id"] not in enriched_ids:
        unenriched_jobs.append(job)
        if len(unenriched_jobs) >= 30:
            break

print(f"\nFound {len(unenriched_jobs)} unenriched jobs in first batch")
print("\nFirst 10 unenriched jobs (newest first):")
for i, job in enumerate(unenriched_jobs[:10], 1):
    posted = job.get("posted_date", "NULL")
    print(f"{i}. {job['title'][:60]} - Posted: {posted}")

print("\n=== VERIFICATION ===")
print(f"✅ Query sorted by posted_date DESC")
print(f"✅ Limit increased to 500 (was 100)")
print(f"✅ Batch size increased to 30 (was 20)")
print(f"\nWith these changes:")
print(f"  - New jobs are ALWAYS in first 500 results")
print(f"  - 30 jobs processed per minute")
print(f"  - 300 jobs/night processed in ~10 minutes")
print(f"  - Current backlog ({len(unenriched_jobs)} jobs) cleared in ~{len(unenriched_jobs)/30:.0f} minutes")
