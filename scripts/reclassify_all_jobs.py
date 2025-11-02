#!/usr/bin/env python3
"""Reclassify ALL job titles (including already classified ones) using LLM v3."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.job_title_classifier import classify_and_save
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

def reclassify_all_jobs(batch_size=50):
    """Reclassify ALL jobs, including already classified ones."""
    try:
        # Get ALL jobs
        logger.info("Fetching all jobs...")
        all_jobs = db.client.table("job_postings")\
            .select("id, title")\
            .execute()
        
        if not all_jobs.data:
            logger.warning("No jobs found!")
            return 0
        
        total_jobs = len(all_jobs.data)
        logger.info(f"Found {total_jobs} jobs to reclassify")
        
        classified_count = 0
        
        # Process in batches
        for i in range(0, total_jobs, batch_size):
            batch = all_jobs.data[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_jobs + batch_size - 1)//batch_size} ({len(batch)} jobs)...")
            
            for job in batch:
                try:
                    classification = classify_and_save(job["id"], job["title"])
                    if classification:
                        classified_count += 1
                        logger.debug(f"  {job['title'][:50]:50} -> {classification}")
                except Exception as e:
                    logger.error(f"Failed to classify job {job['id']}: {e}")
            
            logger.info(f"Progress: {min(i+batch_size, total_jobs)}/{total_jobs} ({classified_count} successful)")
        
        return classified_count
        
    except Exception as e:
        logger.error(f"Failed to reclassify jobs: {e}")
        return 0

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("RECLASSIFY ALL JOB TITLES WITH LLM v3")
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
    
    # Confirm action
    logger.warning(f"⚠️  This will RECLASSIFY ALL {stats['total']} jobs using prompt v3!")
    logger.warning("   This may take 20-30 minutes and will overwrite existing classifications.")
    
    # Start reclassification
    logger.info("\nStarting reclassification in batches of 50...\n")
    
    total_classified = reclassify_all_jobs(batch_size=50)
    
    logger.info("\n" + "="*80)
    logger.success(f"✅ Done! Reclassified {total_classified} job titles.")
    
    # Show final stats
    logger.info("\n📊 Final Statistics:")
    stats = get_classification_stats()
    if stats:
        logger.info(f"  Total jobs: {stats['total']}")
        logger.info(f"  ✅ Classified as 'Data': {stats['data']} ({stats['data']/stats['total']*100:.1f}%)")
        logger.info(f"  ❌ Classified as 'NIS': {stats['nis']} ({stats['nis']/stats['total']*100:.1f}%)")
        logger.info(f"  ⏳ Unclassified: {stats['unclassified']}")
    logger.info("="*80)
