#!/usr/bin/env python3
"""
Debug script to test Indeed scraping and see what Bright Data returns
"""

import asyncio
import sys
sys.path.insert(0, '.')

from clients.brightdata_indeed import BrightDataIndeedClient
from config.settings import settings
from loguru import logger

async def test_indeed_scrape():
    """Test Indeed scraping with Data Engineer query"""
    
    logger.info("🧪 Testing Indeed scrape for 'Data Engineer' in 'Belgium'")
    
    # Initialize client
    client = BrightDataIndeedClient(
        api_token=settings.BRIGHTDATA_API_TOKEN,
        dataset_id=settings.BRIGHTDATA_INDEED_DATASET_ID
    )
    
    try:
        # Trigger collection
        logger.info("📡 Triggering collection...")
        snapshot_id = await client.trigger_collection(
            keyword="Data Engineer",
            location="Belgium",
            posted_date_range="past_week",
            limit=1000
        )
        
        logger.info(f"✅ Collection triggered! Snapshot ID: {snapshot_id}")
        
        # Wait for completion
        logger.info("⏳ Waiting for snapshot to complete...")
        await client.wait_for_completion(snapshot_id)
        
        logger.info("✅ Snapshot completed!")
        
        # Download results
        logger.info("📥 Downloading results...")
        results = await client.download_results(snapshot_id)
        
        logger.info(f"📊 Results: {len(results)} jobs returned")
        
        if len(results) == 0:
            logger.warning("⚠️  0 jobs returned from Bright Data!")
            logger.info("This could mean:")
            logger.info("  1. Indeed Belgium has no 'Data Engineer' jobs posted in past week")
            logger.info("  2. Bright Data API parameters are incorrect")
            logger.info("  3. Bright Data is having issues")
        else:
            logger.success(f"✅ {len(results)} jobs found!")
            logger.info("First job:")
            logger.info(f"  Title: {results[0].get('title', 'N/A')}")
            logger.info(f"  Company: {results[0].get('company', 'N/A')}")
            logger.info(f"  Location: {results[0].get('location', 'N/A')}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        raise
    finally:
        await client.close()

if __name__ == "__main__":
    results = asyncio.run(test_indeed_scrape())
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(results)} jobs returned")
    print("=" * 80)
