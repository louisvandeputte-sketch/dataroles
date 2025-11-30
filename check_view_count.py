#!/usr/bin/env python3
"""Check how many jobs are in job_ranking_view"""

from database.client import db

# Count total jobs in view
total = db.client.table("job_ranking_view")\
    .select("id", count="exact")\
    .execute()

print(f"\n📊 Total jobs in job_ranking_view: {total.count}")

# Count by classification
data_jobs = db.client.table("job_ranking_view")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .execute()

print(f"   Data jobs: {data_jobs.count}")

# Count active Data jobs in job_postings
active_data = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .execute()

print(f"\n📊 Active Data jobs in job_postings: {active_data.count}")

# Check if there's a difference
diff = active_data.count - data_jobs.count
if diff > 0:
    print(f"\n⚠️ MISMATCH: {diff} active Data jobs are NOT in job_ranking_view!")
    
    # Find which jobs are missing
    print(f"\n🔍 Finding missing jobs...")
    
    # Get all job IDs from view
    view_ids = db.client.table("job_ranking_view")\
        .select("id")\
        .eq("title_classification", "Data")\
        .execute()
    
    view_id_set = {job['id'] for job in view_ids.data}
    
    # Get all active Data job IDs from job_postings
    posting_ids = db.client.table("job_postings")\
        .select("id, title, created_at")\
        .eq("is_active", True)\
        .eq("title_classification", "Data")\
        .execute()
    
    missing_jobs = [job for job in posting_ids.data if job['id'] not in view_id_set]
    
    print(f"\n   Found {len(missing_jobs)} missing jobs:")
    for job in missing_jobs[:10]:
        print(f"   - {job['title'][:50]} (created: {job['created_at'][:10]})")
        
        # Check why it's not in view
        # Check if it has enrichment
        enrichment = db.client.table("llm_enrichment")\
            .select("job_posting_id")\
            .eq("job_posting_id", job['id'])\
            .execute()
        
        has_enrichment = len(enrichment.data) > 0
        print(f"     Has enrichment: {has_enrichment}")
else:
    print(f"\n✅ All active Data jobs are in job_ranking_view")
