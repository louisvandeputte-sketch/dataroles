"""Job title classifier using OpenAI LLM to pre-screen data relevance."""

from typing import Optional
from datetime import datetime
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db

# OpenAI Responses API configuration
TITLE_CLASSIFIER_PROMPT_ID = "pmpt_690724c8e4f48190a9d249a76325af9d056897bd40d5b2a3"
TITLE_CLASSIFIER_PROMPT_VERSION = "4"

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def classify_job_title(job_title: str) -> tuple[Optional[str], Optional[str]]:
    """
    Classify a job title as 'Data' or 'NIS' (Not In Scope).
    
    Uses OpenAI Responses API with a specialized prompt to determine
    if a job title is data-related.
    
    Args:
        job_title: The job title to classify
    
    Returns:
        Tuple of (classification, error_message):
        - classification: 'Data' if data-related, 'NIS' if not, None if classification fails
        - error_message: Error message if classification failed, None otherwise
    """
    try:
        logger.debug(f"Classifying job title: {job_title}")
        
        # Call OpenAI Responses API
        response = client.responses.create(
            prompt={
                "id": TITLE_CLASSIFIER_PROMPT_ID,
                "version": TITLE_CLASSIFIER_PROMPT_VERSION
            },
            input=job_title
        )
        
        # Extract classification from response
        # Handle ResponseOutputMessage format
        output = response.output
        if isinstance(output, list) and len(output) > 0:
            # List of ResponseOutputMessage objects
            first_msg = output[0]
            if hasattr(first_msg, 'content') and isinstance(first_msg.content, list) and len(first_msg.content) > 0:
                classification = first_msg.content[0].text.strip()
            elif hasattr(first_msg, 'text'):
                classification = first_msg.text.strip()
            else:
                classification = str(first_msg).strip()
        elif hasattr(output, 'content') and isinstance(output.content, list) and len(output.content) > 0:
            # Single ResponseOutputMessage with content array
            classification = output.content[0].text.strip()
        elif hasattr(output, 'text'):
            # Single message object with text attribute
            classification = output.text.strip()
        else:
            # String or unknown format
            classification = str(output).strip()
        
        # Validate output
        if classification not in ['Data', 'NIS']:
            error_msg = f"Unexpected classification: {classification}"
            logger.warning(f"{error_msg} for title: {job_title}")
            # Return None if classification is invalid - don't auto-fill
            return None, error_msg
        
        logger.debug(f"Classification result: {classification}")
        return classification, None
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to classify job title '{job_title}': {error_msg}")
        # Return None on error - don't auto-fill with 'Data'
        return None, error_msg


def save_classification_to_db(job_id: str, classification: str) -> bool:
    """
    Save job title classification to database.
    
    Args:
        job_id: UUID of the job posting
        classification: 'Data' or 'NIS'
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db.client.table("job_postings")\
            .update({
                "title_classification": classification,
                "title_classification_at": datetime.utcnow().isoformat(),
                "title_classification_error": None  # Clear any previous error
            })\
            .eq("id", job_id)\
            .execute()
        
        logger.debug(f"Saved classification '{classification}' for job {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save classification for job {job_id}: {e}")
        return False


def save_classification_error_to_db(job_id: str, error_message: str) -> bool:
    """
    Save classification error to database.
    
    Args:
        job_id: UUID of the job posting
        error_message: Error message describing why classification failed
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db.client.table("job_postings")\
            .update({
                "title_classification_error": error_message,
                "title_classification_at": datetime.utcnow().isoformat()
            })\
            .eq("id", job_id)\
            .execute()
        
        logger.debug(f"Saved classification error for job {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save classification error for job {job_id}: {e}")
        return False


def classify_and_save(job_id: str, job_title: str) -> Optional[str]:
    """
    Classify a job title and save the result to database.
    
    Args:
        job_id: UUID of the job posting
        job_title: The job title to classify
    
    Returns:
        The classification ('Data' or 'NIS'), or None if failed
    """
    classification, error_message = classify_job_title(job_title)
    
    if classification:
        # Classification succeeded - save it
        if save_classification_to_db(job_id, classification):
            return classification
    else:
        # Classification failed - save the error
        if error_message:
            save_classification_error_to_db(job_id, error_message)
    
    return None


def classify_unclassified_jobs(limit: int = 100) -> int:
    """
    Classify all jobs that don't have a title classification yet.
    
    Args:
        limit: Maximum number of jobs to classify in one batch
    
    Returns:
        Number of jobs classified
    """
    try:
        # Get unclassified jobs
        result = db.client.table("job_postings")\
            .select("id, title")\
            .is_("title_classification", "null")\
            .limit(limit)\
            .execute()
        
        if not result.data:
            logger.info("No unclassified jobs found")
            return 0
        
        logger.info(f"Classifying {len(result.data)} jobs...")
        
        classified_count = 0
        for job in result.data:
            classification = classify_and_save(job["id"], job["title"])
            if classification:
                classified_count += 1
        
        logger.success(f"✅ Classified {classified_count}/{len(result.data)} jobs")
        return classified_count
        
    except Exception as e:
        logger.error(f"Failed to classify unclassified jobs: {e}")
        return 0
