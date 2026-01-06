#!/usr/bin/env python3
"""
One-time script to re-enrich old Data jobs posted before 2025-12-05.

This script:
1. Queries all active Data jobs with posted_date < 2025-12-05
2. Re-enriches them using the same process as the nightly auto-enrichment
3. Includes proper error handling, rate limiting, and progress tracking
4. Saves detailed logs and statistics

Usage:
    python scripts/reenrich_old_data_jobs.py [--dry-run] [--limit N] [--batch-size N]

Options:
    --dry-run       Show what would be done without actually enriching
    --limit N       Limit to first N jobs (default: no limit, process all)
    --batch-size N  Number of jobs to process in each batch (default: 50)
    --delay SECS    Delay between jobs in seconds (default: 1.5)
    --force         Force re-enrichment even if already enriched
    --skip-errors   Skip jobs that already have enrichment errors

Examples:
    # Dry run to see how many jobs would be processed
    python scripts/reenrich_old_data_jobs.py --dry-run

    # Process first 10 jobs as a test
    python scripts/reenrich_old_data_jobs.py --limit 10

    # Process all jobs with 2 second delay between each
    python scripts/reenrich_old_data_jobs.py --delay 2.0

    # Force re-enrich all jobs (even if already enriched)
    python scripts/reenrich_old_data_jobs.py --force
"""

import sys
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db
from ingestion.llm_enrichment import process_job_enrichment


