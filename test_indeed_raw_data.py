#!/usr/bin/env python3
"""
Test script to check raw data from Bright Data Indeed API
Logs all API responses to see what's actually coming back
"""

import asyncio
import sys
import json
sys.path.insert(0, '.')

from clients.brightdata_indeed import BrightDataIndeedClient
from config.settings import settings
from loguru import logger
import httpx

# Configure logger to show everything
logger.remove()
logger.add(sys.stdout, level="DEBUG")

async def test_indeed_raw_data():
    """Test Indeed scraping and log all raw responses"""
    
    logger.info("=" * 80)
    logger.info("🧪 TESTING INDEED SCRAPE - RAW DATA INSPECTION")
    logger.info("=" * 80)
    
    # Initialize client
    indeed_dataset_id = "gd_l4dx9j9sscpvs7no2"
    client = BrightDataIndeedClient(
        api_token=settings.brightdata_api_token,
        dataset_id=indeed_dataset_id,
        timeout=1800,
        poll_interval=10  # Poll every 10 seconds for faster feedback
    )
    
    try:
        # Step 1: Trigger collection
        logger.info("\n📡 STEP 1: Triggering collection...")
        logger.info(f"Query: 'Data Engineer' in 'Belgium' (past_week)")
        
        snapshot_id = await client.trigger_collection(
            keyword="Data Engineer",
            location="Belgium",
            posted_date_range="past_week",
            limit=1000
        )
        
        logger.success(f"✅ Collection triggered! Snapshot ID: {snapshot_id}")
        
        # Step 2 & 3: Wait for completion and download (client handles this)
        logger.info("\n⏳ STEP 2 & 3: Waiting for completion and downloading...")
        logger.info(f"Client will poll every {client.poll_interval} seconds")
        
        results = await client.wait_for_completion(snapshot_id)
        
        logger.success(f"✅ Results downloaded!")
        logger.info(f"Response Size: {len(str(results))} chars")
        
        if True:  # Keep the analysis code
            
            logger.info(f"\n📊 RAW RESULTS ANALYSIS:")
            logger.info(f"Type: {type(results)}")
            logger.info(f"Length: {len(results) if isinstance(results, list) else 'N/A'}")
            
            if isinstance(results, list):
                logger.info(f"Total items: {len(results)}")
                
                # Check for errors
                errors = [r for r in results if r.get('error')]
                logger.info(f"Error items: {len(errors)}")
                
                # Check for valid jobs
                valid_jobs = [r for r in results if not r.get('error')]
                logger.info(f"Valid jobs: {len(valid_jobs)}")
                
                if len(results) > 0:
                    logger.info(f"\n📄 FIRST ITEM (raw):")
                    logger.info(json.dumps(results[0], indent=2))
                    
                if len(valid_jobs) > 0:
                    logger.info(f"\n✅ FIRST VALID JOB:")
                    job = valid_jobs[0]
                    logger.info(f"  Title: {job.get('title', 'N/A')}")
                    logger.info(f"  Company: {job.get('company', 'N/A')}")
                    logger.info(f"  Location: {job.get('location', 'N/A')}")
                    logger.info(f"  URL: {job.get('url', 'N/A')}")
                    logger.info(f"  Posted: {job.get('posted_at', 'N/A')}")
                    logger.info(f"\n  All fields: {list(job.keys())}")
                
                if len(errors) > 0:
                    logger.warning(f"\n⚠️  FIRST ERROR:")
                    logger.warning(json.dumps(errors[0], indent=2))
                
                if len(results) == 0:
                    logger.warning(f"\n⚠️  EMPTY RESULTS!")
                    logger.warning("Bright Data returned an empty array")
                    logger.warning("This means:")
                    logger.warning("  1. No jobs found for this query")
                    logger.warning("  2. OR Indeed.be has no results")
                    logger.warning("  3. OR Bright Data scraper issue")
            
            return results
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        await client.close()
        logger.info("\n🔌 Client closed")

if __name__ == "__main__":
    logger.info("Starting Indeed raw data test...")
    results = asyncio.run(test_indeed_raw_data())
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 FINAL SUMMARY")
    logger.info("=" * 80)
    if isinstance(results, list):
        logger.info(f"Total items returned: {len(results)}")
        valid = [r for r in results if not r.get('error')]
        errors = [r for r in results if r.get('error')]
        logger.info(f"Valid jobs: {len(valid)}")
        logger.info(f"Errors: {len(errors)}")
    else:
        logger.info(f"Unexpected result type: {type(results)}")
    logger.info("=" * 80)
