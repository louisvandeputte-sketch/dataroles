#!/usr/bin/env python3
"""Check GeoDynamics job classification"""

from database.client import db

geodyn_id = "faf12622-68b4-477e-9ca2-59527485cdb1"

result = db.client.table("job_postings")\
    .select("id, title, title_classification, ranking_position, ranking_score")\
    .eq("id", geodyn_id)\
    .single()\
    .execute()

if result.data:
    job = result.data
    print(f"\n🔍 GeoDynamics Job:")
    print(f"   Title: {job['title']}")
    print(f"   Classification: {job['title_classification']}")
    print(f"   Ranking Position: {job['ranking_position']}")
    print(f"   Ranking Score: {job['ranking_score']}")
    
    if job['title_classification'] == 'NIS':
        print(f"\n   ⚠️ This is a NIS job!")
        print(f"   NIS jobs get rank 999999 and are not shown in Data jobs table")
    elif job['title_classification'] == 'Data':
        print(f"\n   ✅ This is a Data job - should be ranked normally")
