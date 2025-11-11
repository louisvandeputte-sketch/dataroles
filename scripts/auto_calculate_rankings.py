"""
Auto-calculate rankings for jobs that need it.

This script checks for jobs with needs_ranking = TRUE and calculates their rankings.
Can be run as a cron job or manually.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db
from ranking.job_ranker import calculate_and_save_rankings, load_jobs_from_database


def check_jobs_needing_ranking():
    """Check how many jobs need ranking"""
    result = db.client.table("job_postings")\
        .select("id", count="exact")\
        .eq("is_active", True)\
        .eq("needs_ranking", True)\
        .execute()
    
    return result.count


def main():
    """Main function to auto-calculate rankings"""
    logger.info("="*60)
    logger.info("AUTO RANKING CALCULATION")
    logger.info("="*60)
    
    # Check if any jobs need ranking
    jobs_needing_ranking = check_jobs_needing_ranking()
    
    if jobs_needing_ranking == 0:
        logger.info("✅ No jobs need ranking. All rankings are up to date.")
        return
    
    logger.info(f"Found {jobs_needing_ranking} jobs that need ranking")
    logger.info("Starting ranking calculation...")
    
    try:
        # Calculate rankings (this will use the updated load function)
        num_ranked = calculate_and_save_rankings()
        
        logger.info("="*60)
        logger.info(f"✅ SUCCESS: Ranked {num_ranked} jobs")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error calculating rankings: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
