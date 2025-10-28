"""
Test script to debug company enrichment issues.
"""

import sys
from loguru import logger
from ingestion.company_enrichment import enrich_company
from database.client import db

# Configure logger
logger.remove()
logger.add(sys.stdout, level="DEBUG")

def test_enrichment():
    """Test enrichment with a known company."""
    
    # Get a company from the database
    result = db.client.table("companies")\
        .select("id, name, logo_url")\
        .limit(1)\
        .execute()
    
    if not result.data:
        logger.error("No companies found in database")
        return
    
    company = result.data[0]
    company_id = company["id"]
    company_name = company["name"]
    company_url = company.get("logo_url")
    
    logger.info(f"Testing enrichment for: {company_name} (ID: {company_id})")
    
    try:
        result = enrich_company(company_id, company_name, company_url)
        
        if result.get("success"):
            logger.success(f"✅ Enrichment successful!")
            logger.info(f"Data: {result.get('data')}")
        else:
            logger.error(f"❌ Enrichment failed: {result.get('error')}")
            
    except Exception as e:
        logger.exception(f"❌ Exception during enrichment: {e}")

if __name__ == "__main__":
    test_enrichment()
