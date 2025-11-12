#!/usr/bin/env python3
"""
Enrich all Data jobs that don't have LLM enrichment yet.
Runs in batches with rate limiting to avoid API overload.
"""

import sys
from pathlib import Path
import time
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db
from ingestion.llm_enrichment import enrich_job_with_llm, save_enrichment_to_db


def get_unenriched_data_jobs(limit: int = 1000):
    """
    Get Data jobs that haven't been enriched yet.
    
    Args:
        limit: Maximum number of jobs to fetch
        
    Returns:
        List of job dictionaries with descriptions
    """
    logger.info(f"Fetching up to {limit} unenriched Data jobs...")
    
    # Get all Data jobs with their descriptions
    # We'll check enrichment status individually to avoid large NOT IN queries
    result = db.client.table("job_postings")\
        .select("id, title")\
        .eq("title_classification", "Data")\
        .eq("is_active", True)\
        .limit(limit * 2)\
        .execute()
    
    all_jobs = result.data if result.data else []
    logger.info(f"Found {len(all_jobs)} active Data jobs")
    
    # Filter out enriched jobs and get descriptions
    jobs_with_descriptions = []
    
    for job in all_jobs:
        if len(jobs_with_descriptions) >= limit:
            break
            
        job_id = job["id"]
        
        # Check if already enriched (completed_at must be set)
        enrich_check = db.client.table("llm_enrichment")\
            .select("enrichment_completed_at")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        # Skip if enrichment is completed (not null)
        if enrich_check.data and enrich_check.data[0].get("enrichment_completed_at"):
            continue
        
        # Get description
        desc_result = db.client.table("job_descriptions")\
            .select("full_description_text")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        if desc_result.data and desc_result.data[0].get("full_description_text"):
            job["description"] = desc_result.data[0]["full_description_text"]
            jobs_with_descriptions.append(job)
    
    logger.info(f"Found {len(jobs_with_descriptions)} unenriched Data jobs with descriptions")
    
    return jobs_with_descriptions


def enrich_data_jobs_batch(
    batch_size: int = 10,
    delay_seconds: int = 2,
    max_jobs: int = None,
    skip_confirmation: bool = False
):
    """
    Enrich Data jobs in batches with rate limiting.
    
    Args:
        batch_size: Number of jobs to process in each batch
        delay_seconds: Seconds to wait between each job
        max_jobs: Maximum total jobs to enrich (None = all)
        skip_confirmation: Skip user confirmation
    """
    logger.info("=" * 80)
    logger.info("ENRICHING DATA JOBS WITH LLM")
    logger.info("=" * 80)
    
    # Get unenriched jobs
    limit = max_jobs if max_jobs else 1000
    jobs = get_unenriched_data_jobs(limit=limit)
    
    if not jobs:
        logger.info("✅ No unenriched Data jobs found!")
        return
    
    total_jobs = len(jobs)
    if max_jobs:
        total_jobs = min(total_jobs, max_jobs)
        jobs = jobs[:max_jobs]
    
    logger.info(f"📊 Will enrich {total_jobs} Data jobs")
    logger.info(f"⏱️  Delay: {delay_seconds}s between jobs")
    logger.info(f"📦 Batch size: {batch_size}")
    logger.info(f"⏳ Estimated time: ~{(total_jobs * delay_seconds) / 60:.1f} minutes")
    
    # Confirm before proceeding
    if not skip_confirmation:
        print("\n" + "=" * 80)
        print(f"⚠️  This will enrich {total_jobs} jobs using OpenAI API")
        print(f"💰 Estimated cost: ~${total_jobs * 0.01:.2f} (rough estimate)")
        print("=" * 80)
        confirm = input("\nProceed? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            logger.info("❌ Cancelled by user")
            return
    
    # Process jobs
    stats = {
        "total": total_jobs,
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    logger.info("\n" + "=" * 80)
    logger.info("STARTING ENRICHMENT")
    logger.info("=" * 80 + "\n")
    
    for i, job in enumerate(jobs, 1):
        job_id = job["id"]
        title = job.get("title", "Unknown")
        description = job.get("description", "")
        
        logger.info(f"[{i}/{total_jobs}] Enriching: {title}")
        
        try:
            # Enrich with LLM
            enrichment_data, error = enrich_job_with_llm(job_id, description)
            
            if enrichment_data:
                # Save to database
                success = save_enrichment_to_db(job_id, enrichment_data)
                
                if success:
                    stats["successful"] += 1
                    logger.success(f"✅ [{i}/{total_jobs}] Enriched: {title}")
                else:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "job_id": job_id,
                        "title": title,
                        "error": "Failed to save to database"
                    })
                    logger.error(f"❌ [{i}/{total_jobs}] Failed to save: {title}")
            else:
                stats["failed"] += 1
                stats["errors"].append({
                    "job_id": job_id,
                    "title": title,
                    "error": error or "Unknown error"
                })
                logger.error(f"❌ [{i}/{total_jobs}] Failed: {title} - {error}")
            
            # Rate limiting
            if i < total_jobs:
                time.sleep(delay_seconds)
                
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append({
                "job_id": job_id,
                "title": title,
                "error": str(e)
            })
            logger.error(f"❌ [{i}/{total_jobs}] Exception: {title} - {e}")
            
            # Continue with rate limiting
            if i < total_jobs:
                time.sleep(delay_seconds)
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("ENRICHMENT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"✅ Successful: {stats['successful']}")
    logger.info(f"❌ Failed: {stats['failed']}")
    logger.info(f"📊 Success rate: {(stats['successful'] / stats['total'] * 100):.1f}%")
    
    if stats["errors"]:
        logger.info("\n" + "=" * 80)
        logger.info("ERRORS")
        logger.info("=" * 80)
        for error in stats["errors"][:10]:  # Show first 10 errors
            logger.error(f"Job: {error['title']}")
            logger.error(f"Error: {error['error']}")
            logger.error("-" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enrich Data jobs with LLM"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of jobs per batch (default: 10)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=2,
        help="Seconds between jobs (default: 2)"
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Maximum jobs to enrich (default: all)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    enrich_data_jobs_batch(
        batch_size=args.batch_size,
        delay_seconds=args.delay,
        max_jobs=args.max_jobs,
        skip_confirmation=args.yes
    )
