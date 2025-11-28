#!/usr/bin/env python3
"""Check if AXA job is enriched"""

from database.client import db

# Check enrichment status
result = db.client.table("job_ranking_view")\
    .select("id, title, company_name, enrichment_completed_at, data_role_type")\
    .eq("id", "e837e315-dfc8-4c91-87a4-7ae0a16290cd")\
    .single()\
    .execute()

if result.data:
    job = result.data
    print(f"\n🔍 AXA AI Analyst Enrichment Status:")
    print(f"   ID: {job['id']}")
    print(f"   Title: {job['title']}")
    print(f"   Company: {job['company_name']}")
    print(f"   Enrichment Completed: {job['enrichment_completed_at']}")
    print(f"   Data Role Type: {job['data_role_type']}")
    
    if not job['enrichment_completed_at']:
        print(f"\n   ⚠️ NOT ENRICHED - Will get base_score = -9999!")
    else:
        print(f"\n   ✅ ENRICHED - Normal scoring applies")
