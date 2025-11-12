#!/usr/bin/env python3
"""
Fix stuck runs with automatic retry mechanism.
- Detects runs stuck in 'running' status for >1 hour
- Schedules retry 4 hours later (up to 4 attempts)
- After 4 failed attempts, marks as permanently failed
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db


def fix_stuck_runs_with_retry(
    max_duration_hours: int = 1,
    retry_delay_hours: int = 4,
    max_retries: int = 4
):
    """
    Find and fix runs that have been stuck in 'running' status for too long.
    Implements automatic retry mechanism with exponential backoff.
    
    Args:
        max_duration_hours: Maximum allowed duration before considering a run stuck
        retry_delay_hours: Hours to wait before retrying
        max_retries: Maximum number of retry attempts (default 4)
    """
    logger.info("=" * 80)
    logger.info("FIXING STUCK SCRAPE RUNS WITH RETRY MECHANISM")
    logger.info("=" * 80)
    
    # Get all running runs
    result = db.client.table("scrape_runs")\
        .select("id, query_id, search_query, location_query, started_at, completed_at, retry_count")\
        .eq("status", "running")\
        .execute()
    
    if not result.data:
        logger.info("✅ No running runs found")
        return
    
    logger.info(f"Found {len(result.data)} running runs")
    
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=max_duration_hours)
    
    stats = {
        "completed": 0,
        "scheduled_retry": 0,
        "permanently_failed": 0,
        "still_running": 0
    }
    
    for run in result.data:
        run_id = run['id']
        query_id = run.get('query_id')
        query = run['search_query']
        location = run['location_query']
        started_at_str = run.get('started_at')
        completed_at = run.get('completed_at')
        retry_count = run.get('retry_count', 0)
        
        # If completed_at is set but status is still 'running', mark as completed
        if completed_at:
            logger.info(f"🔧 Fixing completed run: {query} in {location}")
            db.client.table("scrape_runs")\
                .update({"status": "completed"})\
                .eq("id", run_id)\
                .execute()
            stats["completed"] += 1
            continue
        
        # If no started_at, mark as failed
        if not started_at_str:
            logger.info(f"🔧 Fixing run with no start time: {query} in {location}")
            db.client.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "error_message": "Run never started properly",
                    "completed_at": now.isoformat()
                })\
                .eq("id", run_id)\
                .execute()
            stats["permanently_failed"] += 1
            continue
        
        # Parse started_at timestamp
        try:
            if started_at_str.endswith('+00:00'):
                if '.' in started_at_str:
                    parts = started_at_str.split('.')
                    microseconds = parts[1].replace('+00:00', '')
                    microseconds = microseconds.ljust(6, '0')[:6]
                    started_at_str = f"{parts[0]}.{microseconds}+00:00"
                started_at = datetime.fromisoformat(started_at_str)
            else:
                started_at = datetime.fromisoformat(started_at_str).replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.error(f"Failed to parse timestamp for run {run_id}: {e}")
            continue
        
        # Check if run has been running too long
        duration = now - started_at
        duration_hours = duration.total_seconds() / 3600
        
        if started_at < cutoff_time:
            logger.warning(f"⚠️  Stuck run detected: {query} in {location}")
            logger.warning(f"   Started: {started_at_str}")
            logger.warning(f"   Duration: {duration_hours:.1f} hours")
            logger.warning(f"   Retry count: {retry_count}/{max_retries}")
            
            # Check if we should retry or permanently fail
            if retry_count < max_retries:
                # Schedule retry
                next_retry_at = now + timedelta(hours=retry_delay_hours)
                
                # Mark current run as failed with retry scheduled
                db.client.table("scrape_runs")\
                    .update({
                        "status": "failed",
                        "error_message": f"Run stuck for {duration_hours:.1f}h - retry {retry_count + 1}/{max_retries} scheduled",
                        "completed_at": now.isoformat(),
                        "next_retry_at": next_retry_at.isoformat()
                    })\
                    .eq("id", run_id)\
                    .execute()
                
                # Create new run for retry
                new_run = {
                    "query_id": query_id,
                    "search_query": query,
                    "location_query": location,
                    "status": "pending_retry",
                    "retry_count": retry_count + 1,
                    "max_retries": max_retries,
                    "original_run_id": run_id,
                    "is_retry": True,
                    "next_retry_at": next_retry_at.isoformat(),
                    "created_at": now.isoformat()
                }
                
                db.client.table("scrape_runs")\
                    .insert(new_run)\
                    .execute()
                
                logger.success(f"✅ Retry {retry_count + 1}/{max_retries} scheduled for {next_retry_at.strftime('%H:%M')}")
                stats["scheduled_retry"] += 1
            else:
                # Permanently failed after max retries
                db.client.table("scrape_runs")\
                    .update({
                        "status": "failed",
                        "error_message": f"Run stuck for {duration_hours:.1f}h - permanently failed after {max_retries} attempts",
                        "completed_at": now.isoformat()
                    })\
                    .eq("id", run_id)\
                    .execute()
                
                logger.error(f"❌ Permanently failed after {max_retries} attempts: {query} in {location}")
                stats["permanently_failed"] += 1
        else:
            logger.info(f"⏳ Still running (OK): {query} in {location} ({duration_hours:.1f}h)")
            stats["still_running"] += 1
    
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Marked as completed: {stats['completed']}")
    logger.info(f"🔄 Scheduled for retry: {stats['scheduled_retry']}")
    logger.info(f"❌ Permanently failed: {stats['permanently_failed']}")
    logger.info(f"⏳ Still running (OK): {stats['still_running']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    fix_stuck_runs_with_retry(
        max_duration_hours=1,
        retry_delay_hours=4,
        max_retries=4
    )
