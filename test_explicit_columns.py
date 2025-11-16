#!/usr/bin/env python3
"""Test with explicit columns"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

result = db.client.table("job_postings")\
    .select("""
        id, title, company_id, location_id, posted_date, seniority_level, 
        employment_type, function_areas, base_salary_min, base_salary_max, 
        apply_url, num_applicants, is_active,
        companies(*),
        company_master_data(hiring_model),
        locations(*),
        llm_enrichment(*),
        job_descriptions(description_text)
    """)\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result.data:
    row = result.data[0]
    print(f"Job ID: {row['id']}")
    
    enrichment = row.get('llm_enrichment') or {}
    print(f"\nEnrichment type: {type(enrichment)}")
    if isinstance(enrichment, dict):
        print(f"Enrichment has {len(enrichment.keys())} keys")
        print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")
        
        if enrichment.get('enrichment_completed_at'):
            print("\n✅ SUCCESS! Enrichment data loaded correctly")
        else:
            print("\n❌ FAIL! No enrichment_completed_at")
