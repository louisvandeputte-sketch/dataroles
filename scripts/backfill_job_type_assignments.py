"""
Backfill job type assignments for existing scrape runs.
This script assigns job types to jobs that were scraped but don't have type assignments yet.
"""

from database.client import db
from loguru import logger

def backfill_job_type_assignments():
    """Backfill job type assignments from scrape runs."""
    
    # Get all scrape runs with a job_type_id
    runs = db.client.table("scrape_runs")\
        .select("id, job_type_id, search_query, jobs_found")\
        .not_.is_("job_type_id", "null")\
        .order("started_at", desc=True)\
        .execute()
    
    logger.info(f"Found {len(runs.data)} scrape runs with job types")
    
    total_created = 0
    total_skipped = 0
    
    for run in runs.data:
        run_id = run['id']
        job_type_id = run['job_type_id']
        
        # Get all jobs from this scrape run via job_scrape_history
        history = db.client.table("job_scrape_history")\
            .select("job_posting_id")\
            .eq("scrape_run_id", run_id)\
            .execute()
        
        if not history.data:
            logger.debug(f"No jobs in history for run {run_id}")
            continue
        
        logger.info(f"Processing run '{run['search_query']}' with {len(history.data)} jobs")
        
        created_count = 0
        for item in history.data:
            job_id = item['job_posting_id']
            
            try:
                # Try to insert (will fail silently if already exists)
                db.client.table("job_type_assignments").insert({
                    "job_posting_id": job_id,
                    "job_type_id": job_type_id,
                    "assigned_via": "backfill"
                }).execute()
                created_count += 1
            except Exception as e:
                # Ignore duplicate key errors
                if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                    total_skipped += 1
                else:
                    logger.warning(f"Failed to assign type to job {job_id}: {e}")
        
        total_created += created_count
        logger.info(f"  Created {created_count} assignments for this run")
    
    logger.success(f"✅ Backfill complete: {total_created} created, {total_skipped} skipped (already existed)")
    return {
        "created": total_created,
        "skipped": total_skipped
    }


if __name__ == "__main__":
    logger.info("Starting job type assignment backfill...")
    result = backfill_job_type_assignments()
    logger.info(f"Final result: {result}")
