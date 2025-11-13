"""Debug script to check why scrape run shows 1 job but no jobs in history."""

from database import db
from loguru import logger

run_id = "3830cbff-3699-47d2-88e4-0ed41ce8b048"

logger.info(f"Checking scrape run: {run_id}")

# 1. Get scrape run details
run = db.client.table("scrape_runs")\
    .select("*")\
    .eq("id", run_id)\
    .single()\
    .execute()

logger.info(f"\n=== SCRAPE RUN DETAILS ===")
logger.info(f"Query: {run.data.get('search_query')}")
logger.info(f"Location: {run.data.get('location_query')}")
logger.info(f"Status: {run.data.get('status')}")
logger.info(f"Jobs found: {run.data.get('jobs_found')}")
logger.info(f"Jobs new: {run.data.get('jobs_new')}")
logger.info(f"Jobs updated: {run.data.get('jobs_updated')}")
logger.info(f"Started: {run.data.get('started_at')}")
logger.info(f"Completed: {run.data.get('completed_at')}")
logger.info(f"Metadata: {run.data.get('metadata')}")

# 2. Check job_scrape_history for this run
history = db.client.table("job_scrape_history")\
    .select("*")\
    .eq("scrape_run_id", run_id)\
    .execute()

logger.info(f"\n=== JOB SCRAPE HISTORY ===")
logger.info(f"Records in job_scrape_history: {len(history.data) if history.data else 0}")

if history.data:
    for h in history.data:
        logger.info(f"  - Job ID: {h['job_posting_id']}, Detected: {h['detected_at']}")
        
        # Get job details
        job = db.client.table("job_postings")\
            .select("title, companies(name)")\
            .eq("id", h['job_posting_id'])\
            .single()\
            .execute()
        
        if job.data:
            logger.info(f"    Title: {job.data.get('title')}")
            logger.info(f"    Company: {job.data.get('companies', {}).get('name')}")
else:
    logger.warning("❌ NO RECORDS in job_scrape_history for this run!")

# 3. Check if there are jobs with this run_id in metadata or other fields
logger.info(f"\n=== CHECKING FOR JOBS LINKED TO THIS RUN ===")

# Check if any jobs have this run_id in their metadata
jobs_with_run = db.client.table("job_postings")\
    .select("id, title, created_at")\
    .execute()

found_jobs = []
if jobs_with_run.data:
    for job in jobs_with_run.data:
        # Check created_at timestamp - if it matches the run's started_at, it might be from this run
        if run.data.get('started_at') and job.get('created_at'):
            from datetime import datetime, timedelta
            run_start = datetime.fromisoformat(run.data['started_at'].replace('Z', '+00:00'))
            job_created = datetime.fromisoformat(job['created_at'].replace('Z', '+00:00'))
            
            # If job was created within 10 minutes of run start
            if abs((job_created - run_start).total_seconds()) < 600:
                found_jobs.append(job)

if found_jobs:
    logger.info(f"Found {len(found_jobs)} jobs created around the same time as this run:")
    for job in found_jobs:
        logger.info(f"  - {job['id']}: {job['title']}")
else:
    logger.info("No jobs found created around the same time as this run")

# 4. Summary
logger.info(f"\n=== SUMMARY ===")
logger.info(f"Run says: {run.data.get('jobs_found')} jobs found")
logger.info(f"History has: {len(history.data) if history.data else 0} records")
logger.info(f"Discrepancy: {run.data.get('jobs_found', 0) - (len(history.data) if history.data else 0)} jobs missing")
