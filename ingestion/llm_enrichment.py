"""LLM enrichment service using OpenAI Responses API for job posting analysis."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db

# OpenAI Responses API configuration
PROMPT_TEMPLATE_ID = "pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88"
PROMPT_VERSION = "12"

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def enrich_job_with_llm(job_id: str, job_description: str) -> Optional[Dict[str, Any]]:
    """
    Enrich a single job posting using OpenAI Responses API.
    
    Args:
        job_id: UUID of the job posting
        job_description: Full text description of the job
    
    Returns:
        Parsed enrichment data or None if failed
    """
    try:
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
            raise ValueError(f"Could not extract structured output from API response")
        
        logger.success(f"Successfully enriched job {job_id}")
        logger.debug(f"Enrichment data: {enrichment_data}")
        
        return enrichment_data
        
    except Exception as e:
        logger.error(f"Failed to enrich job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


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
        # New format (v18): English fields at root level, translations in i18n
        # Root level fields (English canonical values)
        data_role_type = enrichment_data.get("data_role_type")
        role_level = enrichment_data.get("role_level", [])
        seniority = enrichment_data.get("seniority", [])
        contract = enrichment_data.get("contract", [])
        sourcing_type = enrichment_data.get("sourcing_type")
        summary_short_en = enrichment_data.get("summary_short")
        summary_long_en = enrichment_data.get("summary_long")
        must_have_languages = enrichment_data.get("must_have_languages", [])
        nice_to_have_languages = enrichment_data.get("nice_to_have_languages", [])
        must_have_ecosystems = enrichment_data.get("must_have_ecosystems", [])
        nice_to_have_ecosystems = enrichment_data.get("nice_to_have_ecosystems", [])
        must_have_spoken = enrichment_data.get("must_have_spoken_languages", [])
        nice_to_have_spoken = enrichment_data.get("nice_to_have_spoken_languages", [])
        
        # Extract i18n translations
        i18n = enrichment_data.get("i18n", {})
        nl_data = i18n.get("nl", {})
        fr_data = i18n.get("fr", {})
        
        # Log for debugging
        logger.debug(f"i18n keys: {list(i18n.keys())}")
        logger.debug(f"nl_data keys: {list(nl_data.keys()) if nl_data else 'None'}")
        logger.debug(f"fr_data keys: {list(fr_data.keys()) if fr_data else 'None'}")
        
        # Prepare data for database (multilingual schema)
        db_data = {
            # English summaries (canonical)
            "samenvatting_kort_en": summary_short_en,
            "samenvatting_lang_en": summary_long_en,
            
            # Dutch translations
            "samenvatting_kort_nl": nl_data.get("summary_short"),
            "samenvatting_lang_nl": nl_data.get("summary_long"),
            
            # French translations
            "samenvatting_kort_fr": fr_data.get("summary_short"),
            "samenvatting_lang_fr": fr_data.get("summary_long"),
            
            # Labels as JSONB (contains all language-specific label translations)
            "labels": json.dumps({
                "en": {
                    "data_role_type": data_role_type,
                    "role_level": role_level,
                    "seniority": seniority,
                    "contract": contract,
                    "sourcing_type": sourcing_type
                },
                "nl": nl_data,  # Contains translated labels
                "fr": fr_data   # Contains translated labels
            }),
            
            # Legacy fields for backward compatibility (use English canonical values)
            "type_datarol": data_role_type,
            "rolniveau": _format_array_for_postgres(role_level),
            "seniority": _format_array_for_postgres(seniority),
            "contract": _format_array_for_postgres(contract),
            "sourcing_type": sourcing_type,
            "samenvatting_kort": summary_short_en,  # Legacy: use English
            "samenvatting_lang": summary_long_en,   # Legacy: use English
            
            # Programming languages and ecosystems (language-agnostic)
            "must_have_programmeertalen": _format_array_for_postgres(must_have_languages),
            "nice_to_have_programmeertalen": _format_array_for_postgres(nice_to_have_languages),
            "must_have_ecosystemen": _format_array_for_postgres(must_have_ecosystems),
            "nice_to_have_ecosystemen": _format_array_for_postgres(nice_to_have_ecosystems),
            
            # Spoken/written languages
            "must_have_talen": _format_array_for_postgres(must_have_spoken),
            "nice_to_have_talen": _format_array_for_postgres(nice_to_have_spoken),
            
            "enrichment_completed_at": datetime.utcnow().isoformat(),
            "enrichment_model_version": f"prompt-{PROMPT_TEMPLATE_ID}-v{PROMPT_VERSION}"
        }
        
        # Update llm_enrichment table
        result = db.client.table("llm_enrichment")\
            .update(db_data)\
            .eq("job_posting_id", job_id)\
            .execute()
        
        if result.data:
            logger.success(f"Saved enrichment for job {job_id}")
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
                .single()\
                .execute()
            
            if existing.data and existing.data.get("enrichment_completed_at"):
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": "Already enriched. Use force=True to re-enrich."
                }
        
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
        enrichment_data = enrich_job_with_llm(job_id, description)
        
        if not enrichment_data:
            return {
                "success": False,
                "job_id": job_id,
                "error": "LLM enrichment failed"
            }
        
        # Save to database
        success = save_enrichment_to_db(job_id, enrichment_data)
        
        if success:
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


def get_unenriched_jobs(limit: int = 100) -> List[str]:
    """
    Get list of job IDs that need enrichment.
    
    Args:
        limit: Maximum number of jobs to return
    
    Returns:
        List of job UUIDs
    """
    try:
        # Find jobs where enrichment_completed_at is NULL
        result = db.client.table("llm_enrichment")\
            .select("job_posting_id")\
            .is_("enrichment_completed_at", "null")\
            .limit(limit)\
            .execute()
        
        job_ids = [row["job_posting_id"] for row in result.data]
        logger.info(f"Found {len(job_ids)} unenriched jobs")
        
        return job_ids
        
    except Exception as e:
        logger.error(f"Failed to get unenriched jobs: {e}")
        return []


def batch_enrich_jobs(job_ids: List[str]) -> Dict[str, Any]:
    """
    Enrich multiple jobs in batch.
    
    Args:
        job_ids: List of job UUIDs to enrich
    
    Returns:
        Statistics dict with success/failure counts and details
    """
    stats = {
        "total": len(job_ids),
        "successful": 0,
        "failed": 0,
        "results": []
    }
    
    logger.info(f"Starting batch enrichment for {len(job_ids)} jobs")
    
    for i, job_id in enumerate(job_ids, 1):
        logger.info(f"Processing job {i}/{len(job_ids)}: {job_id}")
        
        result = process_job_enrichment(job_id)
        stats["results"].append(result)
        
        if result["success"]:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
    
    logger.success(f"Batch enrichment complete: {stats['successful']} successful, {stats['failed']} failed")
    return stats