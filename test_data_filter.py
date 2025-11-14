#!/usr/bin/env python3
"""
Test if Data Only filter works correctly
"""
from loguru import logger
from database.client import db

if __name__ == "__main__":
    logger.info("Testing Data Only filter...")
    
    # Test 1: Get all active jobs
    all_jobs, total_all = db.search_jobs(
        active_only=True,
        limit=10
    )
    
    logger.info(f"\n📊 All active jobs (first 10):")
    for job in all_jobs:
        classification = job.get('title_classification', 'None')
        title = job.get('title', '')[:50]
        logger.info(f"  {classification:4} | {title}")
    
    # Test 2: Get only Data jobs
    data_jobs, total_data = db.search_jobs(
        active_only=True,
        title_classification='Data',
        limit=10
    )
    
    logger.info(f"\n📊 Data Only jobs (first 10):")
    for job in data_jobs:
        classification = job.get('title_classification', 'None')
        title = job.get('title', '')[:50]
        logger.info(f"  {classification:4} | {title}")
    
    logger.info(f"\n✅ Total active jobs: {total_all}")
    logger.info(f"✅ Total Data jobs: {total_data}")
