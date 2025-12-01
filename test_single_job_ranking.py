#!/usr/bin/env python3
"""Test ranking calculation for a single job"""

from database.client import db
from ranking.job_ranker import JobRankingSystem, load_jobs_from_database
from loguru import logger

print("\n🔍 Testing Ranking for Single Job...\n")

# Get the problematic job
job_title = "Technical Solution Architect (Data Platform)"
job_data = db.client.table("job_ranking_view")\
    .select("*")\
    .eq("title", job_title)\
    .single()\
    .execute()

if not job_data.data:
    print(f"❌ Job '{job_title}' not found in job_ranking_view!")
    exit(1)

print(f"✅ Found job: {job_data.data['title']}")
print(f"   ID: {job_data.data['id']}")
print(f"   Posted: {job_data.data.get('posted_date')}")
print(f"   Posted (corrected): {job_data.data.get('posted_date_corrected')}")
print(f"   Classification: {job_data.data.get('title_classification')}")
print(f"   Enrichment completed: {job_data.data.get('enrichment_completed_at')}")

# Try to load all jobs and find this one
print("\n" + "="*80)
print("Loading all jobs from database...")
print("="*80)

try:
    jobs = load_jobs_from_database()
    print(f"✅ Loaded {len(jobs)} jobs total")
    
    # Find our job
    our_job = None
    for job in jobs:
        if job.id == job_data.data['id']:
            our_job = job
            break
    
    if our_job:
        print(f"\n✅ Our job WAS loaded!")
        print(f"   Title: {our_job.title}")
        print(f"   Posted date: {our_job.posted_date}")
        print(f"   Posted date corrected: {our_job.posted_date_corrected}")
        print(f"   Enrichment completed: {our_job.enrichment_completed_at}")
        
        # Try to rank it
        print("\n" + "="*80)
        print("Attempting to rank this job...")
        print("="*80)
        
        ranker = JobRankingSystem()
        ranked = ranker.rank_jobs([our_job])
        
        if ranked:
            print(f"\n✅ Ranking SUCCESSFUL!")
            print(f"   Base score: {ranked[0].base_score:.2f}")
            print(f"   Final score: {ranked[0].final_score:.2f}")
            print(f"   Freshness: {ranked[0].freshness_score:.2f}")
            print(f"   Quality: {ranked[0].quality_score:.2f}")
            print(f"   Transparency: {ranked[0].transparency_score:.2f}")
        else:
            print(f"\n❌ Ranking FAILED - returned empty list!")
    else:
        print(f"\n❌ Our job was NOT loaded from database!")
        print(f"   This means it was filtered out or skipped during loading.")
        print(f"\n   Checking why...")
        
        # Check if it's in the view
        in_view = db.client.table("job_ranking_view").select("id").eq("id", job_data.data['id']).execute()
        if in_view.data:
            print(f"   ✅ Job IS in job_ranking_view")
        else:
            print(f"   ❌ Job NOT in job_ranking_view")
        
        # Check if it's active
        job_posting = db.client.table("job_postings").select("is_active").eq("id", job_data.data['id']).single().execute()
        print(f"   is_active: {job_posting.data.get('is_active')}")

except Exception as e:
    logger.error(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
