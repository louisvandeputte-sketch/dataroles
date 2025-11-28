#!/usr/bin/env python3
"""Rank only AXA job with detailed logging"""

from database.client import db
from ranking.job_ranker import JobRankingSystem
from datetime import datetime

# Get AXA job from view
result = db.client.table("job_ranking_view")\
    .select("*")\
    .eq("id", "e837e315-dfc8-4c91-87a4-7ae0a16290cd")\
    .single()\
    .execute()

if not result.data:
    print("❌ AXA job not found in view")
    exit(1)

row = result.data
print(f"\n🔍 Loading AXA job from view:")
print(f"   posted_date: {row.get('posted_date')}")
print(f"   posted_date_corrected: {row.get('posted_date_corrected')}")

# Parse dates
from dateutil import parser as date_parser

def parse_datetime(date_str):
    if not date_str:
        return None
    try:
        return date_parser.isoparse(date_str)
    except:
        return None

posted_date = parse_datetime(row.get('posted_date'))
posted_date_corrected = parse_datetime(row.get('posted_date_corrected'))

print(f"\n📅 Parsed dates:")
print(f"   posted_date: {posted_date}")
print(f"   posted_date_corrected: {posted_date_corrected}")

if posted_date_corrected:
    age = datetime.now(posted_date_corrected.tzinfo) - posted_date_corrected
    hours_old = age.total_seconds() / 3600
    print(f"   Age: {age.days} days ({hours_old:.1f} hours)")
    
    # Calculate freshness score
    if hours_old <= 30:
        freshness = 150
    elif age.days <= 1:
        freshness = 100
    elif age.days <= 3:
        freshness = 90
    elif age.days <= 7:
        freshness = 75
    elif age.days <= 14:
        freshness = 60
    elif age.days <= 30:
        freshness = 40
    else:
        freshness = 20
    
    print(f"   Expected freshness score: {freshness}")

# Now update the job manually
print(f"\n🔄 Manually updating job...")
update_result = db.client.table("job_postings").update({
    'ranking_metadata': {
        'freshness_score': freshness,
        'quality_score': 20,
        'transparency_score': 90,
        'role_match_score': 90,
        'base_score': freshness + 20 + 90 + 90
    },
    'base_score': freshness + 20 + 90 + 90,
    'ranking_updated_at': datetime.now().isoformat()
}).eq('id', row['id']).execute()

print(f"✅ Update result: {update_result.data}")
