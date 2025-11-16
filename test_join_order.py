#!/usr/bin/env python3
"""Test join order"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

print("=== Test: llm_enrichment FIRST ===")
result = db.client.table("job_postings")\
    .select("""
        id, title,
        llm_enrichment(*),
        companies(*),
        locations(*)
    """)\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result.data:
    row = result.data[0]
    enrichment = row.get('llm_enrichment') or {}
    print(f"Enrichment type: {type(enrichment)}")
    if isinstance(enrichment, dict):
        print(f"Has {len(enrichment.keys())} keys")
        print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")
