#!/usr/bin/env python3
"""Check ranking scores directly from view"""

from database.client import db
from datetime import datetime, timedelta

print("\n🔍 Checking Ranking Scores in View...\n")

# Get recent jobs
week_ago = (datetime.utcnow() - timedelta(days=3)).isoformat()

# Check what columns exist in the view
print("Checking view structure...")
sample = db.client.table("job_ranking_view")\
    .select("*")\
    .limit(1)\
    .execute()

if sample.data:
    print(f"View columns: {list(sample.data[0].keys())}\n")

# Get recent jobs
jobs = db.client.table("job_ranking_view")\
    .select("id, title, posted_date, posted_date_corrected")\
    .gte("posted_date", week_ago)\
    .order("posted_date", desc=True)\
    .limit(20)\
    .execute()

print(f"Found {len(jobs.data)} recent jobs (last 3 days)\n")

# The view doesn't have ranking scores - those are calculated separately!
# Let's check if there's a job_rankings table

print("="*80)
print("Checking for job_rankings table...")
print("="*80)

try:
    rankings_sample = db.client.table("job_rankings")\
        .select("*")\
        .limit(1)\
        .execute()
    print(f"✅ job_rankings table exists!")
    if rankings_sample.data:
        print(f"   Columns: {list(rankings_sample.data[0].keys())}")
except Exception as e:
    print(f"❌ job_rankings table does not exist: {e}")

print("\n" + "="*80)
print("Checking for job_ranking_scores table...")
print("="*80)

try:
    scores_sample = db.client.table("job_ranking_scores")\
        .select("*")\
        .limit(1)\
        .execute()
    print(f"✅ job_ranking_scores table exists!")
    if scores_sample.data:
        print(f"   Columns: {list(scores_sample.data[0].keys())}")
        
        # Count how many jobs have scores
        all_scores = db.client.table("job_ranking_scores")\
            .select("id", count="exact")\
            .execute()
        print(f"   Total jobs with scores: {all_scores.count}")
        
        # Check recent jobs
        recent_scores = db.client.table("job_ranking_scores")\
            .select("*")\
            .order("calculated_at", desc=True)\
            .limit(5)\
            .execute()
        
        if recent_scores.data:
            print(f"\n   Recent scores:")
            for score in recent_scores.data:
                print(f"     Job: {score.get('job_posting_id')[:8]}... | Score: {score.get('final_score', 'N/A')} | Calc: {score.get('calculated_at', 'N/A')}")
        
except Exception as e:
    print(f"❌ job_ranking_scores table does not exist: {e}")

print("\n" + "="*80)
