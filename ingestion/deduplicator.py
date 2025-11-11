"""Deduplication and change tracking for job postings."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from loguru import logger
from database.client import db
import hashlib
import json


def check_job_exists(job_id: str, source: str = "linkedin") -> tuple[bool, Optional[UUID], Optional[Dict]]:
    """
    Check if job posting already exists in database.
    
    Args:
        job_id: Job posting ID (LinkedIn or Indeed)
        source: Job source - "linkedin" or "indeed"
    
    Returns:
        (exists: bool, job_db_id: Optional[UUID], existing_data: Optional[Dict])
    """
    if source == "linkedin":
        existing_job = db.get_job_by_linkedin_id(job_id)
    elif source == "indeed":
        existing_job = db.get_job_by_indeed_id(job_id)
    else:
        raise ValueError(f"Unknown source: {source}")
    
    if existing_job:
        return True, UUID(existing_job["id"]), existing_job
    else:
        return False, None, None


def fields_have_changed(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    fields: List[str]
) -> bool:
    """
    Check if any of the specified fields have changed.
    
    Args:
        old_data: Existing data from database
        new_data: New data from scrape
        fields: List of field names to compare
    
    Returns:
        True if any field has changed
    """
    for field in fields:
        old_value = old_data.get(field)
        new_value = new_data.get(field)
        
        # Handle None comparison
        if old_value != new_value:
            logger.debug(f"Field '{field}' changed: {old_value} -> {new_value}")
            return True
    
    return False


def calculate_data_hash(job_data: Dict[str, Any]) -> str:
    """
    Calculate hash of job data for quick comparison.
    
    Args:
        job_data: Job posting data
    
    Returns:
        MD5 hash string
    """
    # Select fields that matter for change detection
    relevant_fields = [
        "title",
        "num_applicants",
        "base_salary_min",
        "base_salary_max",
        "employment_type",
        "seniority_level"
    ]
    
    # Extract relevant fields in sorted order for consistent hashing
    data_to_hash = {k: job_data.get(k) for k in sorted(relevant_fields)}
    
    # Convert to JSON and hash
    json_str = json.dumps(data_to_hash, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def should_update_job(existing_job: Dict[str, Any], new_job_data: Dict[str, Any]) -> bool:
    """
    Determine if existing job should be updated with new data.
    
    Args:
        existing_job: Current database record
        new_job_data: New data from scrape
    
    Returns:
        True if update is needed
    """
    # Check important fields that might change
    update_fields = [
        "title",
        "num_applicants",
        "base_salary_min",
        "base_salary_max",
        "employment_type",
        "seniority_level",
        "application_available"
    ]
    
    has_changes = fields_have_changed(existing_job, new_job_data, update_fields)
    
    if has_changes:
        # Get job ID based on source
        job_id = existing_job.get('linkedin_job_id') or existing_job.get('indeed_job_id')
        logger.info(f"Job {job_id} has updates")
        return True
    
    return False


def get_changed_fields(existing_job: Dict[str, Any], new_job_data: Dict[str, Any]) -> List[str]:
    """
    Get list of fields that have changed.
    
    Args:
        existing_job: Current database record
        new_job_data: New data from scrape
    
    Returns:
        List of field names that changed
    """
    changed = []
    
    for key in new_job_data.keys():
        if key in existing_job:
            if existing_job[key] != new_job_data[key]:
                changed.append(key)
    
    return changed
