#!/usr/bin/env python3
"""Check ranking_updated_at timestamps"""

from database.client import db
from collections import Counter

# Get all ranking timestamps
result = db.client.table("job_postings")\
    .select("ranking_updated_at")\
    .not_.is_("ranking_updated_at", "null")\
    .limit(1000)\
    .execute()

if result.data:
    timestamps = [job['ranking_updated_at'][:16] for job in result.data]  # Group by minute
    timestamp_counts = Counter(timestamps)
    
    print(f"\n📊 Ranking Timestamps (last 1000 jobs):")
    for ts, count in sorted(timestamp_counts.items(), reverse=True)[:10]:
        print(f"   {ts}: {count} jobs")
    
    # Check AXA specifically
    axa_result = db.client.table("job_postings")\
        .select("id, title, ranking_updated_at")\
        .eq("id", "e837e315-dfc8-4c91-87a4-7ae0a16290cd")\
        .single()\
        .execute()
    
    if axa_result.data:
        print(f"\n🔍 AXA Job:")
        print(f"   Updated: {axa_result.data['ranking_updated_at']}")
        print(f"   Title: {axa_result.data['title']}")
