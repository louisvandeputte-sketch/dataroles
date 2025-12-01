#!/usr/bin/env python3
"""Simple check for missing rankings"""

from database.client import db

print("\n🔍 Checking Missing Rankings...\n")

# Get all active jobs
all_jobs = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("is_active", True)\
    .execute()

print(f"Total active jobs: {all_jobs.count}")

# Get jobs in ranking view
ranked_jobs = db.client.table("job_ranking_view")\
    .select("id", count="exact")\
    .execute()

print(f"Jobs in ranking view: {ranked_jobs.count}")

missing = all_jobs.count - ranked_jobs.count
print(f"\n❌ Missing from ranking view: {missing}")

if missing > 0:
    print(f"\n⚠️ {missing} jobs are NOT in the ranking view!")
    print("\nThis means they are missing enrichment data or other required joins.")
    
    # Find which jobs are missing
    all_job_ids = set(j['id'] for j in db.client.table("job_postings").select("id").eq("is_active", True).execute().data)
    ranked_job_ids = set(j['id'] for j in db.client.table("job_ranking_view").select("id").execute().data)
    
    missing_ids = all_job_ids - ranked_job_ids
    
    print(f"\nChecking enrichment status for missing jobs:")
    for job_id in list(missing_ids)[:10]:
        job = db.client.table("job_postings").select("title, posted_date").eq("id", job_id).single().execute().data
        enrichment = db.client.table("llm_enrichment").select("*").eq("job_posting_id", job_id).execute().data
        
        print(f"\n  {job['title'][:50]:50}")
        print(f"    Posted: {job['posted_date']}")
        if enrichment:
            print(f"    ✅ Has enrichment")
        else:
            print(f"    ❌ NO enrichment - this is why it's not ranked!")
else:
    print("\n✅ All active jobs are in the ranking view!")

print("\n" + "="*80)
