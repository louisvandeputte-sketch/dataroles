#!/usr/bin/env python3
"""Test enrichment query to debug ranking issue"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

# Test the exact query used in ranking
result = db.client.table("job_postings")\
    .select("""
        id,
        title,
        llm_enrichment!job_posting_id(*)
    """)\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result.data:
    job = result.data[0]
    print(f"Job ID: {job['id']}")
    print(f"Title: {job['title']}")
    print(f"\nEnrichment data type: {type(job.get('llm_enrichment'))}")
    print(f"Enrichment data: {job.get('llm_enrichment')}")
    
    enrichment = job.get('llm_enrichment')
    if enrichment:
        if isinstance(enrichment, list):
            print(f"\n⚠️  It's a LIST with {len(enrichment)} items")
            if enrichment:
                print(f"First item: {enrichment[0].get('enrichment_completed_at')}")
        elif isinstance(enrichment, dict):
            print(f"\n✅ It's a DICT")
            print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")
        else:
            print(f"\n❌ Unknown type: {type(enrichment)}")
    else:
        print("\n❌ No enrichment data")
else:
    print("Job not found")
