"""LLM enrichment service using OpenAI Responses API for job posting analysis."""

import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from config.settings import settings
from database.client import db

# OpenAI Responses API configuration
OPENAI_API_URL = "https://api.openai.com/v1/responses"
PROMPT_TEMPLATE_ID = "pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88"
PROMPT_VERSION = "7"


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
        
        # Prepare API request
        url = "https://api.openai.com/v1/responses"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": {
                "id": PROMPT_TEMPLATE_ID,
                "version": PROMPT_VERSION
            },
            "input": job_description  # Version 7 expects string directly, not object
        }
        
        # Call OpenAI Responses API
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Log response for debugging
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # Extract structured output from response
        enrichment_data = None
        if 'output' in data:
            for item in data['output']:
                if item.get('type') == 'message' and 'content' in item:
                    for content in item['content']:
                        if content.get('type') == 'output_text':
                            # Parse JSON from text output
                            enrichment_data = json.loads(content['text'])
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


def save_enrichment_to_db(job_id: str, enrichment_data: Dict[str, Any]) -> bool:
    """
    Save enrichment data to database.
    
    Args:
        job_id: UUID of the job posting
        enrichment_data: Parsed enrichment data from LLM
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare data for database
        db_data = {
            "type_datarol": enrichment_data.get("type_datarol"),
            "rolniveau": enrichment_data.get("rolniveau"),
            "contract": enrichment_data.get("contract", []),
            "must_have_programmeertalen": enrichment_data.get("must_have_programmeertalen", []),
            "nice_to_have_programmeertalen": enrichment_data.get("nice_to_have_programmeertalen", []),
            "must_have_ecosystemen": enrichment_data.get("must_have_ecosystemen", []),
            "nice_to_have_ecosystemen": enrichment_data.get("nice_to_have_ecosystemen", []),
            "must_have_talen": enrichment_data.get("must_have_talen", []),
            "nice_to_have_talen": enrichment_data.get("nice_to_have_talen", []),
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