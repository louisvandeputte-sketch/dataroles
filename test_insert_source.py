#!/usr/bin/env python3
"""Test inserting a single job_sources entry."""

from database.client import db

print("Testing job_sources insert")
print("=" * 80)

# Get one job without sources
all_jobs = db.client.table("job_postings")\
    .select("id, source, linkedin_job_id, indeed_job_id, created_at")\
    .limit(1)\
    .execute()

job = all_jobs.data[0]

print(f"\nJob ID: {job['id']}")
print(f"Source: {job['source']}")
print(f"LinkedIn ID: {job.get('linkedin_job_id')}")
print(f"Indeed ID: {job.get('indeed_job_id')}")

# Try to insert
source_job_id = job.get('linkedin_job_id') if job['source'] == 'linkedin' else job.get('indeed_job_id')

print(f"\nAttempting to insert:")
print(f"  job_posting_id: {job['id']}")
print(f"  source: {job['source']}")
print(f"  source_job_id: {source_job_id}")

try:
    result = db.client.table("job_sources").insert({
        "job_posting_id": job['id'],
        "source": job['source'],
        "source_job_id": source_job_id,
        "first_seen_at": job['created_at'],
        "last_seen_at": job['created_at']
    }).execute()
    
    print(f"\n✅ Success!")
    print(f"Result: {result.data}")
except Exception as e:
    print(f"\n❌ Failed!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
