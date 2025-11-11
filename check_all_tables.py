#!/usr/bin/env python3
"""Check all tables in the database."""

from database.client import db

# Try to query known tables
tables_to_check = [
    'job_postings',
    'companies',
    'company_enrichment',
    'locations',
    'job_descriptions',
    'job_posters',
    'job_types',
    'job_type_assignments',
    'job_sources',
    'search_queries',
    'scrape_runs',
    'job_scrape_history',
    'llm_enrichment'
]

print("Checking tables...")
print("=" * 80)

for table in tables_to_check:
    try:
        result = db.client.table(table).select("*").limit(0).execute()
        print(f"✅ {table}")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e).lower():
            print(f"❌ {table} - Does not exist")
        else:
            print(f"⚠️  {table} - Error: {str(e)[:50]}")

# Check companies table structure
print("\n" + "=" * 80)
print("Companies table columns:")
print("=" * 80)

companies = db.client.table("companies").select("*").limit(1).execute()
if companies.data:
    for key in companies.data[0].keys():
        print(f"  - {key}")
