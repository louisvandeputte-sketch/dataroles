"""Check for duplicate enrichment records."""

from database import db

print("="*80)
print("CHECKING FOR DUPLICATE ENRICHMENT RECORDS")
print("="*80)

# Query all enrichment records
all_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id", count="exact")\
    .execute()

unique_jobs = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .execute()

unique_job_ids = set(e['job_posting_id'] for e in unique_jobs.data)

print(f"\nTotal enrichment records: {all_enrichments.count}")
print(f"Unique job_posting_ids: {len(unique_job_ids)}")
print(f"Duplicate records: {all_enrichments.count - len(unique_job_ids)}")

# Find specific duplicates
from collections import Counter
job_counts = Counter(e['job_posting_id'] for e in unique_jobs.data)
duplicates_list = [(job_id, count) for job_id, count in job_counts.items() if count > 1]

print(f"\nJobs with duplicates: {len(duplicates_list)}")
print("\nTop 10 jobs with most duplicates:")
for job_id, count in sorted(duplicates_list, key=lambda x: x[1], reverse=True)[:10]:
    # Get job details
    job = db.client.table("job_postings")\
        .select("title, title_classification")\
        .eq("id", job_id)\
        .single()\
        .execute()
    
    # Get enrichment records
    enrichments = db.client.table("llm_enrichment")\
        .select("id, enrichment_completed_at, created_at")\
        .eq("job_posting_id", job_id)\
        .order("created_at")\
        .execute()
    
    print(f"\n  Job: {job.data['title']}")
    print(f"  ID: {job_id}")
    print(f"  Classification: {job.data['title_classification']}")
    print(f"  Enrichment records: {count}")
    for i, e in enumerate(enrichments.data, 1):
        print(f"    {i}. created: {e['created_at']}, completed: {e.get('enrichment_completed_at', 'NULL')}")

print("\n" + "="*80)
