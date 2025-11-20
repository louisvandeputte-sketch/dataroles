"""LLM enrichment service using OpenAI Responses API for job posting analysis."""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from openai import OpenAI, RateLimitError, APIError

from config.settings import settings
from database.client import db

# OpenAI Responses API configuration
PROMPT_TEMPLATE_ID = "pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88"
PROMPT_VERSION = "18"  # Latest version with all v17 features

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def enrich_job_with_llm(job_id: str, job_description: str, max_retries: int = 3) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Enrich a single job posting using OpenAI Responses API with retry logic.
    
    Args:
        job_id: UUID of the job posting
        job_description: Full text description of the job
        max_retries: Maximum number of retry attempts for rate limits
    
    Returns:
        Tuple of (enrichment_data, error_message):
        - enrichment_data: Parsed enrichment data or None if failed
        - error_message: Error message if failed, None if successful
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} for job {job_id}")
            else:
                logger.info(f"Enriching job {job_id} with LLM")
            
            # Call OpenAI Responses API using the new SDK
            response = client.responses.create(
                prompt={
                    "id": PROMPT_TEMPLATE_ID,
                    "version": PROMPT_VERSION
                },
                input=job_description
            )
            
            # Extract structured output from response
            enrichment_data = None
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'type') and item.type == 'message' and hasattr(item, 'content'):
                        for content in item.content:
                            if hasattr(content, 'type') and content.type == 'output_text':
                                # Parse JSON from text output
                                enrichment_data = json.loads(content.text)
                                break
                    if enrichment_data:
                        break
            
            if not enrichment_data:
                error_msg = "Could not extract structured output from API response"
                logger.error(f"Failed to enrich job {job_id}: {error_msg}")
                return None, error_msg
            
            logger.success(f"Successfully enriched job {job_id}")
            logger.debug(f"Enrichment data: {enrichment_data}")
            
            return enrichment_data, None
            
        except RateLimitError as e:
            last_error = e
            wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
            logger.warning(f"Rate limit hit for job {job_id}. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
            time.sleep(wait_time)
            continue
            
        except json.JSONDecodeError as e:
            # JSON parsing errors are not retryable
            error_msg = f"Invalid JSON in LLM response: {str(e)}"
            logger.error(f"Failed to enrich job {job_id}: {error_msg}")
            return None, error_msg
            
        except APIError as e:
            last_error = e
            # Retry on API errors with backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 3  # 3s, 6s, 12s
                logger.warning(f"API error for job {job_id}: {str(e)}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                error_msg = f"API error after {max_retries} attempts: {str(e)}"
                logger.error(f"Failed to enrich job {job_id}: {error_msg}")
                return None, error_msg
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to enrich job {job_id}: {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg
    
    # All retries exhausted
    error_msg = f"Rate limit exceeded after {max_retries} attempts: {str(last_error)}"
    logger.error(f"Failed to enrich job {job_id}: {error_msg}")
    return None, error_msg


def _format_array_for_postgres(arr: List[str]) -> str:
    """
    Format a Python list as a PostgreSQL array string.
    Supabase Python client doesn't handle TEXT[] arrays correctly, so we format manually.
    """
    if not arr:
        return "{}"
    # Escape quotes and format as PostgreSQL array
    escaped = [item.replace('"', '\\"') for item in arr]
    return "{" + ",".join(f'"{item}"' for item in escaped) + "}"


def save_enrichment_error_to_db(job_id: str, error_message: str) -> bool:
    """
    Save enrichment error to database.
    
    Args:
        job_id: UUID of the job posting
        error_message: Error message describing why enrichment failed
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db.client.table("llm_enrichment")\
            .update({
                "enrichment_error": error_message,
                "enrichment_completed_at": datetime.utcnow().isoformat()
            })\
            .eq("job_posting_id", job_id)\
            .execute()
        
        logger.debug(f"Saved enrichment error for job {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save enrichment error for job {job_id}: {e}")
        return False


def save_enrichment_to_db(job_id: str, enrichment_data: Dict[str, Any]) -> bool:
    """
    Save enrichment data to database.
    
    Args:
        job_id: UUID of the job posting
        enrichment_data: Parsed enrichment data from LLM (v18 format: English root + i18n translations)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # New format (v17): English fields at root level, translations in labels
        # Root level fields (English canonical values)
        data_role_type = enrichment_data.get("data_role_type")
        role_level = enrichment_data.get("role_level", [])
        seniority = enrichment_data.get("seniority", [])
        contract = enrichment_data.get("contract", [])
        sourcing_type = enrichment_data.get("sourcing_type")
        remote_work_policy = enrichment_data.get("remote_work_policy")
        
        # Summaries (3 languages at root level)
        summary_short_en = enrichment_data.get("summary_short")
        summary_long_en = enrichment_data.get("summary_long")
        summary_short_nl = enrichment_data.get("summary_short_nl")
        summary_long_nl = enrichment_data.get("summary_long_nl")
        summary_short_fr = enrichment_data.get("summary_short_fr")
        summary_long_fr = enrichment_data.get("summary_long_fr")
        
        # Tech stack
        must_have_languages = enrichment_data.get("must_have_languages", [])
        nice_to_have_languages = enrichment_data.get("nice_to_have_languages", [])
        must_have_ecosystems = enrichment_data.get("must_have_ecosystems", [])
        nice_to_have_ecosystems = enrichment_data.get("nice_to_have_ecosystems", [])
        
        # Spoken languages (canonical English names)
        must_have_spoken = enrichment_data.get("must_have_spoken_languages", [])
        nice_to_have_spoken = enrichment_data.get("nice_to_have_spoken_languages", [])
        
        # Individual perk fields (v17)
        perk_remote_policy = enrichment_data.get("perk_remote_policy")
        perk_salary_range = enrichment_data.get("perk_salary_range")
        perk_company_car = enrichment_data.get("perk_company_car")
        perk_hospitalization_insurance = enrichment_data.get("perk_hospitalization_insurance")
        perk_training_budget = enrichment_data.get("perk_training_budget")
        perk_team_events = enrichment_data.get("perk_team_events")
        
        # Extract labels object (contains all translations)
        labels_data = enrichment_data.get("labels", {})
        
        # Log for debugging
        logger.debug(f"labels keys: {list(labels_data.keys())}")
        logger.debug(f"Perk values: remote={perk_remote_policy}, salary={perk_salary_range}, car={perk_company_car}")
        
        # Prepare data for database (v17 schema)
        db_data = {
            # Summaries (3 languages)
            "samenvatting_kort_en": summary_short_en,
            "samenvatting_lang_en": summary_long_en,
            "samenvatting_kort_nl": summary_short_nl,
            "samenvatting_lang_nl": summary_long_nl,
            "samenvatting_kort_fr": summary_short_fr,
            "samenvatting_lang_fr": summary_long_fr,
            
            # Labels as JSONB (contains all translations including perks and spoken languages)
            "labels": json.dumps(labels_data) if labels_data else None,
            
            # Legacy fields for backward compatibility (use English canonical values)
            "type_datarol": data_role_type,
            "rolniveau": _format_array_for_postgres(role_level),
            "seniority": _format_array_for_postgres(seniority),
            "contract": _format_array_for_postgres(contract),
            "sourcing_type": sourcing_type,
            "samenvatting_kort": summary_short_en,  # Legacy: use English
            "samenvatting_lang": summary_long_en,   # Legacy: use English
            
            # Programming languages and ecosystems (language-agnostic canonical names)
            "must_have_programmeertalen": _format_array_for_postgres(must_have_languages),
            "nice_to_have_programmeertalen": _format_array_for_postgres(nice_to_have_languages),
            "must_have_ecosystemen": _format_array_for_postgres(must_have_ecosystems),
            "nice_to_have_ecosystemen": _format_array_for_postgres(nice_to_have_ecosystems),
            
            # Spoken/written languages (canonical English names)
            "must_have_talen": _format_array_for_postgres(must_have_spoken),
            "nice_to_have_talen": _format_array_for_postgres(nice_to_have_spoken),
            
            # Remote work policy
            "remote_work_policy": remote_work_policy,
            
            # Individual perk columns (v17)
            "perk_remote_policy": perk_remote_policy,
            "perk_salary_range": perk_salary_range,
            "perk_company_car": perk_company_car,
            "perk_hospitalization_insurance": perk_hospitalization_insurance,
            "perk_training_budget": perk_training_budget,
            "perk_team_events": perk_team_events,
            
            # Metadata
            "enrichment_completed_at": datetime.utcnow().isoformat(),
            "enrichment_error": None,  # Clear any previous error
            "enrichment_model_version": f"prompt-{PROMPT_TEMPLATE_ID}-v{PROMPT_VERSION}"
        }
        
        # Update llm_enrichment table
        result = db.client.table("llm_enrichment")\
            .update(db_data)\
            .eq("job_posting_id", job_id)\
            .execute()
        
        if result.data:
            # Mark job for re-ranking after enrichment
            db.client.table("job_postings")\
                .update({"needs_ranking": True})\
                .eq("id", job_id)\
                .execute()
            
            logger.success(f"Saved enrichment for job {job_id} and marked for re-ranking")
            return True
        else:
            logger.error(f"No enrichment record found for job {job_id}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save enrichment for job {job_id}: {e}")
        logger.error(f"Enrichment data keys: {list(enrichment_data.keys())}")
        logger.error(f"DB data keys: {list(db_data.keys()) if 'db_data' in locals() else 'db_data not created'}")
        import traceback
        traceback.print_exc()
        return False


def process_job_enrichment(job_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Complete enrichment workflow for a single job.
    
    Args:
        job_id: UUID of the job posting
        force: If True, re-enrich even if already enriched
    
    Returns:
        Result dict with success status and message
    """
    try:
        # Check if already enriched (unless force=True)
        if not force:
            existing = db.client.table("llm_enrichment")\
                .select("enrichment_completed_at")\
                .eq("job_posting_id", job_id)\
                .maybe_single()\
                .execute()
            
            if existing.data and existing.data.get("enrichment_completed_at"):
                logger.debug(f"Job {job_id} already enriched, skipping (use force=True to re-enrich)")
                return {
                    "success": True,  # Changed to True so caller knows to skip
                    "job_id": job_id,
                    "skipped": True,
                    "message": "Already enriched"
                }
        else:
            logger.info(f"Force re-enrichment enabled for job {job_id}")
        
        # Get job description
        result = db.client.table("job_descriptions")\
            .select("full_description_text")\
            .eq("job_posting_id", job_id)\
            .single()\
            .execute()
        
        if not result.data or not result.data.get("full_description_text"):
            return {
                "success": False,
                "job_id": job_id,
                "error": "No description found"
            }
        
        description = result.data["full_description_text"]
        
        # Enrich with LLM
        enrichment_data, error_message = enrich_job_with_llm(job_id, description)
        
        if not enrichment_data:
            # Save error to database
            save_enrichment_error_to_db(job_id, error_message or "LLM enrichment failed")
            return {
                "success": False,
                "job_id": job_id,
                "error": error_message or "LLM enrichment failed"
            }
        
        # Save to database
        success = save_enrichment_to_db(job_id, enrichment_data)
        
        if success:
            # Process tech stack (programming languages and ecosystems)
            try:
                from ingestion.tech_stack_processor import process_tech_stack_for_job
                from uuid import UUID
                process_tech_stack_for_job(UUID(job_id), enrichment_data)
            except Exception as e:
                logger.warning(f"Failed to process tech stack for job {job_id}: {e}")
                # Don't fail the entire enrichment if tech stack processing fails
            
            return {
                "success": True,
                "job_id": job_id,
                "data": enrichment_data
            }
        else:
            return {
                "success": False,
                "job_id": job_id,
                "error": "Failed to save to database"
            }
        
    except Exception as e:
        logger.error(f"Failed to process enrichment for job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e)
        }


def get_unenriched_jobs(limit: int = 100, include_retries: bool = True) -> List[str]:
    """
    Get list of job IDs that need enrichment.
    Only returns jobs with title_classification = 'Data'.
    Includes automatic retry for quota errors after 24h.
    
    Args:
        limit: Maximum number of jobs to return
        include_retries: If True, include jobs with old errors (>24h) for retry
    
    Returns:
        List of job UUIDs
    """
    try:
        from datetime import datetime, timedelta
        
        if include_retries:
            # Calculate retry cutoff (24 hours ago)
            retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Find jobs that need enrichment:
            # 1. Never enriched (enrichment_completed_at is NULL) AND no error
            # 2. Has error AND error is old enough to retry (>24h)
            # AND title_classification = 'Data'
            result = db.client.table("llm_enrichment")\
                .select("job_posting_id, enrichment_error, enrichment_completed_at, job_postings!inner(title_classification)")\
                .or_(
                    f"and(enrichment_completed_at.is.null,enrichment_error.is.null),"
                    f"and(enrichment_error.not.is.null,enrichment_completed_at.lt.{retry_cutoff})"
                )\
                .eq("job_postings.title_classification", "Data")\
                .limit(limit)\
                .execute()
        else:
            # Original behavior: only new jobs
            result = db.client.table("llm_enrichment")\
                .select("job_posting_id, job_postings!inner(title_classification)")\
                .is_("enrichment_completed_at", "null")\
                .is_("enrichment_error", "null")\
                .eq("job_postings.title_classification", "Data")\
                .limit(limit)\
                .execute()
        
        job_ids = [row["job_posting_id"] for row in result.data]
        
        if include_retries and result.data:
            retry_count = sum(1 for row in result.data if row.get("enrichment_error"))
            logger.info(f"Found {len(job_ids)} unenriched 'Data' jobs ({len(job_ids) - retry_count} new, {retry_count} retries)")
        else:
            logger.info(f"Found {len(job_ids)} unenriched 'Data' jobs")
        
        return job_ids
        
    except Exception as e:
        logger.error(f"Failed to get unenriched jobs: {e}")
        return []


def batch_enrich_jobs(job_ids: List[str], batch_size: int = 50, delay_between_jobs: float = 1.0) -> Dict[str, Any]:
    """
    Enrich multiple jobs in batch with rate limiting.
    
    Args:
        job_ids: List of job UUIDs to enrich
        batch_size: Maximum number of jobs to process (default: 50)
        delay_between_jobs: Delay in seconds between each job to avoid rate limits (default: 1.0s)
    
    Returns:
        Statistics dict with success/failure counts and details
    """
    # Limit batch size
    if len(job_ids) > batch_size:
        logger.warning(f"Batch size limited from {len(job_ids)} to {batch_size} jobs")
        job_ids = job_ids[:batch_size]
    
    stats = {
        "total": len(job_ids),
        "successful": 0,
        "failed": 0,
        "rate_limited": 0,
        "results": []
    }
    
    logger.info(f"Starting batch enrichment for {len(job_ids)} jobs (max batch size: {batch_size})")
    
    for i, job_id in enumerate(job_ids, 1):
        logger.info(f"Processing job {i}/{len(job_ids)}: {job_id}")
        
        result = process_job_enrichment(job_id)
        stats["results"].append(result)
        
        if result["success"]:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
            # Check if it's a rate limit error
            if result.get("error") and "rate limit" in result["error"].lower():
                stats["rate_limited"] += 1
        
        # Add delay between jobs to avoid rate limits (except for last job)
        if i < len(job_ids):
            logger.debug(f"Waiting {delay_between_jobs}s before next job...")
            time.sleep(delay_between_jobs)
    
    logger.success(f"Batch enrichment complete: {stats['successful']} successful, {stats['failed']} failed, {stats['rate_limited']} rate limited")
    return stats