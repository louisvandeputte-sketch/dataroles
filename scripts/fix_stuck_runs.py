#!/usr/bin/env python3
"""
Fix stuck runs that have been running for more than 1 hour.
Marks them as 'failed' with an appropriate error message.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db


def fix_stuck_runs(max_duration_hours: int = 1):
    """
    Find and fix runs that have been stuck in 'running' status for too long.
    
    Args:
        max_duration_hours: Maximum allowed duration in hours before considering a run stuck
    """
    logger.info("=" * 80)
    logger.info("FIXING STUCK SCRAPE RUNS")
    logger.info("=" * 80)
    
    # Get all running runs
    result = db.client.table("scrape_runs")\
        .select("id, search_query, location_query, started_at, completed_at")\
        .eq("status", "running")\
        .execute()
    
    if not result.data:
        logger.info("✅ No running runs found")
        return
    
    logger.info(f"Found {len(result.data)} running runs")
    
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=max_duration_hours)
    
    fixed_count = 0
    still_running_count = 0
    
    for run in result.data:
        run_id = run['id']
        query = run['search_query']
        location = run['location_query']
        started_at_str = run.get('started_at')
        completed_at = run.get('completed_at')
        
        # If completed_at is set but status is still 'running', mark as completed
        if completed_at:
            logger.info(f"🔧 Fixing completed run: {query} in {location}")
            db.client.table("scrape_runs")\
                .update({"status": "completed"})\
                .eq("id", run_id)\
                .execute()
            fixed_count += 1
            continue
        
        # If no started_at, mark as failed
        if not started_at_str:
            logger.info(f"🔧 Fixing run with no start time: {query} in {location}")
            db.client.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "error_message": "Run never started properly"
                })\
                .eq("id", run_id)\
                .execute()
            fixed_count += 1
            continue
        
        # Parse started_at timestamp
        try:
            # Handle both formats: with and without timezone
            # Also handle microseconds with varying precision (e.g., .65 vs .963195)
            if started_at_str.endswith('+00:00'):
                # Normalize microseconds to 6 digits if needed
                if '.' in started_at_str:
                    parts = started_at_str.split('.')
                    microseconds = parts[1].replace('+00:00', '')
                    # Pad or truncate to 6 digits
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
            
            # Mark as failed
            db.client.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "error_message": f"Run stuck for {duration_hours:.1f} hours - automatically marked as failed",
                    "completed_at": now.isoformat()
                })\
                .eq("id", run_id)\
                .execute()
            
            logger.success(f"✅ Marked as failed: {query} in {location}")
            fixed_count += 1
        else:
            logger.info(f"⏳ Still running (OK): {query} in {location} ({duration_hours:.1f}h)")
            still_running_count += 1
    
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Fixed: {fixed_count}")
    logger.info(f"⏳ Still running (within time limit): {still_running_count}")
    logger.info("=" * 80)


if __name__ == "__main__":
    fix_stuck_runs(max_duration_hours=1)
