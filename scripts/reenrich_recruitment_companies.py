#!/usr/bin/env python3
"""
Re-enrich all companies that were classified as recruitment agencies.
This updates them with the improved v16 prompt for better hiring_model detection.
"""

import sys
from pathlib import Path
import time
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db
from ingestion.company_enrichment import enrich_company


def main():
    """Re-enrich all recruitment companies with v16 prompt."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Re-enrich recruitment companies with v16 prompt")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("RE-ENRICHING RECRUITMENT COMPANIES WITH PROMPT V16")
    logger.info("=" * 80)
    
    # Find all companies with hiring_model = 'recruitment'
    logger.info("\n🔍 Finding recruitment companies...")
    
    result = db.client.table("company_master_data")\
        .select("company_id, companies!inner(id, name, logo_url)")\
        .eq("hiring_model", "recruitment")\
        .execute()
    
    if not result.data:
        logger.warning("No recruitment companies found!")
        return
    
    companies = result.data
    total = len(companies)
    
    logger.info(f"✅ Found {total} recruitment companies to re-enrich")
    logger.info("=" * 80)
    
    # Confirm before proceeding (unless --yes flag is used)
    if not args.yes:
        print(f"\n⚠️  This will re-enrich {total} companies with prompt v16.")
        print("This may take a while and will use OpenAI API credits.")
        confirm = input("\nProceed? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            logger.info("❌ Cancelled by user")
            return
    else:
        logger.info(f"⚡ Auto-confirmed with --yes flag")
    
    logger.info("\n🚀 Starting re-enrichment...")
    logger.info("=" * 80)
    
    success_count = 0
    error_count = 0
    
    for i, company_data in enumerate(companies, 1):
        company_info = company_data.get("companies", {})
        company_id = company_info.get("id")
        company_name = company_info.get("name", "Unknown")
        company_url = company_info.get("logo_url")
        
        logger.info(f"\n[{i}/{total}] Re-enriching: {company_name}")
        logger.info(f"Company ID: {company_id}")
        
        try:
            # Re-enrich the company
            result = enrich_company(company_id, company_name, company_url)
            
            if result.get("success"):
                success_count += 1
                logger.success(f"✅ Success! New hiring_model: {result.get('hiring_model', 'unknown')}")
            else:
                error_count += 1
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Failed: {error_msg}")
            
            # Rate limiting: wait 2 seconds between requests
            if i < total:
                time.sleep(2)
        
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Exception: {e}")
            continue
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("RE-ENRICHMENT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"✅ Successful: {success_count}/{total}")
    logger.info(f"❌ Failed: {error_count}/{total}")
    logger.info(f"📊 Success rate: {success_count/total*100:.1f}%")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
