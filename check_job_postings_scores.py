#!/usr/bin/env python3
"""Check ranking scores in job_postings table"""

from database.client import db
from datetime import datetime, timedelta

print("\n🔍 Checking Ranking Scores in job_postings Table...\n")

# Get recent jobs
week_ago = (datetime.utcnow() - timedelta(days=3)).isoformat()

jobs = db.client.table("job_postings")\
    .select("id, title, posted_date, base_score, ranking_score, ranking_position, title_classification")\
    .eq("is_active", True)\
    .gte("posted_date", week_ago)\
    .order("posted_date", desc=True)\
    .limit(30)\
    .execute()

print(f"Found {len(jobs.data)} recent active jobs (last 3 days)\n")

jobs_with_score = 0
jobs_without_score = 0
jobs_without_score_list = []

for job in jobs.data:
    title = job.get('title', 'N/A')[:50]
    base_score = job.get('base_score')
    ranking_score = job.get('ranking_score')
    posted = job.get('posted_date', 'N/A')
    classification = job.get('title_classification', 'N/A')
    
    if base_score is not None and ranking_score is not None:
        jobs_with_score += 1
        print(f"✅ {title:50} | Base: {base_score:5.1f} | Final: {ranking_score:5.1f} | {classification:8} | {posted}")
    else:
        jobs_without_score += 1
        jobs_without_score_list.append(job)
        print(f"❌ {title:50} | Base: {str(base_score):5} | Final: {str(ranking_score):5} | {classification:8} | {posted}")

print(f"\n{'='*80}")
print(f"✅ Jobs WITH scores: {jobs_with_score}")
print(f"❌ Jobs WITHOUT scores: {jobs_without_score}")

if jobs_without_score > 0:
    print(f"\n⚠️ {jobs_without_score} recent jobs have NO ranking scores!")
    
    # Check if they have enrichment
    print(f"\nChecking enrichment status:")
    for job in jobs_without_score_list[:5]:
        enrichment = db.client.table("llm_enrichment")\
            .select("enrichment_completed_at, quality_score, relevance_score")\
            .eq("job_posting_id", job['id'])\
            .execute()
        
        if enrichment.data:
            enr = enrichment.data[0]
            print(f"  {job['title'][:40]:40} | ✅ Has enrichment | Quality: {enr.get('quality_score', 'N/A')}")
        else:
            print(f"  {job['title'][:40]:40} | ❌ NO enrichment!")
    
    print(f"\n{'='*80}")
    print("🎯 DIAGNOSIS")
    print(f"{'='*80}")
    print("\nPossible causes:")
    print("1. Ranking calculation hasn't run yet for these new jobs")
    print("2. Jobs added after last hourly ranking run")
    print("3. Ranking scheduler not running")
    print("4. Jobs missing enrichment data (required for ranking)")
    
    print("\nRecommended actions:")
    print("1. Check if ranking scheduler is running")
    print("2. Manually trigger ranking calculation")
    print("3. Wait for next hourly run")
else:
    print("\n✅ All recent jobs have ranking scores!")

print(f"\n{'='*80}")
