"""
ONE-TIME SCHEDULER FOR SIZE_CATEGORY INFERENCE
===============================================

This is a TEMPORARY one-time scheduler that runs the size_category inference script
tomorrow (2025-12-18) at 11:00 AM to process the remaining companies after the first
batch of 1000 completes.

⚠️  IMPORTANT: This scheduler should be REMOVED after successful execution!
⚠️  This is NOT meant to run continuously - it's a one-time ad-hoc task.

How to use:
1. Start this scheduler: python3 one_time_size_category_scheduler.py
2. It will wait until 11:00 AM tomorrow (2025-12-18)
3. It will run the size_category inference script once
4. After successful completion, REMOVE this file and stop the scheduler

To stop manually: Ctrl+C or kill the process
"""

import schedule
import time
import subprocess
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

# Configure logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add("logs/one_time_size_category_scheduler.log", rotation="10 MB")

# Path to the inference script
SCRIPT_PATH = Path(__file__).parent / "infer_size_category_from_existing_data.py"

def run_size_category_inference():
    """
    Run the size_category inference script.
    This will process the next batch of companies (up to 1000).
    """
    logger.info("="*80)
    logger.info("🚀 STARTING SIZE_CATEGORY INFERENCE (ONE-TIME SCHEDULED RUN)")
    logger.info("="*80)
    logger.info(f"Script: {SCRIPT_PATH}")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            ["python3", str(SCRIPT_PATH)],
            cwd=str(SCRIPT_PATH.parent),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Log the output
        if result.stdout:
            logger.info("Script output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("Script errors:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"  {line}")
        
        # Check exit code
        if result.returncode == 0:
            logger.success("✅ Size category inference completed successfully!")
            logger.info("="*80)
            logger.info("⚠️  REMINDER: This was a ONE-TIME scheduler.")
            logger.info("⚠️  Please REMOVE this scheduler file: one_time_size_category_scheduler.py")
            logger.info("⚠️  And stop this process.")
            logger.info("="*80)
        else:
            logger.error(f"❌ Script failed with exit code: {result.returncode}")
        
        logger.info(f"Completed at: {datetime.now().isoformat()}")
        
        # Exit after running once
        logger.info("Exiting scheduler (one-time run complete)")
        sys.exit(0)
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Script timed out after 1 hour")
    except Exception as e:
        logger.error(f"❌ Error running script: {e}")

def main():
    """Main scheduler function."""
    logger.info("="*80)
    logger.info("ONE-TIME SIZE_CATEGORY INFERENCE SCHEDULER")
    logger.info("="*80)
    logger.info("⚠️  This is a TEMPORARY one-time scheduler")
    logger.info("⚠️  Scheduled to run: Tomorrow (2025-12-18) at 11:00 AM")
    logger.info("⚠️  After successful run, REMOVE this file!")
    logger.info("="*80)
    
    # Schedule the job for 11:00 AM
    schedule.every().day.at("11:00").do(run_size_category_inference)
    
    logger.info(f"Scheduler started at: {datetime.now().isoformat()}")
    logger.info("Waiting for scheduled time (11:00 AM)...")
    logger.info("Press Ctrl+C to stop")
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n⚠️  Scheduler stopped by user (Ctrl+C)")
        sys.exit(0)

if __name__ == "__main__":
    main()
