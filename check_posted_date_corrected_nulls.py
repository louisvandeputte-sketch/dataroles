#!/usr/bin/env python3
"""Check why posted_date_corrected is NULL for many jobs."""

from database.client import db

print("=== POSTED_DATE_CORRECTED NULL ANALYSIS ===\n")

# Total jobs
total = db.client.table("job_postings")\
    .select("id", count="exact")\
    .execute()
print(f"Total jobs: {total.count}")

# Jobs with NULL posted_date_corrected
null_corrected = db.client.table("job_postings")\
    .select("id", count="exact")\
    .is_("posted_date_corrected", "null")\
    .execute()
print(f"Jobs with NULL posted_date_corrected: {null_corrected.count}")

# Jobs with non-NULL posted_date_corrected
non_null_corrected = db.client.table("job_postings")\
    .select("id", count="exact")\
    .not_.is_("posted_date_corrected", "null")\
    .execute()
print(f"Jobs with non-NULL posted_date_corrected: {non_null_corrected.count}")

print(f"\n=== BREAKDOWN ===")

# Check posted_date availability
null_posted_date = db.client.table("job_postings")\
    .select("id", count="exact")\
    .is_("posted_date", "null")\
    .execute()
print(f"Jobs with NULL posted_date: {null_posted_date.count}")

# Sample jobs with NULL posted_date_corrected
print(f"\n=== SAMPLE JOBS WITH NULL posted_date_corrected ===")
sample = db.client.table("job_postings")\
    .select("id, title, posted_date, posted_date_corrected")\
    .is_("posted_date_corrected", "null")\
    .limit(10)\
    .execute()

for job in sample.data:
    print(f"Job: {job['title'][:50]}")
    print(f"  posted_date: {job.get('posted_date')}")
    print(f"  posted_date_corrected: {job.get('posted_date_corrected')}")
    
    # Check if job has sources with first_seen_at
    sources = db.client.table("job_sources")\
        .select("first_seen_at")\
        .eq("job_posting_id", job['id'])\
        .execute()
    
    if sources.data:
        first_seen = sources.data[0].get('first_seen_at')
        print(f"  first_seen_at: {first_seen}")
    else:
        print(f"  first_seen_at: NO SOURCES RECORD")
    print()

print("=== ROOT CAUSE ===")
print("If posted_date is NULL and first_seen_at is NULL:")
print("  LEAST(NULL, NULL) = NULL")
print("\nIf posted_date is NULL but first_seen_at exists:")
print("  LEAST(first_seen_at, NULL) = NULL (LEAST returns NULL if any input is NULL)")
print("\nSOLUTION: Use COALESCE to handle NULL values")
print("  LEAST(COALESCE(first_seen_at, posted_date), COALESCE(posted_date, first_seen_at))")
