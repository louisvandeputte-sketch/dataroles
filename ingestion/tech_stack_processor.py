"""Process and normalize tech stack data from LLM enrichment."""

from typing import List, Dict, Any
from uuid import UUID
from loguru import logger

from database.client import db


def process_tech_stack_for_job(job_id: UUID, enrichment_data: Dict[str, Any]) -> None:
    """
    Process tech stack from LLM enrichment and create masterdata entries + assignments.
    
    This function:
    1. Extracts programming languages and ecosystems from enrichment data
    2. Creates masterdata entries if they don't exist (upsert)
    3. Creates job assignments with requirement levels
    
    Args:
        job_id: UUID of the job posting
        enrichment_data: Enrichment data containing must_have/nice_to_have lists
    """
    try:
        # Extract tech stack from enrichment data
        must_have_languages = enrichment_data.get("must_have_languages", [])
        nice_to_have_languages = enrichment_data.get("nice_to_have_languages", [])
        must_have_ecosystems = enrichment_data.get("must_have_ecosystems", [])
        nice_to_have_ecosystems = enrichment_data.get("nice_to_have_ecosystems", [])
        
        logger.debug(f"Processing tech stack for job {job_id}")
        logger.debug(f"Languages: {must_have_languages + nice_to_have_languages}")
        logger.debug(f"Ecosystems: {must_have_ecosystems + nice_to_have_ecosystems}")
        
        # Process programming languages
        for lang in must_have_languages:
            _process_programming_language(job_id, lang, "must_have")
        
        for lang in nice_to_have_languages:
            _process_programming_language(job_id, lang, "nice_to_have")
        
        # Process ecosystems
        for eco in must_have_ecosystems:
            _process_ecosystem(job_id, eco, "must_have")
        
        for eco in nice_to_have_ecosystems:
            _process_ecosystem(job_id, eco, "nice_to_have")
        
        logger.success(f"Processed tech stack for job {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to process tech stack for job {job_id}: {e}")
        import traceback
        traceback.print_exc()


def _process_programming_language(job_id: UUID, language_name: str, requirement_level: str) -> None:
    """
    Process a single programming language: upsert to masterdata and assign to job.
    
    Args:
        job_id: UUID of the job posting
        language_name: Name of the programming language
        requirement_level: 'must_have' or 'nice_to_have'
    """
    try:
        # Normalize name (trim whitespace)
        language_name = language_name.strip()
        if not language_name:
            return
        
        # Check if language exists in masterdata
        existing = db.get_programming_language_by_name(language_name)
        
        if existing:
            language_id = UUID(existing["id"])
            logger.debug(f"Found existing language: {language_name}")
        else:
            # Create new masterdata entry
            language_data = {
                "name": language_name,
                "display_name": language_name,  # Initially same as name
                "is_active": True
            }
            language_id = db.insert_programming_language(language_data)
            logger.info(f"Created new programming language: {language_name}")
        
        # Assign to job (with duplicate handling via UNIQUE constraint)
        try:
            db.assign_programming_language_to_job(job_id, language_id, requirement_level)
            logger.debug(f"Assigned {language_name} to job {job_id} as {requirement_level}")
        except Exception as e:
            # Duplicate assignment, skip
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.debug(f"Language {language_name} already assigned to job {job_id}")
            else:
                raise
        
    except Exception as e:
        logger.error(f"Failed to process language {language_name}: {e}")


def _process_ecosystem(job_id: UUID, ecosystem_name: str, requirement_level: str) -> None:
    """
    Process a single ecosystem: upsert to masterdata and assign to job.
    
    Args:
        job_id: UUID of the job posting
        ecosystem_name: Name of the ecosystem
        requirement_level: 'must_have' or 'nice_to_have'
    """
    try:
        # Normalize name (trim whitespace)
        ecosystem_name = ecosystem_name.strip()
        if not ecosystem_name:
            return
        
        # Check if ecosystem exists in masterdata
        existing = db.get_ecosystem_by_name(ecosystem_name)
        
        if existing:
            ecosystem_id = UUID(existing["id"])
            logger.debug(f"Found existing ecosystem: {ecosystem_name}")
        else:
            # Create new masterdata entry
            ecosystem_data = {
                "name": ecosystem_name,
                "display_name": ecosystem_name,  # Initially same as name
                "is_active": True
            }
            ecosystem_id = db.insert_ecosystem(ecosystem_data)
            logger.info(f"Created new ecosystem: {ecosystem_name}")
        
        # Assign to job (with duplicate handling via UNIQUE constraint)
        try:
            db.assign_ecosystem_to_job(job_id, ecosystem_id, requirement_level)
            logger.debug(f"Assigned {ecosystem_name} to job {job_id} as {requirement_level}")
        except Exception as e:
            # Duplicate assignment, skip
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.debug(f"Ecosystem {ecosystem_name} already assigned to job {job_id}")
            else:
                raise
        
    except Exception as e:
        logger.error(f"Failed to process ecosystem {ecosystem_name}: {e}")


def get_job_tech_stack(job_id: UUID) -> Dict[str, Any]:
    """
    Get complete tech stack for a job with masterdata details.
    
    Returns:
        Dictionary with programming_languages and ecosystems lists
    """
    try:
        languages = db.get_job_programming_languages(job_id)
        ecosystems = db.get_job_ecosystems(job_id)
        
        return {
            "programming_languages": languages,
            "ecosystems": ecosystems
        }
    except Exception as e:
        logger.error(f"Failed to get tech stack for job {job_id}: {e}")
        return {
            "programming_languages": [],
            "ecosystems": []
        }
