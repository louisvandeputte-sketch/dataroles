"""
Job Ranking Scheduler
=====================

Runs ranking calculation daily at 3 AM Belgian time (CET/CEST)
"""

import schedule
import time
from datetime import datetime
from loguru import logger
import pytz

from ranking.job_ranker import calculate_and_save_rankings


def run_ranking_job():
    """Run the ranking calculation"""
    logger.info("⏰ Scheduled ranking job triggered")
    
    try:
        num_ranked = calculate_and_save_rankings()
        logger.info(f"✅ Scheduled ranking complete: {num_ranked} jobs ranked")
    except Exception as e:
        logger.error(f"❌ Scheduled ranking failed: {e}")


def start_scheduler():
    """Start the ranking scheduler"""
    # Belgian timezone
    belgium_tz = pytz.timezone('Europe/Brussels')
    
    logger.info("🕐 Starting job ranking scheduler...")
    logger.info("📅 Schedule: Daily at 3:00 AM Belgian time")
    
    # Schedule daily at 3 AM
    schedule.every().day.at("03:00").do(run_ranking_job)
    
    # Also run immediately on startup (optional)
    logger.info("🚀 Running initial ranking calculation...")
    run_ranking_job()
    
    # Keep running
    logger.info("✅ Scheduler started. Waiting for scheduled jobs...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    start_scheduler()
