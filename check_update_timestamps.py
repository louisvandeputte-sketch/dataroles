#!/usr/bin/env python3
"""Check which jobs were updated in the last ranking run"""

from database.client import db
from collections import Counter

# Get all jobs with their update timestamps
result = db.client.table("job_postings")\
    .select("id, title, ranking_updated_at, ranking_score, base_score, hourly_multiplier")\
    .not_.is_("ranking_updated_at", "null")\
    .limit(1000)\
    .execute()

# Group by timestamp (minute precision)
timestamps = [job['ranking_updated_at'][:16] for job in result.data]
timestamp_counts = Counter(timestamps)

print("\n📊 Ranking Update Timestamps (last 1000 jobs):\n")
for ts, count in sorted(timestamp_counts.items(), reverse=True)[:10]:
    print(f"   {ts}: {count} jobs")

# Check a few jobs that should have been updated
latest_ts = sorted(timestamp_counts.keys(), reverse=True)[0]
print(f"\n🔍 Latest timestamp: {latest_ts}")

# Find jobs NOT updated in latest run
old_jobs = [job for job in result.data if job['ranking_updated_at'][:16] != latest_ts]
print(f"\n⚠️ Jobs NOT updated in latest run: {len(old_jobs)}")

if old_jobs:
    print(f"\nFirst 5 old jobs:")
    for job in old_jobs[:5]:
        # Verify calculation
        expected = job['base_score'] * job['hourly_multiplier'] if job['base_score'] and job['hourly_multiplier'] else None
        actual = job['ranking_score']
        match = abs(expected - actual) < 0.5 if expected and actual else False
        
        print(f"   {job['title'][:50]}")
        print(f"      Updated: {job['ranking_updated_at'][:16]}")
        print(f"      Calc: {job['base_score']:.1f} × {job['hourly_multiplier']:.3f} = {expected:.1f}")
        print(f"      DB: {actual:.1f}  Match: {match}")
