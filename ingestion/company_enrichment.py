"""Company enrichment using OpenAI LLM to extract company information."""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db


# Initialize OpenAI client with extended timeout (5 minutes for long responses)
client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=300.0  # 5 minutes timeout
)

# Prompt ID for unified company enrichment (includes both info + size classification)
# Version 6: Added multilingual sector (sector_en/nl/fr) and category (category_en/nl/fr)
COMPANY_ENRICHMENT_PROMPT_ID = "pmpt_68fd06175d7c8190bd8767fddcb5486a0e87d16aa5f38bc2"
COMPANY_ENRICHMENT_PROMPT_VERSION = "6"


def enrich_company(company_id: str, company_name: str, company_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Enrich a single company using OpenAI LLM.
    
    Args:
        company_id: UUID of the company
        company_name: Name of the company
        company_url: Optional company website URL
        
    Returns:
        Dictionary with success status and enrichment data or error
    """
    try:
        logger.info(f"Starting enrichment for company: {company_name} (ID: {company_id})")
        
        # Prepare input for the LLM
        company_info = f"Company Name: {company_name}"
        if company_url:
            company_info += f"\nWebsite: {company_url}"
        
        # Call OpenAI with the prompt
        logger.debug(f"Calling OpenAI API with input: {company_info}")
        
        response = client.responses.create(
            prompt={
                "id": COMPANY_ENRICHMENT_PROMPT_ID,
                "version": COMPANY_ENRICHMENT_PROMPT_VERSION
            },
            input=company_info
        )
        
        logger.debug(f"OpenAI response: {response}")
        
        # Extract structured output from response (same as job enrichment)
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
            logger.error(f"Could not extract structured output from API response")
            raise ValueError("Could not extract structured output from API response")
        
        logger.debug(f"Extracted enrichment data: {enrichment_data}")
        
        # Validate required fields
        if not isinstance(enrichment_data, dict):
            raise ValueError(f"LLM response is not a valid dictionary, got: {type(enrichment_data)}")
        
        # Save enrichment data to database
        success = save_enrichment_to_db(company_id, enrichment_data)
        
        if success:
            logger.success(f"Successfully enriched company: {company_name}")
            return {
                "success": True,
                "company_id": company_id,
                "company_name": company_name,
                "data": enrichment_data
            }
        else:
            return {
                "success": False,
                "company_id": company_id,
                "company_name": company_name,
                "error": "Failed to save to database"
            }
            
    except Exception as e:
        logger.error(f"Failed to enrich company {company_name}: {e}")
        
        # Save error to database
        try:
            db.client.table("company_master_data")\
                .upsert({
                    "company_id": company_id,
                    "ai_enriched": False,
                    "ai_enrichment_error": str(e),
                    "ai_enriched_at": datetime.utcnow().isoformat()
                }, on_conflict="company_id")\
                .execute()
        except Exception as db_error:
            logger.error(f"Failed to save error to database: {db_error}")
        
        return {
            "success": False,
            "company_id": company_id,
            "company_name": company_name,
            "error": str(e)
        }


def save_enrichment_to_db(company_id: str, enrichment_data: Dict[str, Any]) -> bool:
    """
    Save enrichment data to company_master_data table.
    
    Args:
        company_id: UUID of the company
        enrichment_data: Dictionary with enrichment fields
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare data for database (includes both company info and size classification)
        db_data = {
            "company_id": company_id,
            # Company info fields
            "bedrijfswebsite": enrichment_data.get("bedrijfswebsite"),
            "jobspagina": enrichment_data.get("jobspagina"),
            "email_hr": enrichment_data.get("email_hr"),
            "email_hr_bron": enrichment_data.get("email_hr_bron"),
            "email_algemeen": enrichment_data.get("email_algemeen"),
            "bedrijfsomschrijving_nl": enrichment_data.get("bedrijfsomschrijving_nl"),
            "bedrijfsomschrijving_fr": enrichment_data.get("bedrijfsomschrijving_fr"),
            "bedrijfsomschrijving_en": enrichment_data.get("bedrijfsomschrijving_en"),
            # Multilingual sector fields (prompt v6)
            "sector_en": enrichment_data.get("sector_en"),
            "sector_nl": enrichment_data.get("sector_nl"),
            "sector_fr": enrichment_data.get("sector_fr"),
            "aantal_werknemers": enrichment_data.get("aantal_werknemers"),
            "ai_enriched": True,
            "ai_enriched_at": datetime.utcnow().isoformat(),
            "ai_enrichment_error": None,
            # Size classification fields (from unified prompt v6)
            # Store English category in size_category for backward compatibility
            "size_category": enrichment_data.get("category_en"),
            # Multilingual category fields
            "category_en": enrichment_data.get("category_en"),
            "category_nl": enrichment_data.get("category_nl"),
            "category_fr": enrichment_data.get("category_fr"),
            "size_confidence": enrichment_data.get("confidence"),
            "size_summary_en": enrichment_data.get("summary", {}).get("en") if isinstance(enrichment_data.get("summary"), dict) else None,
            "size_summary_nl": enrichment_data.get("summary", {}).get("nl") if isinstance(enrichment_data.get("summary"), dict) else None,
            "size_summary_fr": enrichment_data.get("summary", {}).get("fr") if isinstance(enrichment_data.get("summary"), dict) else None,
            "size_key_arguments": enrichment_data.get("key_arguments"),
            "size_sources": enrichment_data.get("sources"),
            "size_enriched_at": datetime.utcnow().isoformat() if enrichment_data.get("category_en") else None,
            "size_enrichment_error": None
        }
        
        # Remove None values
        db_data = {k: v for k, v in db_data.items() if v is not None or k in ["ai_enriched", "ai_enrichment_error"]}
        
        # Upsert to database (insert or update)
        result = db.client.table("company_master_data")\
            .upsert(db_data, on_conflict="company_id")\
            .execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save enrichment data to database: {e}")
        return False


def enrich_companies_batch(company_ids: list) -> Dict[str, Any]:
    """
    Enrich multiple companies in batch.
    
    Args:
        company_ids: List of company UUIDs to enrich
        
    Returns:
        Dictionary with statistics about the enrichment process
    """
    stats = {
        "total": len(company_ids),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    logger.info(f"Starting batch enrichment for {len(company_ids)} companies")
    
    for company_id in company_ids:
        try:
            # Get company details
            company = db.client.table("companies")\
                .select("id, name, logo_url")\
                .eq("id", company_id)\
                .single()\
                .execute()
            
            if not company.data:
                logger.warning(f"Company not found: {company_id}")
                stats["failed"] += 1
                stats["errors"].append({
                    "company_id": company_id,
                    "error": "Company not found"
                })
                continue
            
            company_data = company.data
            company_name = company_data.get("name", "Unknown")
            company_url = company_data.get("logo_url")  # Using logo_url as fallback
            
            # Enrich the company
            result = enrich_company(company_id, company_name, company_url)
            
            if result["success"]:
                stats["successful"] += 1
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
    
    logger.info(f"Batch enrichment complete. Successful: {stats['successful']}, Failed: {stats['failed']}")
    
    return stats


def get_unenriched_companies(limit: int = 100) -> list:
    """
    Get list of companies that haven't been enriched yet.
    
    Args:
        limit: Maximum number of companies to return
        
    Returns:
        List of company IDs
    """
    try:
        # Get companies without master data or with ai_enriched = false
        result = db.client.table("companies")\
            .select("id, company_master_data!left(ai_enriched)")\
            .limit(limit)\
            .execute()
        
        unenriched_ids = []
        for company in result.data:
            master_data = company.get("company_master_data")
            
            # Include if no master data or ai_enriched is False/None
            if not master_data or not master_data.get("ai_enriched"):
                unenriched_ids.append(company["id"])
        
        logger.info(f"Found {len(unenriched_ids)} unenriched companies")
        return unenriched_ids
        
    except Exception as e:
        logger.error(f"Failed to get unenriched companies: {e}")
        return []


def get_enrichment_stats() -> Dict[str, Any]:
    """
    Get statistics about company enrichment.
    
    Returns:
        Dictionary with enrichment statistics
    """
    try:
        # Count total companies
        total_result = db.client.table("companies")\
            .select("id", count="exact")\
            .execute()
        total_companies = total_result.count or 0
        
        # Count enriched companies
        enriched_result = db.client.table("company_master_data")\
            .select("id", count="exact")\
            .eq("ai_enriched", True)\
            .execute()
        enriched_companies = enriched_result.count or 0
        
        # Calculate percentage
        percentage = round((enriched_companies / total_companies * 100), 1) if total_companies > 0 else 0
        
        return {
            "total": total_companies,
            "enriched": enriched_companies,
            "unenriched": total_companies - enriched_companies,
            "percentage_enriched": percentage
        }
        
    except Exception as e:
        logger.error(f"Failed to get enrichment stats: {e}")
        return {
            "total": 0,
            "enriched": 0,
            "unenriched": 0,
            "percentage_enriched": 0
        }
