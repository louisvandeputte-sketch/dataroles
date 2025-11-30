#!/usr/bin/env python3
"""Check if jobs without scores have enrichment"""

from database.client import db

# Get jobs without ranking scores
result = db.client.table("job_postings")\
    .select("id, title")\
    .is_("ranking_score", "null")\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .limit(10)\
    .execute()

print(f"\n🔍 Checking enrichment for {len(result.data)} jobs without scores:\n")

for job in result.data:
    job_id = job['id']
    title = job['title']
    
    # Check if it has enrichment
    enrichment = db.client.table("llm_enrichment")\
        .select("job_posting_id, enrichment_completed_at, type_datarol")\
        .eq("job_posting_id", job_id)\
        .execute()
    
    # Check if it's in job_ranking_view
    in_view = db.client.table("job_ranking_view")\
        .select("id")\
        .eq("id", job_id)\
        .execute()
    
    has_enrichment = len(enrichment.data) > 0
    in_ranking_view = len(in_view.data) > 0
    
    status = "✅" if has_enrichment else "❌"
    view_status = "✅" if in_ranking_view else "❌"
    
    print(f"{status} {title[:50]}")
    print(f"   Enrichment: {has_enrichment}")
    print(f"   In ranking view: {view_status}")
    
    if has_enrichment:
        enr = enrichment.data[0]
        print(f"   Completed: {enr.get('enrichment_completed_at')}")
        print(f"   Role type: {enr.get('type_datarol')}")
    
    print()

# Summary
total_without_scores = db.client.table("job_postings")\
    .select("id", count="exact")\
    .is_("ranking_score", "null")\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .execute()

print(f"\n📊 Summary:")
print(f"   Total Data jobs without scores: {total_without_scores.count}")
