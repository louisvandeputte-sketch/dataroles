#!/usr/bin/env python3
"""Check actual llm_enrichment table schema."""

from database.client import db

# Query the table structure via Supabase
result = db.client.table("llm_enrichment").select("*").limit(1).execute()

if result.data:
    print("llm_enrichment columns:")
    print("=" * 80)
    for key in result.data[0].keys():
        print(f"  - {key}")
else:
    print("No data in llm_enrichment table")

# Also check a sample record
sample = db.client.table("llm_enrichment")\
    .select("*")\
    .not_.is_("type_datarol", "null")\
    .limit(1)\
    .execute()

if sample.data:
    print("\nSample enrichment record:")
    print("=" * 80)
    import json
    print(json.dumps(sample.data[0], indent=2, default=str))
