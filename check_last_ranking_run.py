#!/usr/bin/env python3
"""Check when the last ranking run was"""

from database.client import db
from datetime import datetime

# Get most recent ranking_updated_at
result = db.client.table("job_postings")\
    .select("ranking_updated_at")\
    .not_.is_("ranking_updated_at", "null")\
    .order("ranking_updated_at", desc=True)\
    .limit(1)\
    .execute()

if result.data:
    last_update = result.data[0]['ranking_updated_at']
    print(f"\n⏰ Last ranking run: {last_update}")
    
    # Parse and show time ago
    from dateutil import parser
    last_dt = parser.parse(last_update)
    now = datetime.now(last_dt.tzinfo)
    diff = now - last_dt
    hours_ago = diff.total_seconds() / 3600
    
    print(f"   Time ago: {hours_ago:.1f} hours")
    
    if hours_ago > 2:
        print(f"   ⚠️ WARNING: Ranking is {hours_ago:.1f} hours old (should run hourly)")
    else:
        print(f"   ✅ Ranking is recent")

# Check how many jobs were updated in the last run
count_last_run = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("ranking_updated_at", last_update)\
    .execute()

print(f"\n📊 Jobs updated in last run: {count_last_run.count}")

# Check jobs with needs_ranking=True
needs_ranking = db.client.table("job_postings")\
    .select("id, title, created_at", count="exact")\
    .eq("needs_ranking", True)\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .limit(10)\
    .execute()

print(f"\n📊 Active Data jobs with needs_ranking=True: {needs_ranking.count}")

if needs_ranking.data:
    print(f"\n   First 10 jobs needing ranking:")
    for job in needs_ranking.data:
        print(f"   - {job['title'][:50]} (created: {job['created_at'][:10]})")
