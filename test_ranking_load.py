#!/usr/bin/env python3
"""
Test if ranking loads all jobs correctly
"""
from loguru import logger
from ranking.job_ranker import load_jobs_from_database

if __name__ == "__main__":
    logger.info("Testing job loading for ranking...")
    
    # Load all jobs (same as ranking does)
    jobs = load_jobs_from_database(only_needs_ranking=False)
    
    logger.info(f"✅ Loaded {len(jobs)} jobs")
    
    # Count by source
    linkedin_count = sum(1 for j in jobs if hasattr(j, 'source') and j.source == 'linkedin')
    indeed_count = sum(1 for j in jobs if hasattr(j, 'source') and j.source == 'indeed')
    
    logger.info(f"   LinkedIn: {linkedin_count}")
    logger.info(f"   Indeed: {indeed_count}")
    
    # Count enriched vs non-enriched
    enriched = sum(1 for j in jobs if j.enrichment_completed_at is not None)
    non_enriched = len(jobs) - enriched
    
    logger.info(f"   Enriched: {enriched}")
    logger.info(f"   Non-enriched: {non_enriched}")
