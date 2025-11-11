#!/usr/bin/env python3
"""Assign 'Data' job type to all Data-classified jobs without types."""

from database.client import db
from uuid import UUID

print("Assigning Data Type to All Data Jobs")
print("=" * 80)

# Get the "Data" job type
data_type = db.client.table("job_types")\
    .select("id, name")\
    .eq("name", "Data")\
    .single()\
    .execute()

if not data_type.data:
    print("❌ Data job type not found!")
    exit(1)

data_type_id = data_type.data['id']
print(f"\nData job type ID: {data_type_id}")

# Get all jobs with title_classification = 'Data'
data_jobs = db.client.table("job_postings")\
    .select("id, title, source")\
    .eq("title_classification", "Data")\
    .execute()

print(f"Found {len(data_jobs.data)} Data-classified jobs")

# Check which ones don't have the Data type assigned
jobs_without_type = []
for job in data_jobs.data:
    # Check if already has Data type
    existing = db.client.table("job_type_assignments")\
        .select("id")\
        .eq("job_posting_id", job['id'])\
        .eq("job_type_id", data_type_id)\
        .execute()
    
    if not existing.data:
        jobs_without_type.append(job)

print(f"Jobs without Data type: {len(jobs_without_type)}")

if len(jobs_without_type) == 0:
    print("✅ All Data jobs already have the Data type assigned!")
else:
    print(f"\nAssigning Data type to {len(jobs_without_type)} jobs...")
    
    assigned = 0
    failed = 0
    
    for i, job in enumerate(jobs_without_type, 1):
        try:
            db.client.table("job_type_assignments").insert({
                "job_posting_id": job['id'],
                "job_type_id": data_type_id
            }).execute()
            
            assigned += 1
            if i % 10 == 0:
                print(f"  [{i}/{len(jobs_without_type)}] Assigned...")
        except Exception as e:
            failed += 1
            print(f"  ❌ Failed for {job['title'][:40]}: {e}")
    
    print(f"\n" + "=" * 80)
    print(f"Results:")
    print(f"  Assigned: {assigned}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(jobs_without_type)}")
    print(f"\n✅ All Data jobs now have the Data type!")
