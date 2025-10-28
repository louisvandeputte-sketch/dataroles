#!/usr/bin/env python3
"""
Batch classify company sizes for existing companies.
Runs LLM classification on all companies without size classification.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ingestion.company_size_enrichment import enrich_company_size, get_classification_stats
from database.client import db
from loguru import logger
import time


def classify_companies_batch(limit: Optional[int] = None, force_reclassify: bool = False) -> Dict[str, int]:
    """
    Classify company sizes in batches.
    
    Args:
        limit: Maximum number of companies to classify (None = all)
        force_reclassify: If True, reclassify all companies even if already classified
        
    Returns:
        Dict with success/failure counts
    """
    try:
        # Build query
        query = db.client.table("company_master_data")\
            .select("id, name, country")
        
        if not force_reclassify:
            # Only classify companies without classification
            query = query.is_("size_category", "null")
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        companies = result.data if result.data else []
        
        if not companies:
            logger.info("No companies to classify")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"Found {len(companies)} companies to classify")
        
        success_count = 0
        failed_count = 0
        
        for i, company in enumerate(companies, 1):
            company_id = company["id"]
            company_name = company.get("name")
            country = company.get("country")
            
            if not company_name:
                logger.warning(f"Skipping company {company_id}: no name")
                failed_count += 1
                continue
            
            logger.info(f"[{i}/{len(companies)}] Classifying: {company_name}")
            
            try:
                result = enrich_company_size(company_id, company_name, country)
                
                if result:
                    success_count += 1
                    logger.success(f"  ✅ {result['category']} (confidence: {result['confidence']})")
                else:
                    failed_count += 1
                    logger.error(f"  ❌ Classification failed")
                
                # Rate limiting: wait 2 seconds between requests
                if i < len(companies):
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
                failed_count += 1
                continue
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": 0
        }
        
    except Exception as e:
        logger.error(f"Batch classification failed: {e}")
        return {"success": 0, "failed": 0, "skipped": 0}


if __name__ == "__main__":
    from typing import Optional, Dict
    
    # Parse arguments
    force_reclassify = False
    batch_size = None
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--force", "-f"):
            force_reclassify = True
            print(f"\n🔄 Force reclassify mode: Will classify ALL companies")
            if len(sys.argv) > 2:
                try:
                    batch_size = int(sys.argv[2])
                    print(f"📦 Batch size: {batch_size} companies")
                except ValueError:
                    pass
        else:
            try:
                batch_size = int(sys.argv[1])
                print(f"\n📦 Batch size: {batch_size} companies")
            except ValueError:
                print("❌ Invalid batch size argument. Using all pending companies.")
    
    # Get current stats
    print("\n📊 Current Status:")
    stats = get_classification_stats()
    if stats:
        print(f"   Total companies: {stats['total']}")
        print(f"   Already classified: {stats['classified']}")
        print(f"   Failed classifications: {stats['failed']}")
        print(f"   Pending classification: {stats['pending']}")
        
        if stats['categories']:
            print(f"\n   Category breakdown:")
            for category, count in sorted(stats['categories'].items()):
                print(f"     - {category}: {count}")
    else:
        print("   ❌ Could not retrieve stats")
        sys.exit(1)
    
    # Check if work needed
    if stats['pending'] == 0 and not force_reclassify:
        print("\n✅ All companies are already classified!")
        sys.exit(0)
    
    # Ask for confirmation
    companies_to_process = batch_size if batch_size else (stats['total'] if force_reclassify else stats['pending'])
    print(f"\n⚠️  This will classify {companies_to_process} companies using OpenAI API with web search.")
    print("   This may take a while and will consume API credits.")
    print("   Rate limit: 2 seconds between requests")
    
    if not force_reclassify:
        confirm = input(f"\n   Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Classification cancelled")
            sys.exit(0)
    else:
        print("✅ Force mode: auto-confirmed")
    
    # Run classification
    print(f"\n🚀 Starting classification...")
    print("-" * 60)
    
    result = classify_companies_batch(limit=batch_size, force_reclassify=force_reclassify)
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 Classification Results:")
    print(f"   ✅ Successful: {result['success']}")
    print(f"   ❌ Failed: {result['failed']}")
    print(f"   ⏭️  Skipped: {result['skipped']}")
    print("=" * 60)
    
    # Get updated stats
    print("\n📊 Updated Status:")
    updated_stats = get_classification_stats()
    if updated_stats:
        print(f"   Total companies: {updated_stats['total']}")
        print(f"   Classified: {updated_stats['classified']}")
        print(f"   Pending: {updated_stats['pending']}")
        
        if updated_stats['categories']:
            print(f"\n   Category breakdown:")
            for category, count in sorted(updated_stats['categories'].items()):
                print(f"     - {category}: {count}")
    
    print("\n✅ Done!")
