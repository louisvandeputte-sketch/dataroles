#!/usr/bin/env python3
"""Check when ranking was last calculated"""

from database.client import db
from datetime import datetime

print("\n🔍 Checking Last Ranking Calculation...\n")

# Check the most recent ranking_score update
jobs_with_scores = db.client.table("job_postings")\
    .select("id, title, base_score, ranking_score, updated_at")\
    .not_.is_("ranking_score", "null")\
    .order("updated_at", desc=True)\
    .limit(10)\
    .execute()

if jobs_with_scores.data:
    latest = jobs_with_scores.data[0]
    print(f"Latest ranking update: {latest['updated_at']}")
    print(f"Job: {latest['title']}")
    print(f"Score: {latest['ranking_score']}")
    
    # Parse and check how long ago
    updated_at = datetime.fromisoformat(latest['updated_at'].replace('Z', '+00:00'))
    now = datetime.utcnow().replace(tzinfo=updated_at.tzinfo)
    hours_ago = (now - updated_at).total_seconds() / 3600
    
    print(f"\n⏰ Last ranking run was {hours_ago:.1f} hours ago")
    
    if hours_ago > 2:
        print(f"   ⚠️ Rankings are STALE! Should run every hour.")
        print(f"   Ranking scheduler may not be running!")
    else:
        print(f"   ✅ Rankings are recent")
else:
    print("❌ No jobs with ranking scores found!")

print("\n" + "="*80)
print("🔍 Checking Jobs Without Scores")
print("="*80)

jobs_without_scores = db.client.table("job_postings")\
    .select("id, title, posted_date, title_classification")\
    .is_("ranking_score", "null")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(10)\
    .execute()

print(f"\nFound {len(jobs_without_scores.data)} active jobs without scores\n")

for job in jobs_without_scores.data:
    print(f"  {job['title'][:50]:50} | {job.get('title_classification', 'N/A'):8} | {job['posted_date']}")

print("\n" + "="*80)
print("🎯 SOLUTION")
print("="*80)

print("\nThe ranking scheduler should run every hour to calculate scores for new jobs.")
print("\nTo fix:")
print("1. Check if ranking scheduler is running in Railway logs")
print("2. Manually trigger ranking calculation:")
print("   python -m ranking.calculate_rankings")
print("3. Or wait for next hourly run")

print("\n" + "="*80)
