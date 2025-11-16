#!/usr/bin/env python3
"""Test with all joins"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

result = db.client.table("job_postings")\
    .select("""
        *,
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
    
    # Check each join
    print(f"\ncompanies: {type(row.get('companies'))}, empty: {not row.get('companies')}")
    print(f"company_master_data: {type(row.get('company_master_data'))}, empty: {not row.get('company_master_data')}")
    print(f"locations: {type(row.get('locations'))}, empty: {not row.get('locations')}")
    print(f"llm_enrichment: {type(row.get('llm_enrichment'))}, empty: {not row.get('llm_enrichment')}")
    print(f"job_descriptions: {type(row.get('job_descriptions'))}, empty: {not row.get('job_descriptions')}")
    
    enrichment = row.get('llm_enrichment') or {}
    if isinstance(enrichment, dict):
        print(f"\nEnrichment has {len(enrichment.keys())} keys")
        print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")
