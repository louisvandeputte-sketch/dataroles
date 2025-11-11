"""
Retry helper for LLM enrichment operations.
Implements automatic retry logic for quota errors and other transient failures.
"""

from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


def should_retry_enrichment(
    error_message: Optional[str],
    last_attempt_at: Optional[str],
    retry_delay_hours: int = 24
) -> bool:
    """
    Determine if an enrichment should be retried based on error type and age.
    
    Args:
        error_message: The error message from previous attempt
        last_attempt_at: ISO timestamp of last attempt
        retry_delay_hours: Hours to wait before retry (default 24h)
    
    Returns:
        True if should retry, False otherwise
    """
    # No error = not a retry case
    if not error_message:
        return False
    
    # No timestamp = can't determine age, allow retry
    if not last_attempt_at:
        return True
    
    # Parse timestamp
    try:
        last_attempt = datetime.fromisoformat(last_attempt_at.replace('Z', '+00:00'))
        age = datetime.utcnow() - last_attempt.replace(tzinfo=None)
    except Exception as e:
        logger.warning(f"Could not parse timestamp {last_attempt_at}: {e}")
        return True  # Allow retry if timestamp is invalid
    
    # Check if enough time has passed
    if age < timedelta(hours=retry_delay_hours):
        return False  # Too soon to retry
    
    # Determine retry based on error type
    error_lower = error_message.lower()
    
    # Quota errors: retry after delay
    if "quota" in error_lower or "429" in error_lower:
        logger.info(f"Quota error is {age} old, retrying...")
        return True
    
    # Rate limit errors: retry after delay
    if "rate limit" in error_lower or "too many requests" in error_lower:
        logger.info(f"Rate limit error is {age} old, retrying...")
        return True
    
    # Timeout errors: retry after delay
    if "timeout" in error_lower or "timed out" in error_lower:
        logger.info(f"Timeout error is {age} old, retrying...")
        return True
    
    # Parsing/validation errors: don't retry (likely permanent)
    if any(keyword in error_lower for keyword in ["parse", "json", "invalid", "validation"]):
        logger.debug(f"Parsing/validation error, not retrying: {error_message[:50]}")
        return False
    
    # Unknown errors: retry once after delay
    logger.info(f"Unknown error is {age} old, retrying once...")
    return True


def get_retry_query_filter(
    table_name: str,
    enriched_field: str = "ai_enriched",
    error_field: str = "ai_enrichment_error",
    timestamp_field: str = "ai_enriched_at",
    retry_delay_hours: int = 24
) -> str:
    """
    Generate PostgREST query filter for items that need retry.
    
    Args:
        table_name: Name of the table
        enriched_field: Name of the boolean enriched field
        error_field: Name of the error message field
        timestamp_field: Name of the timestamp field
        retry_delay_hours: Hours to wait before retry
    
    Returns:
        PostgREST filter string for .or_() method
    """
    retry_cutoff = (datetime.utcnow() - timedelta(hours=retry_delay_hours)).isoformat()
    
    # Items that need enrichment:
    # 1. Never enriched (enriched is null or false) AND no error
    # 2. Has error AND error is old enough to retry
    return (
        f"{enriched_field}.is.null,"
        f"{enriched_field}.eq.false,"
        f"and({error_field}.not.is.null,{timestamp_field}.lt.{retry_cutoff})"
    )


def is_quota_error(error_message: Optional[str]) -> bool:
    """Check if error is a quota/rate limit error."""
    if not error_message:
        return False
    error_lower = error_message.lower()
    return "quota" in error_lower or "429" in error_lower or "rate limit" in error_lower