class ReEnrichmentStats:
    """Track statistics for re-enrichment process."""
    
    def __init__(self):
        self.total_jobs = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.rate_limited = 0
        self.errors: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
    
    def add_success(self):
        self.successful += 1
    
    def add_failure(self, job_id: str, title: str, error: str):
        self.failed += 1
        self.errors.append({
            "job_id": job_id,
            "title": title,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        if "rate limit" in error.lower() or "quota" in error.lower():
            self.rate_limited += 1
    
    def add_skip(self):
        self.skipped += 1
    
    def get_duration(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def print_summary(self):
        """Print summary statistics."""
        duration = self.get_duration()
        logger.info("=" * 80)
        logger.info("RE-ENRICHMENT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total jobs processed: {self.total_jobs}")
        logger.info(f"✅ Successful: {self.successful}")
        logger.info(f"⏭️  Skipped: {self.skipped}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"⚠️  Rate limited: {self.rate_limited}")
        logger.info(f"⏱️  Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        
        if self.successful > 0:
            avg_time = duration / self.successful
            logger.info(f"📊 Average time per job: {avg_time:.1f}s")
        
        if self.errors:
            logger.warning(f"\n❌ First 5 errors:")
            for i, error in enumerate(self.errors[:5], 1):
                logger.warning(f"  {i}. {error['title']}: {error['error']}")
        
        logger.info("=" * 80)


def get_old_data_jobs(
    cutoff_date: str = "2025-12-05",
    skip_errors: bool = False,
    skip_enriched_after: str = None
) -> List[Dict[str, Any]]:
    """
    Get all active Data jobs posted before the cutoff date.
    
    Args:
        cutoff_date: ISO date string (YYYY-MM-DD) - jobs posted before this date
        skip_errors: If True, skip jobs that already have enrichment errors
        skip_enriched_after: ISO datetime string - skip jobs enriched after this time
                            (prevents re-enriching jobs already processed in this run)
    
    Returns:
        List of job dicts with id, title, posted_date, enrichment status
    """
    logger.info(f"Querying jobs with posted_date < {cutoff_date} and title_classification = 'Data'...")
    
    try:
        # Get all matching jobs
        result = db.client.table("job_postings")\
            .select("id, title, posted_date, company_id")\
            .eq("title_classification", "Data")\
            .eq("is_active", True)\
            .lt("posted_date", cutoff_date)\
            .order("posted_date", desc=False)\
            .execute()
        
        if not result.data:
            logger.warning("No jobs found matching criteria")
            return []
        
        job_ids = [j["id"] for j in result.data]
        logger.info(f"Found {len(job_ids)} jobs matching criteria")
        
        # Get enrichment status for these jobs (in batches to avoid query size limits)
        enrichment_map = {}
        batch_size = 100
        for i in range(0, len(job_ids), batch_size):
            batch_ids = job_ids[i:i+batch_size]
            logger.debug(f"Fetching enrichment status for batch {i//batch_size + 1} ({len(batch_ids)} jobs)")
            
            enrichments = db.client.table("llm_enrichment")\
                .select("job_posting_id, enrichment_completed_at, enrichment_error")\
                .in_("job_posting_id", batch_ids)\
                .execute()
            
            # Add to enrichment map
            for e in enrichments.data:
                enrichment_map[e["job_posting_id"]] = {
                    "completed": e.get("enrichment_completed_at"),
                    "error": e.get("enrichment_error")
                }
        
        # Combine job data with enrichment status
        jobs = []
        for job in result.data:
            job_id = job["id"]
            enrich_status = enrichment_map.get(job_id, {})
            
            # Skip jobs with errors if requested
            if skip_errors and enrich_status.get("error"):
                logger.debug(f"Skipping {job['title']} - has enrichment error")
                continue
            
            # Skip jobs that were enriched after the cutoff (already processed in this run)
            if skip_enriched_after and enrich_status.get("completed"):
                enriched_at = enrich_status.get("completed")
                if enriched_at > skip_enriched_after:
                    logger.debug(f"Skipping {job['title']} - already re-enriched after {skip_enriched_after}")
                    continue
            
            jobs.append({
                "id": job_id,
                "title": job["title"],
                "posted_date": job["posted_date"],
                "company_id": job["company_id"],
                "enriched": bool(enrich_status.get("completed")),
                "enriched_at": enrich_status.get("completed"),
                "has_error": bool(enrich_status.get("error")),
                "error": enrich_status.get("error")
            })
        
        # Log statistics
        enriched_count = sum(1 for j in jobs if j["enriched"])
        error_count = sum(1 for j in jobs if j["has_error"])
        unenriched_count = len(jobs) - enriched_count
        
        logger.info(f"Job breakdown:")
        logger.info(f"  - Already enriched: {enriched_count}")
        logger.info(f"  - Not enriched: {unenriched_count}")
        logger.info(f"  - Has errors: {error_count}")
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to query jobs: {e}")
        import traceback
        traceback.print_exc()
        return []


def reenrich_jobs_batch(
    jobs: List[Dict[str, Any]],
    force: bool = False,
    delay: float = 1.5,
    dry_run: bool = False
) -> ReEnrichmentStats:
    """
    Re-enrich a batch of jobs.
    
    Args:
        jobs: List of job dicts to enrich
        force: If True, re-enrich even if already enriched
        delay: Delay in seconds between jobs
        dry_run: If True, don't actually enrich, just simulate
    
    Returns:
        ReEnrichmentStats object with results
    """
    stats = ReEnrichmentStats()
    stats.total_jobs = len(jobs)
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual enrichment will be performed")
    
    logger.info(f"Starting re-enrichment of {len(jobs)} jobs...")
    logger.info(f"Settings: force={force}, delay={delay}s, dry_run={dry_run}")
    
    for i, job in enumerate(jobs, 1):
        job_id = job["id"]
        title = job["title"]
        enriched = job["enriched"]
        has_error = job["has_error"]
        
        # Progress indicator
        progress = f"[{i}/{len(jobs)}]"
        
        # Determine action
        if enriched and not force:
            logger.info(f"{progress} ⏭️  Skipping (already enriched): {title}")
            stats.add_skip()
            continue
        
        if has_error:
            logger.info(f"{progress} 🔄 Re-enriching (had error): {title}")
        elif enriched and force:
            logger.info(f"{progress} 🔄 Force re-enriching: {title}")
        else:
            logger.info(f"{progress} 🆕 Enriching (not yet enriched): {title}")
        
        if dry_run:
            logger.info(f"{progress} 🔍 [DRY RUN] Would enrich: {title}")
            stats.add_success()
            time.sleep(0.1)  # Small delay for dry run
            continue
        
        # Actual enrichment
        try:
            result = process_job_enrichment(job_id, force=force)
            
            if result.get("success"):
                if result.get("skipped"):
                    logger.info(f"{progress} ⏭️  Skipped (already enriched): {title}")
                    stats.add_skip()
                else:
                    logger.success(f"{progress} ✅ Successfully enriched: {title}")
                    stats.add_success()
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"{progress} ❌ Failed to enrich: {title} - {error}")
                stats.add_failure(job_id, title, error)
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{progress} ❌ Exception during enrichment: {title} - {error_msg}")
            stats.add_failure(job_id, title, error_msg)
        
        # Rate limiting delay (except for last job)
        if i < len(jobs):
            logger.debug(f"Waiting {delay}s before next job...")
            time.sleep(delay)
        
        # Print interim stats every 10 jobs
        if i % 10 == 0:
            elapsed = stats.get_duration()
            logger.info(f"Progress: {i}/{len(jobs)} jobs | {stats.successful} successful | {stats.failed} failed | {elapsed:.0f}s elapsed")
    
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-enrich old Data jobs posted before 2025-12-05",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually enriching"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit to first N jobs (default: process all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=300,
        help="Number of jobs to process in each batch (default: 300)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay between jobs in seconds (default: 1.5)"
    )
    parser.add_argument(
        "--no-force",
        action="store_true",
        help="Do NOT force re-enrichment (skip already enriched jobs). Default is to FORCE re-enrich all old jobs."
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Skip jobs that already have enrichment errors"
    )
    parser.add_argument(
        "--cutoff-date",
        type=str,
        default="2025-12-05",
        help="Cutoff date for jobs to re-enrich (default: 2025-12-05)"
    )
    parser.add_argument(
        "--skip-enriched-after",
        type=str,
        default=None,
        help="Skip jobs enriched after this datetime (ISO format, e.g. 2026-01-06T18:00:00). "
             "Use this to avoid re-enriching jobs already processed in a previous run."
    )
    
    args = parser.parse_args()
    
    # Default behavior: FORCE re-enrich old jobs (unless --no-force is specified)
    args.force = not args.no_force
    
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Add file logger
    log_file = f"reenrich_old_jobs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG"
    )
    
    logger.info("=" * 80)
    logger.info("RE-ENRICHMENT SCRIPT FOR OLD DATA JOBS")
    logger.info("=" * 80)
    logger.info(f"Cutoff date: {args.cutoff_date}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Force re-enrich: {args.force} (default for old jobs)")
    logger.info(f"Skip errors: {args.skip_errors}")
    logger.info(f"Limit: {args.limit or 'None (process all)'}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Delay: {args.delay}s")
    logger.info(f"Log file: {log_file}")
    if args.skip_enriched_after:
        logger.info(f"Skip enriched after: {args.skip_enriched_after}")
    logger.info("=" * 80)
    
    # Get jobs to process
    jobs = get_old_data_jobs(
        cutoff_date=args.cutoff_date,
        skip_errors=args.skip_errors,
        skip_enriched_after=args.skip_enriched_after
    )
    
    if not jobs:
        logger.warning("No jobs to process. Exiting.")
        return
    
    # Apply limit if specified
    if args.limit:
        original_count = len(jobs)
        jobs = jobs[:args.limit]
        logger.info(f"Limited to first {args.limit} jobs (out of {original_count} total)")
    
    # Confirm before proceeding (unless dry-run)
    if not args.dry_run:
        logger.warning(f"\n⚠️  About to re-enrich {len(jobs)} jobs. This will:")
        logger.warning(f"   - Make LLM API calls (costs money)")
        logger.warning(f"   - Take approximately {len(jobs) * args.delay / 60:.1f} minutes")
        if args.force:
            logger.warning(f"   - FORCE re-enrich ALL jobs (overwrite existing enrichments)")
        else:
            logger.warning(f"   - Only enrich jobs that are not yet enriched")
        
        response = input("\nProceed? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            logger.info("Cancelled by user. Exiting.")
            return
    
    # Process in batches
    all_stats = ReEnrichmentStats()
    all_stats.total_jobs = len(jobs)
    
    for batch_start in range(0, len(jobs), args.batch_size):
        batch_end = min(batch_start + args.batch_size, len(jobs))
        batch = jobs[batch_start:batch_end]
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Processing batch {batch_start // args.batch_size + 1}: jobs {batch_start + 1}-{batch_end}")
        logger.info(f"{'=' * 80}\n")
        
        batch_stats = reenrich_jobs_batch(
            batch,
            force=args.force,
            delay=args.delay,
            dry_run=args.dry_run
        )
        
        # Aggregate stats
        all_stats.successful += batch_stats.successful
        all_stats.failed += batch_stats.failed
        all_stats.skipped += batch_stats.skipped
        all_stats.rate_limited += batch_stats.rate_limited
        all_stats.errors.extend(batch_stats.errors)
        
        # Print batch summary
        logger.info(f"\nBatch complete: {batch_stats.successful} successful, {batch_stats.failed} failed, {batch_stats.skipped} skipped")
        
        # Pause between batches (except for last batch)
        if batch_end < len(jobs):
            pause_time = 5
            logger.info(f"Pausing {pause_time}s before next batch...")
            time.sleep(pause_time)
    
    # Print final summary
    logger.info("\n")
    all_stats.print_summary()
    
    # Save error log if there were errors
    if all_stats.errors:
        error_log_file = f"reenrich_errors_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        with open(error_log_file, 'w') as f:
            f.write("RE-ENRICHMENT ERRORS\n")
            f.write("=" * 80 + "\n\n")
            for error in all_stats.errors:
                f.write(f"Job ID: {error['job_id']}\n")
                f.write(f"Title: {error['title']}\n")
                f.write(f"Error: {error['error']}\n")
                f.write(f"Timestamp: {error['timestamp']}\n")
                f.write("-" * 80 + "\n")
        logger.info(f"Error details saved to: {error_log_file}")
    
    logger.info(f"Complete log saved to: {log_file}")


if __name__ == "__main__":
    main()
