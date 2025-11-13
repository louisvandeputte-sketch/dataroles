#!/usr/bin/env python3
"""
Rerank all jobs after increasing Other/NIS penalties
"""
from loguru import logger
from ranking.job_ranker import calculate_and_save_rankings

if __name__ == "__main__":
    logger.info("🔄 Reranking all jobs after penalty increase...")
    logger.info("   'Other' penalty: -50 → -200 points")
    logger.info("   'NIS' penalty: -30 → -150 points")
    
    count = calculate_and_save_rankings()
    
    logger.info(f"✅ Reranked {count} jobs successfully!")
    logger.info("   'Other' and 'NIS' jobs should now be at the bottom")
