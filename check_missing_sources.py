#!/usr/bin/env python3
"""Check jobs with missing source display."""

from database.client import db

print("Jobs with Missing Source Display")
print("=" * 80)

# Get jobs without visible source
jobs = db.client.table("job_postings")\
    .select("id, title, source, companies(name), job_sources(source)")\
    .limit(10)\
    .order("posted_date", desc=True)\
    .execute()

print(f"\n📊 Checking first 10 recent jobs:\n")

for i, job in enumerate(jobs.data, 1):
    title = job['title'][:50]
    company = job.get('companies', {}).get('name', 'N/A')[:30]
    old_source = job.get('source', 'NULL')
    job_sources = job.get('job_sources', [])
    
    print(f"{i}. {title}")
    print(f"   Company: {company}")
    print(f"   OLD source field: '{old_source}'")
    print(f"   NEW job_sources: {[s['source'] for s in job_sources]}")
    
    if not job_sources:
        print(f"   ⚠️  PROBLEM: No entries in job_sources table!")
    elif not old_source or old_source == 'NULL':
        print(f"   ⚠️  PROBLEM: Old source field is NULL/empty!")
    print()

# Check how many jobs have this issue
print("=" * 80)
print("\n📈 Statistics:")

# Jobs with NULL source field
null_source = db.client.table("job_postings")\
    .select("id", count="exact")\
    .is_("source", "null")\
    .execute()

print(f"  Jobs with NULL source field: {null_source.count}")

# Jobs without job_sources entries
all_jobs = db.client.table("job_postings")\
    .select("id")\
    .execute()

jobs_with_sources = db.client.table("job_sources")\
    .select("job_posting_id")\
    .execute()

job_ids_with_sources = set([s['job_posting_id'] for s in jobs_with_sources.data])
jobs_without_sources = [j for j in all_jobs.data if j['id'] not in job_ids_with_sources]

print(f"  Jobs without job_sources entries: {len(jobs_without_sources)}")

print("\n💡 Solution:")
print("  1. Backfill job_sources for jobs missing entries")
print("  2. Ensure old 'source' field is populated (for backward compatibility)")
