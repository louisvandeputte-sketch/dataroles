#!/usr/bin/env python3
"""Backfill job_sources for jobs that don't have entries yet."""

from database.client import db

print("Backfilling job_sources")
print("=" * 80)

# 1. Find jobs without job_sources entries
print("\n1. Finding jobs without job_sources...")

# Get ALL job IDs (with pagination)
all_jobs_data = []
offset = 0
batch_size = 1000

while True:
    batch = db.client.table("job_postings")\
        .select("id, source, linkedin_job_id, indeed_job_id, created_at")\
        .range(offset, offset + batch_size - 1)\
        .execute()
    
    if not batch.data:
        break
    
    all_jobs_data.extend(batch.data)
    offset += batch_size
    
    if len(batch.data) < batch_size:
        break

print(f"   Total jobs: {len(all_jobs_data)}")

# Get ALL job IDs that have sources (with pagination)
jobs_with_sources_data = []
offset = 0

while True:
    batch = db.client.table("job_sources")\
        .select("job_posting_id")\
        .range(offset, offset + batch_size - 1)\
        .execute()
    
    if not batch.data:
        break
    
    jobs_with_sources_data.extend(batch.data)
    offset += batch_size
    
    if len(batch.data) < batch_size:
        break

job_ids_with_sources = set([s['job_posting_id'] for s in jobs_with_sources_data])

# Find jobs without sources
jobs_without_sources = [
    job for job in all_jobs_data 
    if job['id'] not in job_ids_with_sources
]

print(f"   Jobs without job_sources: {len(jobs_without_sources)}")

if len(jobs_without_sources) == 0:
    print("\n✅ All jobs have job_sources entries!")
    exit(0)

# 2. Show examples
print(f"\n2. Examples of jobs without sources:")
for job in jobs_without_sources[:5]:
    source_id = job.get('linkedin_job_id') or job.get('indeed_job_id') or 'NONE'
    print(f"   {job['id'][:20]} | source: {job['source']:8} | source_id: {source_id[:20]}")

# 3. Backfill
proceed = input(f"\nBackfill {len(jobs_without_sources)} jobs? (yes/no): ")
if proceed.lower() != 'yes':
    print("Aborted.")
    exit(0)

print(f"\n3. Backfilling...")

success = 0
failed = 0
skipped = 0

for i, job in enumerate(jobs_without_sources, 1):
    source = job['source']
    
    # Get source_job_id
    if source == 'linkedin':
        source_job_id = job.get('linkedin_job_id')
    elif source == 'indeed':
        source_job_id = job.get('indeed_job_id')
    else:
        print(f"   [{i}/{len(jobs_without_sources)}] ⚠️  Unknown source: {source}")
        skipped += 1
        continue
    
    if not source_job_id:
        print(f"   [{i}/{len(jobs_without_sources)}] ⚠️  No source_job_id for {job['id']}")
        skipped += 1
        continue
    
    # Insert job_sources entry
    try:
        db.client.table("job_sources").insert({
            "job_posting_id": job['id'],
            "source": source,
            "source_job_id": source_job_id,
            "first_seen_at": job['created_at'],
            "last_seen_at": job['created_at']
        }).execute()
        
        success += 1
        if i % 100 == 0:
            print(f"   [{i}/{len(jobs_without_sources)}] Backfilled...")
    except Exception as e:
        failed += 1
        error_msg = str(e)
        if i <= 3 or "duplicate" not in error_msg.lower():
            print(f"   [{i}/{len(jobs_without_sources)}] ❌ Failed: {error_msg[:100]}")

print(f"\n" + "=" * 80)
print(f"Results:")
print(f"  Success: {success}")
print(f"  Failed: {failed}")
print(f"  Skipped: {skipped}")
print(f"  Total: {len(jobs_without_sources)}")

# 4. Verify
print(f"\n4. Verifying...")
remaining = db.client.table("job_postings")\
    .select("id")\
    .execute()

remaining_with_sources = db.client.table("job_sources")\
    .select("job_posting_id")\
    .execute()

remaining_ids = set([s['job_posting_id'] for s in remaining_with_sources.data])
still_missing = len(remaining.data) - len(remaining_ids)

if still_missing == 0:
    print(f"   ✅ All jobs now have job_sources entries!")
else:
    print(f"   ⚠️  Still {still_missing} jobs without sources")

print("\n✅ Backfill complete!")
