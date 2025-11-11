#!/usr/bin/env python3
"""Re-classify all job titles, including those that previously failed or were auto-filled."""

from database.client import db
from ingestion.job_title_classifier import classify_and_save
from loguru import logger
import time

def reclassify_all_jobs(batch_size: int = 1000, delay_seconds: float = 1.0):
    """
    Re-classify all job titles in the database.
    
    Args:
        batch_size: Number of jobs to fetch per batch from database
        delay_seconds: Delay between API calls to avoid rate limiting
    """
    try:
        # Get total count first
        logger.info("🔍 Counting total jobs...")
        count_result = db.client.table("job_postings")\
            .select("id", count="exact")\
            .execute()
        
        total_jobs = count_result.count if hasattr(count_result, 'count') else 0
        logger.info(f"📊 Total jobs in database: {total_jobs}")
        
        # Process ALL jobs in batches
        all_jobs = []
        offset = 0
        
        logger.info(f"🔍 Fetching all jobs in batches of {batch_size}...")
        
        while True:
            # Fetch batch
            result = db.client.table("job_postings")\
                .select("id, title, title_classification, title_classification_error")\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            batch = result.data if result.data else []
            
            if not batch:
                break  # No more jobs
            
            all_jobs.extend(batch)
            offset += batch_size
            
            logger.info(f"   Fetched {len(all_jobs)} jobs so far...")
            
            if len(batch) < batch_size:
                break  # Last batch
        
        jobs = all_jobs
        
        if not jobs:
            logger.info("✅ No jobs need classification")
            return
        
        logger.info(f"📊 Found {len(jobs)} jobs to classify")
        
        # Show breakdown
        unclassified = sum(1 for j in jobs if not j.get('title_classification'))
        with_errors = sum(1 for j in jobs if j.get('title_classification_error'))
        
        logger.info(f"   - Unclassified: {unclassified}")
        logger.info(f"   - With errors: {with_errors}")
        
        # Process in batches
        total = len(jobs)
        success_count = 0
        error_count = 0
        
        for i, job in enumerate(jobs, 1):
            job_id = job["id"]
            job_title = job["title"]
            
            logger.info(f"[{i}/{total}] Classifying: {job_title[:60]}...")
            
            try:
                classification = classify_and_save(job_id, job_title)
                
                if classification:
                    success_count += 1
                    logger.success(f"   ✅ {classification}")
                else:
                    error_count += 1
                    logger.warning(f"   ⚠️ Failed (error saved to DB)")
                
                # Delay to avoid rate limiting
                if i < total:  # Don't delay after last item
                    time.sleep(delay_seconds)
                
            except Exception as e:
                error_count += 1
                logger.error(f"   ❌ Exception: {e}")
                continue
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.success(f"✅ Classification complete!")
        logger.info(f"   Total processed: {total}")
        logger.info(f"   Successful: {success_count}")
        logger.info(f"   Failed: {error_count}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to reclassify jobs: {e}")


if __name__ == "__main__":
    logger.info("🚀 Starting job title re-classification")
    logger.info("=" * 80)
    
    # You can adjust these parameters:
    # - batch_size: not used in current implementation but kept for future batching
    # - delay_seconds: delay between API calls (1.0 = 1 second)
    
    reclassify_all_jobs(batch_size=50, delay_seconds=1.0)
    
    logger.info("\n✅ Done!")
