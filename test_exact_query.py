#!/usr/bin/env python3
"""Test the exact query from load_jobs_from_database"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

# Exact query from the code
result = db.client.table("job_postings")\
    .select("""
        *,
        companies(*),
        company_master_data(hiring_model),
        locations(*),
        llm_enrichment(*),
        job_descriptions(description_text)
    """)\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result.data:
    row = result.data[0]
    print(f"Job ID: {row['id']}")
    print(f"Title: {row['title']}")
    
    enrichment = row.get('llm_enrichment') or {}
    print(f"\nEnrichment type: {type(enrichment)}")
    print(f"Enrichment keys: {list(enrichment.keys())[:10] if isinstance(enrichment, dict) else 'N/A'}")
    print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at') if isinstance(enrichment, dict) else 'N/A'}")
    
    # Check if it's empty
    if not enrichment:
        print("\n❌ Enrichment is empty!")
    elif isinstance(enrichment, dict) and enrichment.get('enrichment_completed_at'):
        print(f"\n✅ Enrichment completed at: {enrichment['enrichment_completed_at']}")
    else:
        print(f"\n⚠️  Enrichment exists but no completed_at timestamp")
else:
    print("No job found")
