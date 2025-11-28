#!/usr/bin/env python3
"""
Manual script to run job ranking calculation once
Usage: python ranking/run_ranking_manual.py
"""

from job_ranker import calculate_and_save_rankings
from loguru import logger

if __name__ == "__main__":
    logger.info("🎯 Manual ranking calculation started...")
    
    try:
        num_jobs = calculate_and_save_rankings()
        logger.success(f"✅ Successfully ranked {num_jobs} jobs!")
        
    except Exception as e:
        logger.error(f"❌ Ranking failed: {e}")
        raise
