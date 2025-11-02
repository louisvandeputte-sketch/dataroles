"""Debug enrichment failures."""

import sys
import json
from loguru import logger

# Configure detailed logging
logger.remove()
logger.add(sys.stdout, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

from database.client import db

# Check recent failures
print("\n" + "="*80)
print("CHECKING RECENT ENRICHMENT FAILURES")
print("="*80 + "\n")

result = db.client.table("company_master_data")\
    .select("company_id, ai_enrichment_error, ai_enriched_at, size_enrichment_error")\
    .eq("ai_enriched", False)\
    .order("ai_enriched_at", desc=True)\
    .limit(5)\
    .execute()

if result.data:
    for i, row in enumerate(result.data, 1):
        print(f"\n--- Failure #{i} ---")
        print(f"Company ID: {row['company_id']}")
        print(f"Timestamp: {row.get('ai_enriched_at', 'N/A')}")
        print(f"Error: {row.get('ai_enrichment_error', 'N/A')}")
        if row.get('size_enrichment_error'):
            print(f"Size Error: {row['size_enrichment_error']}")
        print("-" * 80)
else:
    print("✅ No recent failures found!")

# Now try a test enrichment
print("\n" + "="*80)
print("TESTING ENRICHMENT WITH A SAMPLE COMPANY")
print("="*80 + "\n")

# Get a company
company_result = db.client.table("companies")\
    .select("id, name, logo_url")\
    .limit(1)\
    .execute()

if company_result.data:
    company = company_result.data[0]
    print(f"Testing with: {company['name']} (ID: {company['id']})")
    print(f"URL: {company.get('logo_url', 'N/A')}")
    
    print("\nCalling enrich_company()...")
    
    try:
        from ingestion.company_enrichment import enrich_company
        
        result = enrich_company(
            company_id=company['id'],
            company_name=company['name'],
            company_url=company.get('logo_url')
        )
        
        print("\n" + "="*80)
        print("RESULT:")
        print("="*80)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ EXCEPTION CAUGHT:")
        print("="*80)
        logger.exception(e)
else:
    print("❌ No companies found in database")
