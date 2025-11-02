"""
Assign job types to jobs that are missing them (FAST VERSION).
Uses bulk queries to avoid N+1 problem.
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
    
    logger.info("Starting FAST job type assignment...")
    
    try:
        # Step 1: Get all jobs without type assignments
        logger.info("1/5 Fetching jobs without type assignments...")
        
        # Manual query (RPC function doesn't exist)
        all_jobs = db.client.table("job_postings").select("id").execute()
        assigned = db.client.table("job_type_assignments").select("job_posting_id").execute()
        assigned_ids = {a["job_posting_id"] for a in assigned.data}
        unassigned_job_ids = [j["id"] for j in all_jobs.data if j["id"] not in assigned_ids]
        
        logger.info(f"✓ Found {len(unassigned_job_ids)} jobs without type assignments")
        
        if not unassigned_job_ids:
            logger.success("✅ All jobs already have type assignments!")
            return 0
        
        # Step 2: Get scrape_history for all unassigned jobs
        logger.info(f"2/5 Fetching scrape history for {len(unassigned_job_ids)} jobs...")
        
        # Batch fetch scrape_history (limit to avoid timeout)
        batch_size = 100  # Smaller batch size to avoid URL length issues
        job_to_run = {}
        
        for i in range(0, len(unassigned_job_ids), batch_size):
            batch = unassigned_job_ids[i:i+batch_size]
            history = db.client.table("job_scrape_history")\
                .select("job_posting_id, scrape_run_id")\
                .in_("job_posting_id", batch)\
                .execute()
            
            for h in history.data:
                if h["job_posting_id"] not in job_to_run:
                    job_to_run[h["job_posting_id"]] = h["scrape_run_id"]
            
            logger.info(f"  Progress: {min(i+batch_size, len(unassigned_job_ids))}/{len(unassigned_job_ids)}")
        
        logger.info(f"✓ Found scrape history for {len(job_to_run)} jobs")
        
        # Step 3: Get all scrape_runs
        logger.info("3/5 Fetching scrape runs...")
        run_ids = list(set(job_to_run.values()))
        
        run_to_type = {}
        for i in range(0, len(run_ids), batch_size):
            batch = run_ids[i:i+batch_size]
            runs = db.client.table("scrape_runs")\
                .select("id, job_type_id, search_query, location_query")\
                .in_("id", batch)\
                .execute()
            
            for run in runs.data:
                run_to_type[run["id"]] = {
                    "job_type_id": run.get("job_type_id"),
                    "search_query": run.get("search_query", "").lower(),
                    "location_query": run.get("location_query", "").lower()
                }
        
        logger.info(f"✓ Fetched {len(run_to_type)} scrape runs")
        
        # Step 4: Get search_queries mapping
        logger.info("4/5 Fetching search queries...")
        search_queries = db.client.table("search_queries")\
            .select("search_query, location_query, job_type_id")\
            .not_.is_("job_type_id", "null")\
            .execute()
        
        query_to_type = {}
        for sq in search_queries.data:
            key = (sq["search_query"].lower(), sq["location_query"].lower())
            query_to_type[key] = sq["job_type_id"]
        
        logger.info(f"✓ Found {len(query_to_type)} search queries with job types")
        
        # Step 5: Assign job types
        logger.info("5/5 Assigning job types...")
        
        assignments = []
        skipped = 0
        
        for job_id, run_id in job_to_run.items():
            run_info = run_to_type.get(run_id)
            if not run_info:
                skipped += 1
                continue
            
            # Try to get job_type_id from scrape_run
            job_type_id = run_info["job_type_id"]
            
            # If not in scrape_run, try search_queries mapping
            if not job_type_id:
                key = (run_info["search_query"], run_info["location_query"])
                job_type_id = query_to_type.get(key)
            
            if job_type_id:
                assignments.append({
                    "job_posting_id": job_id,
                    "job_type_id": job_type_id,
                    "assigned_via": "script"
                })
            else:
                skipped += 1
        
        logger.info(f"Prepared {len(assignments)} assignments, skipped {skipped}")
        
        # Bulk insert assignments
        if assignments:
            # Insert in batches to avoid timeout
            insert_batch_size = 500
            inserted = 0
            
            for i in range(0, len(assignments), insert_batch_size):
                batch = assignments[i:i+insert_batch_size]
                try:
                    db.client.table("job_type_assignments").insert(batch).execute()
                    inserted += len(batch)
                    logger.info(f"  Inserted {inserted}/{len(assignments)} assignments...")
                except Exception as e:
                    if "duplicate key" in str(e).lower():
                        logger.warning(f"Some assignments already exist (skipping)")
                    else:
                        logger.error(f"Failed to insert batch: {e}")
            
            logger.success(f"✅ Assigned job types to {inserted} jobs")
            logger.info(f"⚠️  Skipped {skipped} jobs (no matching job type found)")
            return inserted
        else:
            logger.warning("No assignments to make")
            return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to assign job types: {e}")
        logger.exception(e)
        return 0

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("ASSIGN MISSING JOB TYPES (FAST VERSION)")
    logger.info("="*80)
    
    count = assign_missing_job_types()
    
    if count > 0:
        logger.success(f"✅ Done! Assigned {count} job types.")
    else:
        logger.info("No job types were assigned.")
