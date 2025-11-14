#!/usr/bin/env python3
"""
Test if jobs are sorted correctly by ranking_score
"""
from loguru import logger
from database.client import db

if __name__ == "__main__":
    logger.info("Testing job sorting by ranking_score...")
    
    # Get top 20 jobs sorted by ranking_score DESC
    result = db.client.table("job_postings")\
        .select("id, title, ranking_score, ranking_position")\
        .eq("is_active", True)\
        .eq("title_classification", "Data")\
        .order("ranking_score", desc=True)\
        .limit(20)\
        .execute()
    
    logger.info(f"\n✅ Top 20 jobs by ranking_score (DESC):\n")
    for i, job in enumerate(result.data, 1):
        score = job.get('ranking_score')
        position = job.get('ranking_position')
        title = job.get('title', '')[:50]
        logger.info(f"{i:2d}. Score: {score:7.1f} | Pos: {position:4} | {title}")
