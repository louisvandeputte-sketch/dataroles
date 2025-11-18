"""Main ingestion pipeline for processing LinkedIn and Indeed job data."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger
from pydantic import ValidationError

from models.linkedin import LinkedInJobPosting
from models.indeed import IndeedJobPosting
from database.client import db
from ingestion.normalizer import normalize_company, normalize_location
from ingestion.deduplicator import should_update_job  # Keep for update logic
from ingestion.deduplicator_v2 import (
    check_job_exists_by_dedup,
    check_source_exists_for_job,
    add_source_to_job,
    update_source_last_seen,
    create_dedup_key
)
from ingestion.job_title_classifier import classify_and_save


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
    
    @property
    def job_ids(self) -> List[UUID]:
        """Get list of all successfully processed job IDs."""
        return [r.job_id for r in self.results if r.job_id is not None]
    
    @property
    def error_details(self) -> List[Dict[str, str]]:
        """Get list of all errors with details."""
        return [{"error": r.error} for r in self.results if r.status == 'error']


def process_job_posting(raw_job: Dict[str, Any], scrape_run_id: UUID, source: str = "linkedin") -> ProcessingResult:
    """
    Process a single job posting through the ingestion pipeline.
    
    Workflow:
    1. Parse with Pydantic model (LinkedIn or Indeed)
    2. Process company (upsert)
    3. Process location (insert if new)
    4. Check deduplication
    5. Insert or update job posting
    6. Insert related records (description, poster, llm_enrichment stub)
    7. Record in scrape history
    
    Args:
        raw_job: Raw job data from Bright Data API
        scrape_run_id: UUID of current scrape run
        source: Job source - "linkedin" or "indeed"
    
    Returns:
        ProcessingResult with status and job_id
    """
    try:
        # Step 1: Parse and validate with Pydantic based on source
        # Extract job_id_field first for error logging
        if source == "linkedin":
            job_id_field = raw_job.get('job_posting_id', 'unknown')
        elif source == "indeed":
            # Bright Data uses 'jobid' (not 'job_id')
            job_id_field = raw_job.get('jobid', 'unknown')
        else:
            job_id_field = 'unknown'
        
        try:
            if source == "linkedin":
                job = LinkedInJobPosting(**raw_job)
            elif source == "indeed":
                # Log raw data for debugging
                logger.debug(f"Raw Indeed job keys: {list(raw_job.keys())}")
                job = IndeedJobPosting(**raw_job)
            else:
                raise ValueError(f"Unknown source: {source}")
        except ValidationError as e:
            error_msg = f"ValidationError for {source} job {job_id_field}: {str(e)}"
            logger.error(error_msg)
            # Log raw data on validation failure for debugging
            import json
            logger.error(f"Raw job data that failed validation: {json.dumps(raw_job, indent=2)}")
            # Return simplified error for metadata (first error only)
            first_error = e.errors()[0] if e.errors() else {}
            field = first_error.get('loc', ['unknown'])[0]
            msg = first_error.get('msg', str(e))
            return ProcessingResult(status='error', error=f"Field '{field}': {msg}")
        
        # Step 2: Process company
        if source == "linkedin":
            company_model = job.get_company()
            company_data = normalize_company(company_model.model_dump())
        else:  # indeed
            company_data = normalize_company(job.get_company_dict())
        
        if company_data.get("linkedin_company_id"):
            # LinkedIn job: Check by LinkedIn ID
            existing_company = db.get_company_by_linkedin_id(company_data["linkedin_company_id"])
            if existing_company:
                company_id = UUID(existing_company["id"])
            else:
                company_id = db.insert_company(company_data)
        else:
            # Indeed job (no LinkedIn ID): Check by name to avoid duplicates
            existing_company = db.get_company_by_name(company_data["name"])
            if existing_company:
                company_id = UUID(existing_company["id"])
                logger.debug(f"Reusing existing company: {company_data['name']}")
            else:
                company_id = db.insert_company(company_data)
                logger.debug(f"Created new company: {company_data['name']}")
        
        # Step 3: Process location
        if source == "linkedin":
            location_model = job.get_location()
            location_string = location_model.full_location_string
        else:  # indeed
            location_string = job.get_location_string()
        
        location_data = normalize_location(location_string)
        
        existing_location = db.get_location_by_string(location_data["full_location_string"])
        if existing_location:
            location_id = UUID(existing_location["id"])
        else:
            location_id = db.insert_location(location_data)
        
        # Step 3b: Determine location override
        # If location is vague (e.g., "Flemish Region, Belgium"), create/get location from company
        location_id_override = None
        
        if location_string.strip().startswith("Flemish Region"):
            # Location is vague - try to use company's locatie_belgie
            try:
                company_master = db.client.table("company_master_data")\
                    .select("locatie_belgie")\
                    .eq("company_id", str(company_id))\
                    .single()\
                    .execute()
                
                if company_master.data and company_master.data.get("locatie_belgie"):
                    company_location = company_master.data["locatie_belgie"]
                    if company_location and company_location.lower() != "niet gevonden":
                        # Create location string from company location
                        override_location_string = f"{company_location}, Belgium"
                        override_location_data = normalize_location(override_location_string)
                        
                        # Check if this location already exists
                        existing_override = db.get_location_by_string(override_location_data["full_location_string"])
                        if existing_override:
                            location_id_override = UUID(existing_override["id"])
                        else:
                            location_id_override = db.insert_location(override_location_data)
                        
                        logger.info(f"Using company location override: {company_location}")
            except Exception as e:
                logger.debug(f"Could not fetch company location: {e}")
        
        # Step 4: Check deduplication (by title + company)
        # Get company name for dedup
        company_result = db.client.table("companies").select("name").eq("id", str(company_id)).single().execute()
        company_name = company_result.data["name"] if company_result.data else ""
        
        # Get source-specific job ID
        source_job_id = job.job_posting_id if source == "linkedin" else job.jobid
        
        # Check if job exists by title + company
        exists, existing_job_id, existing_job_data = check_job_exists_by_dedup(job.job_title, company_name)
        
        job_data = job.to_db_dict(company_id, location_id)
        
        # Add dedup_key and location_id_override to job_data
        dedup_key = create_dedup_key(job.job_title, company_name)
        job_data["dedup_key"] = dedup_key
        job_data["title_normalized"] = job.job_title.lower().strip()
        job_data["location_id_override"] = str(location_id_override) if location_id_override else None
        
        if exists:
            # Job exists - check if THIS source already exists
            job_id = existing_job_id
            
            if check_source_exists_for_job(job_id, source, source_job_id):
                # This source already exists - just update last_seen
                update_source_last_seen(job_id, source)
                
                # Also check if job data needs updating
                if should_update_job(existing_job_data, job_data):
                    db.update_job_posting(job_id, {
                        **job_data,
                        "last_seen_at": datetime.utcnow().isoformat()
                    })
                    status = 'updated'
                    logger.info(f"Updated job: {job.job_title} (source: {source})")
                else:
                    db.update_job_posting(job_id, {
                        "last_seen_at": datetime.utcnow().isoformat()
                    })
                    status = 'updated'
                    logger.debug(f"Re-saw job (no changes): {job.job_title} (source: {source})")
            else:
                # NEW source for existing job - add it!
                add_source_to_job(job_id, source, source_job_id)
                
                # Update job data (merge info from new source)
                db.update_job_posting(job_id, {
                    **job_data,
                    "last_seen_at": datetime.utcnow().isoformat()
                })
                status = 'updated'
                logger.info(f"Added {source} source to existing job: {job.job_title}")
        else:
            # Step 5: Insert new job posting
            job_id = db.insert_job_posting(job_data)
            
            # Add source to job_sources table
            add_source_to_job(job_id, source, source_job_id)
            
            # Step 6: Insert job description
            description_data = job.get_description_dict(job_id)
            db.insert_job_description(description_data)
            
            # Insert job poster if available (LinkedIn only)
            if source == "linkedin":
                poster = job.get_poster()
                if poster:
                    poster_data = poster.to_db_dict(job_id)
                    if poster_data:
                        db.insert_job_poster(poster_data)
            
            # Insert LLM enrichment stub (all NULL fields)
            db.insert_llm_enrichment_stub(job_id)
            
            status = 'new'
            logger.info(f"Inserted new job: {job.job_title} (source: {source})")
        
        # Step 7: Record in scrape history
        db.insert_scrape_history(job_id, scrape_run_id)
        
        # Step 8: Classify job title (async, non-blocking)
        try:
            classification = classify_and_save(str(job_id), job.job_title)
            if classification:
                logger.debug(f"Job title classified as: {classification}")
        except Exception as e:
            # Don't fail the entire job processing if classification fails
            logger.warning(f"Failed to classify job title for {job_id}: {e}")
        
        return ProcessingResult(status=status, job_id=job_id)
        
    except Exception as e:
        logger.exception(f"Error processing job {raw_job.get('job_posting_id', 'unknown')}: {e}")
        return ProcessingResult(status='error', error=str(e))


async def process_jobs_batch(raw_jobs: List[Dict[str, Any]], scrape_run_id: UUID, source: str = "linkedin") -> BatchResult:
    """
    Process multiple jobs in batch with error handling.
    
    Args:
        raw_jobs: List of raw job data from API
        scrape_run_id: UUID of current scrape run
        source: Job source - "linkedin" or "indeed"
    
    Returns:
        BatchResult with counts and details
    """
    logger.info(f"Processing batch of {len(raw_jobs)} {source} jobs")
    
    result = BatchResult()
    
    for i, raw_job in enumerate(raw_jobs, 1):
        if i % 10 == 0:
            logger.info(f"Processed {i}/{len(raw_jobs)} jobs")
        
        job_result = process_job_posting(raw_job, scrape_run_id, source=source)
        result.add(job_result)
    
    logger.success(f"Batch processing complete: {result.summary()}")
    return result
