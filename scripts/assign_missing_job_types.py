"""
Assign job types to jobs that are missing them.
Uses the search_query from scrape_runs to determine the correct job_type.
"""

import sys
import os

# Add parent directory to path so we can import from database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from database.client import db

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

def assign_missing_job_types():
    """Assign job types to jobs based on their scrape_run's search_query."""
    
    logger.info("Starting job type assignment...")
    
    try:
        # Get all jobs without a job type assignment
        logger.info("Fetching all jobs...")
        all_jobs = []
        offset = 0
        batch_size = 1000
        
        while True:
            batch = db.client.table("job_postings")\
                .select("id")\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            if not batch.data:
                break
                
            all_jobs.extend(batch.data)
            offset += batch_size
            
            if len(batch.data) < batch_size:
                break
        
        logger.info(f"✓ Found {len(all_jobs)} total jobs")
        
        # Get all existing job type assignments
        logger.info("Fetching existing assignments...")
        existing_assignments = db.client.table("job_type_assignments")\
            .select("job_posting_id")\
            .execute()
        
        assigned_job_ids = {a["job_posting_id"] for a in existing_assignments.data}
        logger.info(f"✓ Found {len(assigned_job_ids)} jobs already with type assignments")
        
        # Filter to jobs without assignments
        unassigned_jobs = [j for j in all_jobs if j["id"] not in assigned_job_ids]
        logger.info(f"Found {len(unassigned_jobs)} jobs without type assignments")
        
        if not unassigned_jobs:
            logger.info("✅ All jobs already have type assignments!")
            return
        
        # Get all search queries with their job_type_id
        logger.info("Fetching search queries...")
        search_queries = db.client.table("search_queries")\
            .select("id, search_query, location_query, job_type_id")\
            .execute()
        
        # Create mapping: (search_query, location) -> job_type_id
        query_to_type = {}
        for sq in search_queries.data:
            if sq.get("job_type_id"):
                key = (sq["search_query"].lower(), sq["location_query"].lower())
                query_to_type[key] = sq["job_type_id"]
        
        logger.info(f"✓ Found {len(query_to_type)} search queries with job types")
        logger.info(f"Processing {len(unassigned_jobs)} jobs...")
        
        # Process each unassigned job
        assigned_count = 0
        skipped_count = 0
        
        for job in unassigned_jobs:
            job_id = job["id"]
            
            # Find the scrape_run(s) that found this job
            scrape_history = db.client.table("job_scrape_history")\
                .select("scrape_run_id")\
                .eq("job_posting_id", job_id)\
                .limit(1)\
                .execute()
            
            if not scrape_history.data:
                logger.debug(f"No scrape history for job {job_id}")
                skipped_count += 1
                continue
            
            scrape_run_id = scrape_history.data[0]["scrape_run_id"]
            
            # Get the scrape_run details
            scrape_run = db.client.table("scrape_runs")\
                .select("search_query, location_query, job_type_id")\
                .eq("id", scrape_run_id)\
                .single()\
                .execute()
            
            if not scrape_run.data:
                skipped_count += 1
                continue
            
            run = scrape_run.data
            
            # Try to get job_type_id from scrape_run first
            job_type_id = run.get("job_type_id")
            
            # If not in scrape_run, try to match with search_queries
            if not job_type_id:
                key = (run["search_query"].lower(), run["location_query"].lower())
                job_type_id = query_to_type.get(key)
            
            if job_type_id:
                # Assign the job type
                try:
                    db.client.table("job_type_assignments").insert({
                        "job_posting_id": job_id,
                        "job_type_id": job_type_id,
                        "assigned_via": "script"
                    }).execute()
                    assigned_count += 1
                    
                    if assigned_count % 100 == 0:
                        logger.info(f"Progress: {assigned_count} jobs assigned...")
                        
                except Exception as e:
                    if "duplicate key" not in str(e).lower():
                        logger.warning(f"Failed to assign type to job {job_id}: {e}")
            else:
                skipped_count += 1
        
        logger.success(f"✅ Assigned job types to {assigned_count} jobs")
        logger.info(f"⚠️  Skipped {skipped_count} jobs (no matching search query with job_type)")
        
        return assigned_count
        
    except Exception as e:
        logger.error(f"❌ Failed to assign job types: {e}")
        logger.exception(e)
        return 0

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("ASSIGN MISSING JOB TYPES")
    logger.info("="*80)
    
    count = assign_missing_job_types()
    
    if count > 0:
        logger.success(f"✅ Done! Assigned {count} job types.")
    else:
        logger.info("No job types were assigned.")
