"""One-time script to set all jobs to type 'Data'."""

from loguru import logger
from database.client import db


def set_all_jobs_to_data_type():
    """Set all job postings to type 'Data'."""
    try:
        logger.info("Starting to update all jobs to type 'Data'")
        
        # First, check if 'Data' type exists in job_types table
        type_result = db.client.table("job_types")\
            .select("id")\
            .eq("name", "Data")\
            .execute()
        
        if not type_result.data:
            logger.info("Creating 'Data' job type...")
            create_result = db.client.table("job_types")\
                .insert({"name": "Data"})\
                .execute()
            data_type_id = create_result.data[0]["id"]
            logger.success(f"Created 'Data' type with ID: {data_type_id}")
        else:
            data_type_id = type_result.data[0]["id"]
            logger.info(f"Found existing 'Data' type with ID: {data_type_id}")
        
        # Get all job postings (fetch in batches to handle large datasets)
        all_jobs = []
        page_size = 1000
        offset = 0
        
        while True:
            jobs_result = db.client.table("job_postings")\
                .select("id")\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if not jobs_result.data:
                break
            
            all_jobs.extend(jobs_result.data)
            logger.info(f"Fetched {len(all_jobs)} jobs so far...")
            
            if len(jobs_result.data) < page_size:
                break
            
            offset += page_size
        
        total_jobs = len(all_jobs)
        logger.info(f"Found {total_jobs} total jobs to update")
        
        if total_jobs == 0:
            logger.warning("No jobs found in database")
            return
        
        # Get existing job_type_assignments to avoid duplicates (fetch all)
        existing_job_ids = set()
        offset = 0
        page_size = 1000
        
        while True:
            existing_result = db.client.table("job_type_assignments")\
                .select("job_posting_id")\
                .eq("job_type_id", data_type_id)\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if not existing_result.data:
                break
            
            for row in existing_result.data:
                existing_job_ids.add(row["job_posting_id"])
            
            if len(existing_result.data) < page_size:
                break
            
            offset += page_size
        
        logger.info(f"Found {len(existing_job_ids)} jobs already with 'Data' type")
        
        # Prepare inserts for jobs that don't have the type yet
        inserts = []
        for job in all_jobs:
            if job["id"] not in existing_job_ids:
                inserts.append({
                    "job_posting_id": job["id"],
                    "job_type_id": data_type_id,
                    "assigned_via": "manual"
                })
        
        if not inserts:
            logger.success("All jobs already have 'Data' type!")
            return
        
        logger.info(f"Inserting 'Data' type for {len(inserts)} jobs...")
        
        # Insert in batches of 100 to avoid timeout
        batch_size = 100
        successful = 0
        failed = 0
        
        for i in range(0, len(inserts), batch_size):
            batch = inserts[i:i + batch_size]
            try:
                db.client.table("job_type_assignments")\
                    .insert(batch)\
                    .execute()
                successful += len(batch)
                logger.info(f"Progress: {successful}/{len(inserts)} jobs updated")
            except Exception as e:
                failed += len(batch)
                logger.error(f"Failed to insert batch: {e}")
        
        logger.success(f"✅ Update complete!")
        logger.success(f"   Total jobs: {total_jobs}")
        logger.success(f"   Already had type: {len(existing_job_ids)}")
        logger.success(f"   Successfully updated: {successful}")
        logger.success(f"   Failed: {failed}")
        
    except Exception as e:
        logger.error(f"Failed to update jobs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Setting all jobs to type 'Data'")
    logger.info("=" * 60)
    set_all_jobs_to_data_type()
