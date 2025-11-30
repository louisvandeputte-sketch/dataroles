"""
Auto-archive old scrape runs
Archives completed/failed runs older than 2 days
"""

from datetime import datetime, timedelta
from loguru import logger
from database.client import db


def archive_old_runs(days_threshold: int = 2) -> int:
    """
    Archive scrape runs older than the specified number of days.
    
    Args:
        days_threshold: Number of days after which to archive runs (default: 2)
        
    Returns:
        Number of runs archived
    """
    logger.info(f"🗄️ Archiving scrape runs older than {days_threshold} days...")
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        cutoff_iso = cutoff_date.isoformat()
        
        logger.info(f"   Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Find runs to archive:
        # - completed_at is older than cutoff (for completed runs)
        # - OR started_at is older than cutoff and status is failed (for failed runs without completed_at)
        # - AND not already archived
        
        # Get completed runs older than cutoff
        completed_runs = db.client.table("scrape_runs")\
            .select("id, search_query, location_query, platform, completed_at")\
            .eq("archived", False)\
            .eq("status", "completed")\
            .lt("completed_at", cutoff_iso)\
            .execute()
        
        # Get failed runs older than cutoff
        failed_runs = db.client.table("scrape_runs")\
            .select("id, search_query, location_query, platform, started_at")\
            .eq("archived", False)\
            .eq("status", "failed")\
            .lt("started_at", cutoff_iso)\
            .execute()
        
        # Combine all runs to archive
        runs_to_archive = completed_runs.data + failed_runs.data
        
        if not runs_to_archive:
            logger.info("   ✅ No runs to archive")
            return 0
        
        logger.info(f"   Found {len(runs_to_archive)} runs to archive:")
        logger.info(f"      - Completed: {len(completed_runs.data)}")
        logger.info(f"      - Failed: {len(failed_runs.data)}")
        
        # Archive each run
        archived_count = 0
        for run in runs_to_archive:
            try:
                db.client.table("scrape_runs")\
                    .update({"archived": True})\
                    .eq("id", run["id"])\
                    .execute()
                
                archived_count += 1
                
                # Log first 5 for visibility
                if archived_count <= 5:
                    platform = run.get("platform", "linkedin")
                    query = run.get("search_query", "N/A")
                    location = run.get("location_query", "N/A")
                    date = run.get("completed_at") or run.get("started_at")
                    logger.info(f"      ✓ Archived: {platform} | {query} in {location} ({date[:10]})")
                
            except Exception as e:
                logger.error(f"      ✗ Failed to archive run {run['id']}: {e}")
        
        if archived_count > 5:
            logger.info(f"      ... and {archived_count - 5} more")
        
        logger.success(f"✅ Archived {archived_count} scrape runs")
        return archived_count
        
    except Exception as e:
        logger.error(f"❌ Error archiving runs: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    import sys
    
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    archive_old_runs(days_threshold=days)
