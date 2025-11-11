"""
Batch enrichment script for all Data jobs.
Processes jobs in batches of 50 to avoid overwhelming the API.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path to import from project
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db
from ingestion.llm_enrichment import process_job_enrichment

# Configuration
BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 5  # seconds
DELAY_BETWEEN_JOBS = 1  # seconds


def get_data_jobs_to_enrich():
    """
    Get all Data jobs for enrichment.
    Returns ALL jobs where:
    - title_classification = 'Data'
    - is_active = true
    
    Note: This will re-enrich ALL jobs, overwriting existing enrichment data.
    """
    try:
        # Get all active Data jobs
        result = db.client.table("job_postings")\
            .select("id, title, company_id")\
            .eq("title_classification", "Data")\
            .eq("is_active", True)\
            .execute()
        
        if not result.data:
            logger.info("No Data jobs found")
            return []
        
        all_jobs = result.data
        logger.info(f"Found {len(all_jobs)} active Data jobs to enrich")
        
        return all_jobs
        
    except Exception as e:
        logger.error(f"Failed to get jobs: {e}")
        return []


def enrich_batch(jobs, batch_num, total_batches):
    """
    Enrich a batch of jobs with force=True (always overwrite existing enrichment).
    
    Args:
        jobs: List of job dicts with 'id' and 'title'
        batch_num: Current batch number
        total_batches: Total number of batches
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing batch {batch_num}/{total_batches} ({len(jobs)} jobs)")
    logger.info(f"{'='*60}\n")
    
    successful = 0
    failed = 0
    
    for i, job in enumerate(jobs, 1):
        job_id = job["id"]
        job_title = job.get("title", "Unknown")
        
        logger.info(f"[{i}/{len(jobs)}] Processing: {job_title[:50]}...")
        
        try:
            # Always use force=True to overwrite existing enrichment
            result = process_job_enrichment(job_id, force=True)
            
            if result["success"]:
                logger.success(f"✅ Enriched: {job_title[:50]}")
                successful += 1
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"❌ Failed: {job_title[:50]} - {error}")
                failed += 1
            
            # Delay between jobs to avoid rate limits
            if i < len(jobs):
                time.sleep(DELAY_BETWEEN_JOBS)
                
        except Exception as e:
            logger.error(f"❌ Error processing {job_title[:50]}: {e}")
            failed += 1
    
    logger.info(f"\nBatch {batch_num} complete: {successful} successful, {failed} failed")
    return successful, failed


def main():
    """
    Main enrichment workflow.
    
    This script will RE-ENRICH ALL active Data jobs, overwriting existing enrichment data.
    """
    logger.info("="*60)
    logger.info("BATCH ENRICHMENT SCRIPT FOR DATA JOBS")
    logger.info("="*60)
    logger.info(f"Batch size: {BATCH_SIZE}")
    logger.info(f"Mode: FORCE RE-ENRICH (overwrites existing data)")
    logger.info(f"Delay between batches: {DELAY_BETWEEN_BATCHES}s")
    logger.info(f"Delay between jobs: {DELAY_BETWEEN_JOBS}s")
    logger.info("="*60 + "\n")
    
    # Get all jobs to enrich
    jobs = get_data_jobs_to_enrich()
    
    if not jobs:
        logger.info("No jobs to enrich. Exiting.")
        return
    
    # Calculate batches
    total_jobs = len(jobs)
    total_batches = (total_jobs + BATCH_SIZE - 1) // BATCH_SIZE
    
    logger.info(f"Total jobs to process: {total_jobs}")
    logger.info(f"Total batches: {total_batches}\n")
    
    # Confirm before starting
    logger.warning("⚠️  WARNING: This will OVERWRITE all existing enrichment data for these jobs!")
    response = input(f"\nStart enrichment of {total_jobs} jobs in {total_batches} batches? (y/n): ")
    if response.lower() != 'y':
        logger.info("Cancelled by user")
        return
    
    # Process in batches
    total_successful = 0
    total_failed = 0
    
    start_time = time.time()
    
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_jobs)
        batch = jobs[start_idx:end_idx]
        
        successful, failed = enrich_batch(batch, batch_num + 1, total_batches)
        
        total_successful += successful
        total_failed += failed
        
        # Delay between batches (except after last batch)
        if batch_num < total_batches - 1:
            logger.info(f"\nWaiting {DELAY_BETWEEN_BATCHES}s before next batch...\n")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    # Final summary
    elapsed_time = time.time() - start_time
    
    logger.info("\n" + "="*60)
    logger.info("ENRICHMENT COMPLETE")
    logger.info("="*60)
    logger.info(f"Total jobs processed: {total_jobs}")
    logger.info(f"Successful: {total_successful}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Time elapsed: {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
    logger.info(f"Average time per job: {elapsed_time/total_jobs:.1f}s")
    logger.info("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user. Exiting gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
