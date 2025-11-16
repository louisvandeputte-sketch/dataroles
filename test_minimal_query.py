#!/usr/bin/env python3
"""Test minimal query"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

print("=== Test 1: Only llm_enrichment ===")
result1 = db.client.table("job_postings")\
    .select("id, title, llm_enrichment(*)")\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result1.data:
    row = result1.data[0]
    enrichment = row.get('llm_enrichment') or {}
    print(f"Enrichment type: {type(enrichment)}")
    print(f"Is empty: {not enrichment or enrichment == {}}")
    if isinstance(enrichment, dict) and enrichment:
        print(f"Has keys: {len(enrichment.keys())}")
        print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")

print("\n=== Test 2: With companies join ===")
result2 = db.client.table("job_postings")\
    .select("id, title, companies(*), llm_enrichment(*)")\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result2.data:
    row = result2.data[0]
    enrichment = row.get('llm_enrichment') or {}
    print(f"Enrichment type: {type(enrichment)}")
    print(f"Is empty: {not enrichment or enrichment == {}}")
    if isinstance(enrichment, dict) and enrichment:
        print(f"Has keys: {len(enrichment.keys())}")
        print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")
