#!/usr/bin/env python3
"""Fresh check of AXA job ranking"""

from database.client import db
from datetime import datetime

# Get AXA job with fresh query
result = db.client.table("job_postings")\
    .select("id, title, base_score, ranking_score, ranking_position, ranking_metadata, ranking_updated_at")\
    .eq("id", "e837e315-dfc8-4c91-87a4-7ae0a16290cd")\
    .single()\
    .execute()

if result.data:
    job = result.data
    print(f"\n🔍 AXA AI Analyst (Fresh Query):")
    print(f"   ID: {job['id']}")
    print(f"   Title: {job['title']}")
    print(f"   Rank: {job['ranking_position']}")
    print(f"   Base Score: {job['base_score']}")
    print(f"   Ranking Score: {job['ranking_score']}")
    print(f"   Updated At: {job['ranking_updated_at']}")
    
    if job['ranking_metadata']:
        meta = job['ranking_metadata']
        print(f"\n   📊 Metadata:")
        print(f"   - Freshness: {meta.get('freshness_score')}")
        print(f"   - Quality: {meta.get('quality_score')}")
        print(f"   - Transparency: {meta.get('transparency_score')}")
        print(f"   - Role Match: {meta.get('role_match_score')}")
        print(f"   - Base Score: {meta.get('base_score')}")
        
        # Calculate expected score with F:20
        expected_base = 20 + meta.get('quality_score', 0) + meta.get('transparency_score', 0) + meta.get('role_match_score', 0)
        print(f"\n   💡 Expected base score with F:20: {expected_base}")
