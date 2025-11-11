"""Deduplication based on title + company (v2)."""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from loguru import logger
from database.client import db
import re


def normalize_title(title: str) -> str:
    """Normalize job title for deduplication."""
    # Lowercase
    normalized = title.lower()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    # Trim
    normalized = normalized.strip()
    return normalized


def create_dedup_key(title: str, company_name: str) -> str:
    """Create deduplication key from title and company."""
    normalized_title = normalize_title(title)
    normalized_company = company_name.lower().strip() if company_name else ""
    return f"{normalized_title}|{normalized_company}"


def check_job_exists_by_dedup(
    title: str,
    company_name: str
) -> Tuple[bool, Optional[UUID], Optional[Dict]]:
    """
    Check if job exists based on title + company deduplication.
    
    Args:
        title: Job title
        company_name: Company name
    
    Returns:
        (exists: bool, job_db_id: Optional[UUID], existing_data: Optional[Dict])
    """
    dedup_key = create_dedup_key(title, company_name)
    
    # Query by dedup_key
    result = db.client.table("job_postings")\
        .select("*")\
        .eq("dedup_key", dedup_key)\
        .execute()
    
    if result.data and len(result.data) > 0:
        existing_job = result.data[0]
        return True, UUID(existing_job["id"]), existing_job
    else:
        return False, None, None


def check_source_exists_for_job(
    job_id: UUID,
    source: str,
    source_job_id: str
) -> bool:
    """
    Check if a specific source already exists for this job.
    
    Args:
        job_id: Job posting UUID
        source: Source name (linkedin/indeed)
        source_job_id: Job ID from source platform
    
    Returns:
        True if source exists
    """
    result = db.client.table("job_sources")\
        .select("id")\
        .eq("job_posting_id", str(job_id))\
        .eq("source", source)\
        .execute()
    
    return len(result.data) > 0


def add_source_to_job(
    job_id: UUID,
    source: str,
    source_job_id: str
) -> None:
    """
    Add a source to an existing job.
    
    Args:
        job_id: Job posting UUID
        source: Source name (linkedin/indeed)
        source_job_id: Job ID from source platform
    """
    try:
        db.client.table("job_sources").insert({
            "job_posting_id": str(job_id),
            "source": source,
            "source_job_id": source_job_id
        }).execute()
        
        logger.info(f"Added {source} source to job {job_id}")
    except Exception as e:
        # Might already exist (race condition)
        logger.warning(f"Could not add source: {e}")


def update_source_last_seen(
    job_id: UUID,
    source: str
) -> None:
    """
    Update last_seen_at for a source.
    
    Args:
        job_id: Job posting UUID
        source: Source name (linkedin/indeed)
    """
    from datetime import datetime
    
    db.client.table("job_sources")\
        .update({"last_seen_at": datetime.now().isoformat()})\
        .eq("job_posting_id", str(job_id))\
        .eq("source", source)\
        .execute()


def fields_have_changed(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    fields: List[str]
) -> bool:
    """Check if any of the specified fields have changed."""
    for field in fields:
        old_value = old_data.get(field)
        new_value = new_data.get(field)
        
        if old_value != new_value:
            logger.debug(f"Field '{field}' changed: {old_value} -> {new_value}")
            return True
    
    return False


def should_update_job(existing_job: Dict[str, Any], new_job_data: Dict[str, Any]) -> bool:
    """Determine if existing job should be updated with new data."""
    update_fields = [
        "title",
        "num_applicants",
        "base_salary_min",
        "base_salary_max",
        "employment_type",
        "seniority_level",
        "application_available"
    ]
    
    return fields_have_changed(existing_job, new_job_data, update_fields)
