#!/usr/bin/env python3
"""Classify job titles for all unclassified jobs using LLM."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.job_title_classifier import classify_unclassified_jobs
from database.client import db
from loguru import logger

def get_classification_stats():
    """Get statistics about job title classifications."""
    try:
        # Total jobs
        total = db.client.table("job_postings").select("id", count="exact").execute()
        
        # Classified as Data
        data_jobs = db.client.table("job_postings")\
            .select("id", count="exact")\
            .eq("title_classification", "Data")\
            .execute()
        
        # Classified as NIS
        nis_jobs = db.client.table("job_postings")\
            .select("id", count="exact")\
            .eq("title_classification", "NIS")\
            .execute()
        
        # Unclassified
        unclassified = db.client.table("job_postings")\
            .select("id", count="exact")\
            .is_("title_classification", "null")\
            .execute()
        
        return {
            "total": total.count,
            "data": data_jobs.count,
            "nis": nis_jobs.count,
            "unclassified": unclassified.count
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return None

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("CLASSIFY JOB TITLES WITH LLM")
    logger.info("="*80)
    
    # Show initial stats
    logger.info("\n📊 Initial Statistics:")
    stats = get_classification_stats()
    if stats:
        logger.info(f"  Total jobs: {stats['total']}")
        logger.info(f"  ✅ Classified as 'Data': {stats['data']}")
        logger.info(f"  ❌ Classified as 'NIS': {stats['nis']}")
        logger.info(f"  ⏳ Unclassified: {stats['unclassified']}")
        logger.info("")
    
    if stats and stats['unclassified'] == 0:
        logger.success("✅ All jobs are already classified!")
        sys.exit(0)
    
    # Classify in batches of 50 (slower but more reliable)
    total_classified = 0
    batch_size = 50
    
    logger.info(f"Starting classification in batches of {batch_size}...\n")
    
    while True:
        count = classify_unclassified_jobs(limit=batch_size)
        total_classified += count
        
        if count < batch_size:
            # No more jobs to classify
            break
        
        logger.info(f"Progress: {total_classified} jobs classified so far...")
    
    logger.info("\n" + "="*80)
    logger.success(f"✅ Done! Classified {total_classified} job titles.")
    
    # Show final stats
    logger.info("\n📊 Final Statistics:")
    stats = get_classification_stats()
    if stats:
        logger.info(f"  Total jobs: {stats['total']}")
        logger.info(f"  ✅ Classified as 'Data': {stats['data']} ({stats['data']/stats['total']*100:.1f}%)")
        logger.info(f"  ❌ Classified as 'NIS': {stats['nis']} ({stats['nis']/stats['total']*100:.1f}%)")
        logger.info(f"  ⏳ Unclassified: {stats['unclassified']}")
    logger.info("="*80)
