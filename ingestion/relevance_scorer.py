"""
Relevance scorer for programming languages and ecosystems.
Uses LLM to score relevance (0-100) for data professionals.
"""

from typing import Optional
from loguru import logger
from openai import OpenAI

from config.settings import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)

# OpenAI Responses API configuration
RELEVANCE_PROMPT_ID = "pmpt_69126115f9d081909035c9bb6b27324409e4a060c0961fa7"
RELEVANCE_PROMPT_VERSION = "2"


def score_relevance(name: str) -> tuple[Optional[int], Optional[str]]:
    """
    Score the relevance of a programming language, tool, or ecosystem for data professionals.
    
    Args:
        name: Name of the programming language, tool, or ecosystem
    
    Returns:
        Tuple of (score, error_message):
        - score: Integer between 0-100, or None if scoring failed
        - error_message: Error message if scoring failed, None otherwise
    """
    try:
        logger.debug(f"Scoring relevance for: {name}")
        
        # Call OpenAI Responses API
        response = client.responses.create(
            prompt={
                "id": RELEVANCE_PROMPT_ID,
                "version": RELEVANCE_PROMPT_VERSION
            },
            input=name
        )
        
        # Extract score from response
        # Handle ResponseOutputMessage format
        output = response.output
        if isinstance(output, list) and len(output) > 0:
            # List of ResponseOutputMessage objects
            first_msg = output[0]
            if hasattr(first_msg, 'content') and isinstance(first_msg.content, list) and len(first_msg.content) > 0:
                score_text = first_msg.content[0].text.strip()
            elif hasattr(first_msg, 'text'):
                score_text = first_msg.text.strip()
            else:
                score_text = str(first_msg).strip()
        elif hasattr(output, 'content') and isinstance(output.content, list) and len(output.content) > 0:
            # Single ResponseOutputMessage with content array
            score_text = output.content[0].text.strip()
        elif hasattr(output, 'text'):
            # Single message object with text attribute
            score_text = output.text.strip()
        else:
            # String or unknown format
            score_text = str(output).strip()
        
        # Parse as integer
        try:
            score = int(score_text)
            
            # Validate range
            if not (0 <= score <= 100):
                error_msg = f"Score out of range: {score}"
                logger.warning(f"{error_msg} for: {name}")
                return None, error_msg
            
            logger.debug(f"Relevance score for '{name}': {score}")
            return score, None
            
        except ValueError:
            error_msg = f"Invalid score format: {score_text}"
            logger.warning(f"{error_msg} for: {name}")
            return None, error_msg
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to score relevance for '{name}': {error_msg}")
        return None, error_msg


def score_programming_language(language_id: str, name: str) -> bool:
    """
    Score a programming language and save to database.
    
    Args:
        language_id: UUID of the programming language
        name: Name of the programming language
    
    Returns:
        True if successful, False otherwise
    """
    from database.client import db
    
    try:
        score, error = score_relevance(name)
        
        if score is not None:
            # Save score to database
            db.client.table("programming_languages")\
                .update({"relevance_score": score})\
                .eq("id", language_id)\
                .execute()
            
            logger.success(f"✅ Scored '{name}': {score}/100")
            return True
        else:
            logger.warning(f"⚠️ Failed to score '{name}': {error}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save score for '{name}': {e}")
        return False


def score_ecosystem(ecosystem_id: str, name: str) -> bool:
    """
    Score an ecosystem and save to database.
    
    Args:
        ecosystem_id: UUID of the ecosystem
        name: Name of the ecosystem
    
    Returns:
        True if successful, False otherwise
    """
    from database.client import db
    
    try:
        score, error = score_relevance(name)
        
        if score is not None:
            # Save score to database
            db.client.table("ecosystems")\
                .update({"relevance_score": score})\
                .eq("id", ecosystem_id)\
                .execute()
            
            logger.success(f"✅ Scored '{name}': {score}/100")
            return True
        else:
            logger.warning(f"⚠️ Failed to score '{name}': {error}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save score for '{name}': {e}")
        return False
