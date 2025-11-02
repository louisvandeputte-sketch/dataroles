#!/usr/bin/env python3
"""Check job type assignments for recent jobs."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.client import db
from loguru import logger

def check_assignments():
    """Check job type assignments."""
    
    logger.info("Checking job type assignments...")
    
    # 1. Check search_queries
    logger.info("\n1. Checking search_queries...")
    queries = db.client.table("search_queries")\
        .select("id, search_query, location_query, job_type_id")\
        .execute()
    
    with_type = [q for q in queries.data if q.get("job_type_id")]
    without_type = [q for q in queries.data if not q.get("job_type_id")]
    
    logger.info(f"Total queries: {len(queries.data)}")
    logger.info(f"  With job_type_id: {len(with_type)}")
    logger.info(f"  Without job_type_id: {len(without_type)}")
    
    if without_type:
        logger.warning("Queries WITHOUT job_type_id:")
        for q in without_type:
            logger.warning(f"  - {q['search_query']} in {q['location_query']}")
    
    # 2. Check recent scrape_runs
    logger.info("\n2. Checking recent scrape_runs...")
    runs = db.client.table("scrape_runs")\
        .select("id, search_query, location_query, job_type_id, jobs_found, started_at")\
        .order("started_at", desc=True)\
        .limit(10)\
        .execute()
    
    logger.info(f"Last 10 scrape runs:")
    for run in runs.data:
        logger.info(f"  - {run['search_query']} in {run['location_query']}")
        logger.info(f"    job_type_id: {run.get('job_type_id', 'NONE')}")
        logger.info(f"    jobs_found: {run.get('jobs_found', 0)}")
        logger.info(f"    started_at: {run.get('started_at')}")
        
        # Check if jobs from this run have type assignments
        if run.get('job_type_id'):
            history = db.client.table("job_scrape_history")\
                .select("job_posting_id")\
                .eq("scrape_run_id", run['id'])\
                .limit(5)\
                .execute()
            
            if history.data:
                job_ids = [h['job_posting_id'] for h in history.data[:3]]
                logger.info(f"    Checking first 3 jobs from this run...")
                
                for job_id in job_ids:
                    assignments = db.client.table("job_type_assignments")\
                        .select("job_type_id, assigned_via")\
                        .eq("job_posting_id", job_id)\
                        .execute()
                    
                    if assignments.data:
                        logger.success(f"      ✓ Job {job_id[:8]}... HAS assignment: {assignments.data[0]['job_type_id'][:8]}... via {assignments.data[0]['assigned_via']}")
                    else:
                        logger.error(f"      ✗ Job {job_id[:8]}... MISSING assignment!")
        logger.info("")
    
    # 3. Check total assignments
    logger.info("\n3. Overall statistics...")
    total_jobs = db.client.table("job_postings").select("id", count="exact").execute()
    total_assignments = db.client.table("job_type_assignments").select("id", count="exact").execute()
    
    logger.info(f"Total jobs: {total_jobs.count}")
    logger.info(f"Total assignments: {total_assignments.count}")
    logger.info(f"Jobs without assignment: {total_jobs.count - total_assignments.count}")

if __name__ == "__main__":
    check_assignments()
