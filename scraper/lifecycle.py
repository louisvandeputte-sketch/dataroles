"""Job lifecycle management for tracking inactive jobs."""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID
from loguru import logger
from database.client import db


def mark_inactive_jobs(threshold_days: int = 14) -> int:
    """
    Mark jobs as inactive if they haven't been seen in threshold_days.
    
    This should be run periodically to keep job status up to date.
    
    Args:
        threshold_days: Number of days without being seen before marking inactive
    
    Returns:
        Count of jobs marked inactive
    """
    logger.info(f"Checking for jobs inactive for >{threshold_days} days")
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)
    
    # Query for jobs that are:
    # - Currently marked active
    # - Haven't been seen since cutoff_date
    query = db.client.table("job_postings")\
        .select("id")\
        .eq("is_active", True)\
        .lt("last_seen_at", cutoff_date.isoformat())\
        .execute()
    
    job_ids = [UUID(row["id"]) for row in query.data]
    
    if not job_ids:
        logger.info("No jobs to mark inactive")
        return 0
    
    # Mark jobs as inactive
    count = db.mark_jobs_inactive(job_ids)
    
    logger.success(f"Marked {count} jobs as inactive")
    return count


def get_inactive_jobs_summary() -> dict:
    """
    Get summary statistics about inactive jobs.
    
    Returns:
        Dictionary with inactive job counts by various dimensions
    """
    summary = {}
    
    # Total inactive jobs
    result = db.client.table("job_postings")\
        .select("id", count="exact")\
        .eq("is_active", False)\
        .execute()
    summary["total_inactive"] = result.count
    
    # Inactive in last 7 days
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    result = db.client.table("job_postings")\
        .select("id", count="exact")\
        .eq("is_active", False)\
        .gte("detected_inactive_at", week_ago)\
        .execute()
    summary["inactive_last_7_days"] = result.count
    
    # Inactive in last 30 days
    month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    result = db.client.table("job_postings")\
        .select("id", count="exact")\
        .eq("is_active", False)\
        .gte("detected_inactive_at", month_ago)\
        .execute()
    summary["inactive_last_30_days"] = result.count
    
    return summary
