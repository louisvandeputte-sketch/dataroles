"""Main ingestion pipeline for processing LinkedIn job data."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger
from pydantic import ValidationError

from models.linkedin import LinkedInJobPosting
from database.client import db
from ingestion.normalizer import normalize_company, normalize_location
from ingestion.deduplicator import check_job_exists, should_update_job


class ProcessingResult:
    """Result of processing a single job."""
    
    def __init__(
        self,
        status: str,  # 'new', 'updated', 'skipped', 'error'
        job_id: Optional[UUID] = None,
        error: Optional[str] = None
    ):
        self.status = status
        self.job_id = job_id
        self.error = error


class BatchResult:
    """Result of processing a batch of jobs."""
    
    def __init__(self):
        self.new_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.results: List[ProcessingResult] = []
    
    def add(self, result: ProcessingResult):
        """Add a processing result to the batch."""
        self.results.append(result)
        if result.status == 'new':
            self.new_count += 1
        elif result.status == 'updated':
            self.updated_count += 1
        elif result.status == 'skipped':
            self.skipped_count += 1
        elif result.status == 'error':
            self.error_count += 1
    
    def summary(self) -> str:
        """Get summary string of batch results."""
        return f"New: {self.new_count}, Updated: {self.updated_count}, Skipped: {self.skipped_count}, Errors: {self.error_count}"


def process_job_posting(raw_job: Dict[str, Any], scrape_run_id: UUID) -> ProcessingResult:
    """
    Process a single job posting through the ingestion pipeline.
    
    Workflow:
    1. Parse with Pydantic model
    2. Process company (upsert)
    3. Process location (insert if new)
    4. Check deduplication
    5. Insert or update job posting
    6. Insert related records (description, poster, llm_enrichment stub)
    7. Record in scrape history
    
    Args:
        raw_job: Raw job data from Bright Data API
        scrape_run_id: UUID of current scrape run
    
    Returns:
        ProcessingResult with status and job_id
    """
    try:
        # Step 1: Parse and validate with Pydantic
        try:
            job = LinkedInJobPosting(**raw_job)
        except ValidationError as e:
            logger.error(f"Validation error for job {raw_job.get('job_posting_id')}: {e}")
            return ProcessingResult(status='error', error=str(e))
        
        # Step 2: Process company
        company_model = job.get_company()
        company_data = normalize_company(company_model.model_dump())
        
        if company_data.get("linkedin_company_id"):
            existing_company = db.get_company_by_linkedin_id(company_data["linkedin_company_id"])
            if existing_company:
                company_id = UUID(existing_company["id"])
            else:
                company_id = db.insert_company(company_data)
        else:
            # No linkedin_company_id, insert with just name
            company_id = db.insert_company(company_data)
        
        # Step 3: Process location
        location_model = job.get_location()
        location_data = normalize_location(location_model.full_location_string)
        
        existing_location = db.get_location_by_string(location_data["full_location_string"])
        if existing_location:
            location_id = UUID(existing_location["id"])
        else:
            location_id = db.insert_location(location_data)
        
        # Step 4: Check deduplication
        exists, existing_job_id, existing_job_data = check_job_exists(job.job_posting_id)
        
        job_data = job.to_db_dict(company_id, location_id)
        
        if exists:
            # Job exists, check if update needed
            if should_update_job(existing_job_data, job_data):
                # Update job posting with changes
                db.update_job_posting(existing_job_id, {
                    **job_data,
                    "last_seen_at": datetime.utcnow().isoformat()
                })
                job_id = existing_job_id
                status = 'updated'
                logger.info(f"Updated job: {job.job_title} ({job.job_posting_id})")
            else:
                # No changes, just update last_seen_at
                # Still count as 'updated' since we re-saw it in this run
                db.update_job_posting(existing_job_id, {
                    "last_seen_at": datetime.utcnow().isoformat()
                })
                job_id = existing_job_id
                status = 'updated'  # Changed from 'skipped' to 'updated'
                logger.debug(f"Re-saw job (no changes): {job.job_title} ({job.job_posting_id})")
        else:
            # Step 5: Insert new job posting
            job_id = db.insert_job_posting(job_data)
            
            # Step 6: Insert job description
            description_data = job.get_description_dict(job_id)
            db.insert_job_description(description_data)
            
            # Insert job poster if available
            poster = job.get_poster()
            if poster:
                poster_data = poster.to_db_dict(job_id)
                if poster_data:
                    db.insert_job_poster(poster_data)
            
            # Insert LLM enrichment stub (all NULL fields)
            db.insert_llm_enrichment_stub(job_id)
            
            status = 'new'
            logger.info(f"Inserted new job: {job.job_title} ({job.job_posting_id})")
        
        # Step 7: Record in scrape history
        db.insert_scrape_history(job_id, scrape_run_id)
        
        return ProcessingResult(status=status, job_id=job_id)
        
    except Exception as e:
        logger.exception(f"Error processing job {raw_job.get('job_posting_id', 'unknown')}: {e}")
        return ProcessingResult(status='error', error=str(e))


async def process_jobs_batch(raw_jobs: List[Dict[str, Any]], scrape_run_id: UUID) -> BatchResult:
    """
    Process multiple jobs in batch with error handling.
    
    Args:
        raw_jobs: List of raw job data from API
        scrape_run_id: UUID of current scrape run
    
    Returns:
        BatchResult with counts and details
    """
    logger.info(f"Processing batch of {len(raw_jobs)} jobs")
    
    result = BatchResult()
    
    for i, raw_job in enumerate(raw_jobs, 1):
        if i % 10 == 0:
            logger.info(f"Processed {i}/{len(raw_jobs)} jobs")
        
        job_result = process_job_posting(raw_job, scrape_run_id)
        result.add(job_result)
    
    logger.success(f"Batch processing complete: {result.summary()}")
    return result
