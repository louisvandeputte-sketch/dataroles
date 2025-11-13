#!/usr/bin/env python3
"""
Test if ranking loads all jobs correctly and check multi-source support
"""
from loguru import logger
from ranking.job_ranker import load_jobs_from_database
from database.client import db

if __name__ == "__main__":
    logger.info("Testing job loading for ranking...")
    
    # Load all jobs (same as ranking does)
    jobs = load_jobs_from_database(only_needs_ranking=False)
    
    logger.info(f"✅ Loaded {len(jobs)} jobs")
    
    # Count by primary source (from job_postings.source - backward compatibility)
    linkedin_count = sum(1 for j in jobs if hasattr(j, 'source') and j.source == 'linkedin')
    indeed_count = sum(1 for j in jobs if hasattr(j, 'source') and j.source == 'indeed')
    
    logger.info(f"\n📊 Primary source (job_postings.source):")
    logger.info(f"   LinkedIn: {linkedin_count}")
    logger.info(f"   Indeed: {indeed_count}")
    
    # Check job_sources table for multi-source jobs
    logger.info(f"\n🔍 Checking job_sources table for multi-source support...")
    
    job_ids = [j.id for j in jobs]
    
    # Get all sources for these jobs
    sources_result = db.client.table("job_sources")\
        .select("job_posting_id, source")\
        .in_("job_posting_id", job_ids)\
        .execute()
    
    # Count jobs by source from job_sources table
    from collections import defaultdict
    job_to_sources = defaultdict(set)
    source_counts = defaultdict(int)
    
    for row in sources_result.data:
        job_id = row['job_posting_id']
        source = row['source']
        job_to_sources[job_id].add(source)
        source_counts[source] += 1
    
    # Find multi-source jobs
    multi_source_jobs = [job_id for job_id, sources in job_to_sources.items() if len(sources) > 1]
    
    logger.info(f"\n📊 Actual sources (job_sources table):")
    logger.info(f"   LinkedIn entries: {source_counts.get('linkedin', 0)}")
    logger.info(f"   Indeed entries: {source_counts.get('indeed', 0)}")
    logger.info(f"   Jobs with BOTH sources: {len(multi_source_jobs)}")
    logger.info(f"   Jobs with only LinkedIn: {sum(1 for sources in job_to_sources.values() if sources == {'linkedin'})}")
    logger.info(f"   Jobs with only Indeed: {sum(1 for sources in job_to_sources.values() if sources == {'indeed'})}")
    
    # Count enriched vs non-enriched
    enriched = sum(1 for j in jobs if j.enrichment_completed_at is not None)
    non_enriched = len(jobs) - enriched
    
    logger.info(f"\n📊 Enrichment status:")
    logger.info(f"   Enriched: {enriched}")
    logger.info(f"   Non-enriched: {non_enriched}")
