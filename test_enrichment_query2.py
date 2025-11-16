#!/usr/bin/env python3
"""Test different enrichment query approaches"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

print("=== Test 1: Without foreign key hint ===")
result1 = db.client.table("job_postings")\
    .select("id, title, llm_enrichment(*)")\
    .eq("title", "Technical power BI consultant (medior)")\
    .limit(1)\
    .execute()

if result1.data:
    job = result1.data[0]
    enrichment = job.get('llm_enrichment')
    print(f"Type: {type(enrichment)}")
    if isinstance(enrichment, list):
        print(f"List with {len(enrichment)} items")
        if enrichment:
            print(f"enrichment_completed_at: {enrichment[0].get('enrichment_completed_at')}")
    elif isinstance(enrichment, dict):
        print(f"Dict")
        print(f"enrichment_completed_at: {enrichment.get('enrichment_completed_at')}")
    else:
        print(f"Value: {enrichment}")

print("\n=== Test 2: Direct query on llm_enrichment ===")
result2 = db.client.table("llm_enrichment")\
    .select("enrichment_completed_at, job_posting_id")\
    .eq("job_posting_id", "d2ba4093-f21f-4513-91a3-3dfe0949f5d3")\
    .execute()

if result2.data:
    print(f"Found enrichment: {result2.data[0]}")
else:
    print("No enrichment found")
