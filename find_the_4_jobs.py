"""Find the exact 4 jobs causing the discrepancy."""

from database import db

print("="*80)
print("FINDING THE 4 MISSING JOBS")
print("="*80)

# Get all Data jobs with completed enrichment (filter perspective)
filter_jobs = db.client.table("job_postings")\
    .select("id, title, llm_enrichment(id, enrichment_completed_at)")\
    .eq("title_classification", "Data")\
    .not_.is_("llm_enrichment.enrichment_completed_at", "null")\
    .execute()

filter_job_ids = {j['id'] for j in filter_jobs.data}
print(f"Filter finds: {len(filter_job_ids)} Data jobs with completed enrichment")

# Get all enriched Data jobs (stats perspective)
stats_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id, id, enrichment_completed_at, job_postings!inner(id, title, title_classification)")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

stats_job_ids = {e['job_posting_id'] for e in stats_enrichments.data}
print(f"Stats finds: {len(stats_job_ids)} unique Data jobs with completed enrichment")

# Find the difference
in_filter_not_stats = filter_job_ids - stats_job_ids
in_stats_not_filter = stats_job_ids - filter_job_ids

print(f"\nJobs in FILTER but NOT in STATS: {len(in_filter_not_stats)}")
print(f"Jobs in STATS but NOT in FILTER: {len(in_stats_not_filter)}")

# These are the 4 problematic jobs
print("\n" + "="*80)
print("THE 4 PROBLEMATIC JOBS (in filter but not in stats):")
print("="*80)

for job_id in in_filter_not_stats:
    # Get job details
    job = db.client.table("job_postings")\
        .select("id, title, title_classification, is_active")\
        .eq("id", job_id)\
        .single()\
        .execute()
    
    # Get ALL enrichment records for this job
    enrichments = db.client.table("llm_enrichment")\
        .select("id, enrichment_completed_at, created_at")\
        .eq("job_posting_id", job_id)\
        .execute()
    
    print(f"\nJob: {job.data['title']}")
    print(f"ID: {job_id}")
    print(f"title_classification: {job.data['title_classification']}")
    print(f"is_active: {job.data['is_active']}")
    print(f"Enrichment records: {len(enrichments.data)}")
    
    for i, e in enumerate(enrichments.data, 1):
        print(f"  {i}. ID: {e['id']}")
        print(f"     completed_at: {e.get('enrichment_completed_at')}")
        print(f"     created_at: {e.get('created_at')}")
    
    # Check if the job_postings record exists in the enrichment query
    check = db.client.table("llm_enrichment")\
        .select("*, job_postings!inner(title_classification)")\
        .eq("job_posting_id", job_id)\
        .not_.is_("enrichment_completed_at", "null")\
        .execute()
    
    print(f"  Stats query finds this job: {len(check.data) > 0}")
    if check.data:
        for c in check.data:
            print(f"    - job_postings data: {c.get('job_postings')}")

print("\n" + "="*80)
