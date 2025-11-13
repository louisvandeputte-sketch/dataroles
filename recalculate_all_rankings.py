#!/usr/bin/env python3
"""
Recalculate all job rankings with new algorithm.
This script marks all jobs for re-ranking and then calculates new rankings.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from database.client import db
from ranking.job_ranker import calculate_and_save_rankings

def mark_all_for_reranking():
    """Mark all Data jobs for re-ranking"""
    logger.info("Marking all Data jobs for re-ranking...")
    
    result = db.client.table("job_postings")\
        .update({"needs_ranking": True})\
        .eq("title_classification", "Data")\
        .eq("is_active", True)\
        .execute()
    
    logger.info(f"✅ Marked all Data jobs for re-ranking")

def main():
    logger.info("=" * 80)
    logger.info("RECALCULATING ALL JOB RANKINGS")
    logger.info("=" * 80)
    
    # Step 1: Mark all for re-ranking
    mark_all_for_reranking()
    
    # Step 2: Calculate new rankings
    logger.info("\nCalculating new rankings with updated algorithm...")
    num_ranked = calculate_and_save_rankings()
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✅ COMPLETE: {num_ranked} jobs re-ranked")
    logger.info("=" * 80)
    
    logger.info("\nNew penalties applied:")
    logger.info("  - 'Other' role type: -50 points")
    logger.info("  - 'NIS' role type: -30 points")
    logger.info("  - No skills: -30 points")
    logger.info("\nJobs with 'Other' role type and no skills will rank much lower!")

if __name__ == "__main__":
    main()
