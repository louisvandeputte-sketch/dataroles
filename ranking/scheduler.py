"""
Job Ranking & Maintenance Scheduler
====================================

Scheduled tasks:
- Ranking calculation: Every hour (for dynamic rankings with hourly multiplier)
- Stuck run cleanup: Every hour
- Location geocoding: Every 6 hours (50 locations per batch)
- Auto-archive old runs: Every day at 3 AM (archives runs >2 days old)
"""

import schedule
import time
from datetime import datetime
from loguru import logger
import pytz

from ranking.job_ranker import calculate_and_save_rankings
from ingestion.stuck_run_cleaner import clean_stuck_runs
from ingestion.location_geocoder import enrich_all_locations
from ingestion.auto_archive_runs import archive_old_runs


def run_ranking_job():
    """Run the ranking calculation"""
    logger.info("⏰ Scheduled ranking job triggered")
    
    try:
        num_ranked = calculate_and_save_rankings()
        logger.info(f"✅ Scheduled ranking complete: {num_ranked} jobs ranked")
    except Exception as e:
        logger.error(f"❌ Scheduled ranking failed: {e}")


def run_stuck_run_cleanup():
    """Clean up stuck scrape runs"""
    logger.info("⏰ Scheduled stuck run cleanup triggered")
    
    try:
        num_cleaned = clean_stuck_runs()
        if num_cleaned > 0:
            logger.info(f"✅ Cleaned up {num_cleaned} stuck run(s)")
        else:
            logger.info("✅ No stuck runs found")
    except Exception as e:
        logger.error(f"❌ Stuck run cleanup failed: {e}")


def run_geocoding_job():
    """Geocode locations without coordinates"""
    logger.info("⏰ Scheduled geocoding job triggered")
    
    try:
        # Process 50 locations at a time
        enrich_all_locations(limit=50, only_missing=True)
        logger.info("✅ Scheduled geocoding complete")
    except Exception as e:
        logger.error(f"❌ Scheduled geocoding failed: {e}")


def run_archive_job():
    """Archive old scrape runs (>2 days)"""
    logger.info("⏰ Scheduled archive job triggered")
    
    try:
        num_archived = archive_old_runs(days_threshold=2)
        if num_archived > 0:
            logger.info(f"✅ Archived {num_archived} old run(s)")
        else:
            logger.info("✅ No runs to archive")
    except Exception as e:
        logger.error(f"❌ Archive job failed: {e}")


def start_scheduler():
    """Start the ranking scheduler"""
    # Belgian timezone
    belgium_tz = pytz.timezone('Europe/Brussels')
    
    logger.info("🕐 Starting job ranking & maintenance scheduler...")
    logger.info("📅 Ranking schedule: Every hour (dynamic rankings with random multiplier)")
    logger.info("📅 Stuck run cleanup: Every hour")
    logger.info("📅 Location geocoding: Every 6 hours (50 locations per batch)")
    logger.info("📅 Auto-archive old runs: Every day at 3:00 AM (archives runs >2 days old)")
    
    # Schedule ranking calculation every hour
    schedule.every().hour.do(run_ranking_job)
    
    # Schedule stuck run cleanup every hour
    schedule.every().hour.do(run_stuck_run_cleanup)
    
    # Schedule geocoding every 6 hours
    schedule.every(6).hours.do(run_geocoding_job)
    
    # Schedule auto-archive every day at 3 AM (Belgian time)
    schedule.every().day.at("03:00").do(run_archive_job)
    
    # Also run immediately on startup
    logger.info("🚀 Running initial ranking calculation...")
    run_ranking_job()
    
    logger.info("🚀 Running initial stuck run cleanup...")
    run_stuck_run_cleanup()
    
    logger.info("🚀 Running initial geocoding...")
    run_geocoding_job()
    
    # Keep running
    logger.info("✅ Scheduler started. Waiting for scheduled jobs...")
    logger.info("⏰ Next ranking: in 1 hour")
    logger.info("⏰ Next geocoding: in 6 hours")
    logger.info("⏰ Next archive: tomorrow at 3:00 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    start_scheduler()
