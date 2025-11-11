#!/usr/bin/env python3
"""Check Title Check and Search Type columns."""

from database.client import db

print("Checking Job Columns")
print("=" * 80)

# Get sample jobs
result = db.client.table("job_postings")\
    .select("id, title, title_classification, companies(name)")\
    .limit(10)\
    .execute()

print("\n1. Title Classification (Title Check):")
print("-" * 80)
for job in result.data:
    classification = job.get('title_classification') or 'NULL'
    company = job.get('companies', {}).get('name', 'N/A') if job.get('companies') else 'N/A'
    print(f"   {job['title'][:50]:50} | {classification:10} | {company[:30]}")

# Check distribution
print("\n2. Title Classification Distribution:")
stats = db.client.table("job_postings")\
    .select("title_classification", count="exact")\
    .execute()

# Count by classification
from collections import Counter
classifications = [j.get('title_classification') for j in stats.data]
counts = Counter(classifications)
print(f"   Total jobs: {len(classifications)}")
for classification, count in counts.most_common():
    classification_name = classification or 'NULL'
    percentage = (count / len(classifications) * 100) if len(classifications) > 0 else 0
    print(f"   {classification_name:15} : {count:5} ({percentage:.1f}%)")

# Check job types (Search Type)
print("\n3. Job Type Assignments (Search Type):")
print("-" * 80)

# Get jobs with their types
jobs_with_types = db.client.table("job_postings")\
    .select("id, title")\
    .limit(10)\
    .execute()

for job in jobs_with_types.data:
    # Get types for this job
    types = db.client.table("job_type_assignments")\
        .select("job_types(name)")\
        .eq("job_posting_id", job['id'])\
        .execute()
    
    type_names = [t['job_types']['name'] for t in types.data if t.get('job_types')]
    type_str = ', '.join(type_names) if type_names else 'NONE'
    print(f"   {job['title'][:50]:50} | {type_str}")

# Check distribution of job type assignments
print("\n4. Job Type Assignment Statistics:")
all_assignments = db.client.table("job_type_assignments")\
    .select("*", count="exact")\
    .execute()

all_jobs = db.client.table("job_postings")\
    .select("id", count="exact")\
    .execute()

print(f"   Total jobs: {all_jobs.count}")
print(f"   Total type assignments: {all_assignments.count}")
print(f"   Jobs with types: {len(set([a['job_posting_id'] for a in all_assignments.data]))}")
print(f"   Jobs without types: {all_jobs.count - len(set([a['job_posting_id'] for a in all_assignments.data]))}")

print("\n" + "=" * 80)
