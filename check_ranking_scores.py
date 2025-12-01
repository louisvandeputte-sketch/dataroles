#!/usr/bin/env python3
"""Check which jobs have ranking scores"""

from database.client import db
from datetime import datetime, timedelta

print("\n🔍 Checking Ranking Scores...\n")

# Get recent jobs from ranking view
week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

jobs = db.client.rpc("get_ranked_jobs", {
    "limit_count": 50
}).execute()

print(f"Got {len(jobs.data)} jobs from get_ranked_jobs RPC\n")

jobs_with_score = 0
jobs_without_score = 0

for job in jobs.data[:20]:
    title = job.get('title', 'N/A')[:40]
    final_score = job.get('final_score')
    base_score = job.get('base_score')
    posted = job.get('posted_date_corrected', job.get('posted_date', 'N/A'))
    
    if final_score is not None:
        jobs_with_score += 1
        print(f"✅ {title:40} | Score: {final_score:5.1f} | Posted: {posted}")
    else:
        jobs_without_score += 1
        print(f"❌ {title:40} | Score: None   | Posted: {posted}")

print(f"\n✅ Jobs WITH score: {jobs_with_score}")
print(f"❌ Jobs WITHOUT score: {jobs_without_score}")

if jobs_without_score > 0:
    print(f"\n⚠️ {jobs_without_score} jobs have NO ranking scores!")
    print("\nThis could mean:")
    print("1. Ranking calculation hasn't run yet")
    print("2. Jobs were added after last ranking run")
    print("3. Ranking calculation is failing for these jobs")

print("\n" + "="*80)
