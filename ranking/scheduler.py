"""
Job Ranking & Maintenance Scheduler
====================================

Scheduled tasks:
- Ranking calculation: Every hour (for dynamic rankings with hourly multiplier)
- Stuck run cleanup: Every hour
"""

import schedule
import time
from datetime import datetime
from loguru import logger
import pytz

from ranking.job_ranker import calculate_and_save_rankings
from ingestion.stuck_run_cleaner import clean_stuck_runs


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


def start_scheduler():
    """Start the ranking scheduler"""
    # Belgian timezone
    belgium_tz = pytz.timezone('Europe/Brussels')
    
    logger.info("🕐 Starting job ranking scheduler...")
    logger.info("📅 Ranking schedule: Every hour (dynamic rankings with random multiplier)")
    logger.info("📅 Stuck run cleanup: Every hour")
    
    # Schedule ranking calculation every hour
    schedule.every().hour.do(run_ranking_job)
    
    # Schedule stuck run cleanup every hour
    schedule.every().hour.do(run_stuck_run_cleanup)
    
    # Also run immediately on startup
    logger.info("🚀 Running initial ranking calculation...")
    run_ranking_job()
    
    logger.info("🚀 Running initial stuck run cleanup...")
    run_stuck_run_cleanup()
    
    # Keep running
    logger.info("✅ Scheduler started. Waiting for scheduled jobs...")
    logger.info("⏰ Next ranking: in 1 hour")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    start_scheduler()
