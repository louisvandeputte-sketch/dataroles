"""Consulting company classifier using OpenAI LLM."""

import json
from typing import Dict, Any
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db

# Initialize OpenAI client
import os
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY") or settings.openai_api_key,
    timeout=60.0
)

# Prompt ID for consulting classification
CONSULTING_PROMPT_ID = "pmpt_6916e9315b0481979ae85ac397cf75900d3a633ba7b777d8"
CONSULTING_PROMPT_VERSION = "2"


def classify_consulting(company_id: str, company_name: str, company_description: str = None) -> Dict[str, Any]:
    """
    Classify if a company is primarily a consulting firm.
    
    Args:
        company_id: UUID of the company
        company_name: Name of the company
        company_description: Optional company description
        
    Returns:
        Dictionary with success status and classification result
    """
    try:
        logger.info(f"Starting consulting classification for company: {company_name} (ID: {company_id})")
        
        # Prepare input - use description if available, otherwise just name
        if company_description:
            company_info = f"Company: {company_name}\nDescription: {company_description}"
        else:
            company_info = f"Company: {company_name}"
        
        logger.debug(f"Calling OpenAI API with input: {company_info}")
        
        # Call OpenAI with the prompt
        response = client.responses.create(
            prompt={
                "id": CONSULTING_PROMPT_ID,
                "version": CONSULTING_PROMPT_VERSION
            },
            input=company_info
        )
        
        logger.debug(f"OpenAI response: {response}")
        
        # Extract structured output from response
        classification_data = None
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message' and hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'type') and content.type == 'output_text':
                            # Parse JSON from text output
                            classification_data = json.loads(content.text)
                            break
                if classification_data:
                    break
        
        if not classification_data:
            logger.error(f"Could not extract structured output from API response")
            raise ValueError("Could not extract structured output from API response")
        
        logger.debug(f"Extracted classification data: {classification_data}")
        
        # Validate required fields
        if not isinstance(classification_data, dict):
            raise ValueError(f"LLM response is not a valid dictionary, got: {type(classification_data)}")
        
        if 'Consulting' not in classification_data:
            raise ValueError(f"Missing 'Consulting' field in response: {classification_data}")
        
        is_consulting = classification_data.get('Consulting', False)
        reasoning = classification_data.get('reasoning', '')
        
        # Update database
        success = update_consulting_status(company_id, is_consulting, reasoning)
        
        if success:
            logger.success(f"Successfully classified company: {company_name} - Consulting: {is_consulting}")
            return {
                "success": True,
                "company_id": company_id,
                "company_name": company_name,
                "is_consulting": is_consulting,
                "reasoning": reasoning
            }
        else:
            raise Exception("Failed to update database")
            
    except Exception as e:
        logger.error(f"Failed to classify company {company_name}: {e}")
        return {
            "success": False,
            "company_id": company_id,
            "company_name": company_name,
            "error": str(e)
        }


def update_consulting_status(company_id: str, is_consulting: bool, reasoning: str = None) -> bool:
    """
    Update the is_consulting field in company_master_data.
    
    Args:
        company_id: UUID of the company
        is_consulting: Boolean indicating if company is consulting
        reasoning: Optional reasoning for the classification
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if master data exists
        existing = db.client.table("company_master_data")\
            .select("id")\
            .eq("company_id", company_id)\
            .execute()
        
        update_data = {
            "is_consulting": is_consulting
        }
        
        if reasoning:
            update_data["consulting_reasoning"] = reasoning
        
        if existing.data:
            # Update existing master data
            db.client.table("company_master_data")\
                .update(update_data)\
                .eq("company_id", company_id)\
                .execute()
            logger.debug(f"Updated existing master data for company {company_id}")
        else:
            # Create new master data
            update_data["company_id"] = company_id
            db.client.table("company_master_data")\
                .insert(update_data)\
                .execute()
            logger.debug(f"Created new master data for company {company_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update consulting status in database: {e}")
        return False


def classify_consulting_batch(company_ids: list) -> Dict[str, Any]:
    """
    Classify multiple companies for consulting status.
    
    Args:
        company_ids: List of company UUIDs
        
    Returns:
        Dictionary with statistics about the classification
    """
    stats = {
        "total": len(company_ids),
        "successful": 0,
        "failed": 0,
        "consulting": 0,
        "not_consulting": 0,
        "errors": []
    }
    
    for company_id in company_ids:
        try:
            # Get company info
            company = db.client.table("companies")\
                .select("id, name, company_master_data(bedrijfsomschrijving_en)")\
                .eq("id", company_id)\
                .single()\
                .execute()
            
            if not company.data:
                logger.warning(f"Company not found: {company_id}")
                stats["failed"] += 1
                continue
            
            company_name = company.data.get("name", "Unknown")
            
            # Get description if available
            description = None
            if company.data.get("company_master_data"):
                master_data = company.data["company_master_data"]
                if isinstance(master_data, list) and len(master_data) > 0:
                    description = master_data[0].get("bedrijfsomschrijving_en")
                elif isinstance(master_data, dict):
                    description = master_data.get("bedrijfsomschrijving_en")
            
            # Classify
            result = classify_consulting(company_id, company_name, description)
            
            if result["success"]:
                stats["successful"] += 1
                if result["is_consulting"]:
                    stats["consulting"] += 1
                else:
                    stats["not_consulting"] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "error": result.get("error", "Unknown error")
                })
                
        except Exception as e:
            logger.error(f"Error processing company {company_id}: {e}")
            stats["failed"] += 1
            stats["errors"].append({
                "company_id": company_id,
                "error": str(e)
            })
    
    logger.info(f"Batch consulting classification complete: {stats['successful']} successful, {stats['failed']} failed")
    return stats
