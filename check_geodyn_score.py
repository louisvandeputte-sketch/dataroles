#!/usr/bin/env python3
"""Check GeoDynamics job score after re-ranking"""

from database.client import db

# Get GeoDynamics job
result = db.client.table("job_postings")\
    .select("id, title, base_score, ranking_score, ranking_metadata, ranking_updated_at")\
    .eq("id", "faf12622-68b4-477e-9ca2-59527485cdb1")\
    .single()\
    .execute()

if result.data:
    job = result.data
    print(f"\n🔍 GeoDynamics ML/AI Job:")
    print(f"   Title: {job['title']}")
    print(f"   Base Score: {job['base_score']}")
    print(f"   Ranking Score: {job['ranking_score']}")
    print(f"   Updated At: {job['ranking_updated_at']}")
    
    if job['ranking_metadata']:
        meta = job['ranking_metadata']
        print(f"\n   📊 Score Breakdown:")
        print(f"   F:{meta.get('freshness_score')} Q:{meta.get('quality_score')} T:{meta.get('transparency_score')} R:{meta.get('role_match_score')}")
        
        freshness = meta.get('freshness_score')
        if freshness == 150:
            print(f"\n   ❌ STILL WRONG! F:150 (should be F:40)")
        elif freshness == 40:
            print(f"\n   ✅ CORRECT! F:40 (26 days old)")
        else:
            print(f"\n   ⚠️ Unexpected freshness: {freshness}")
