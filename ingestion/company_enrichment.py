"""Company enrichment using OpenAI LLM to extract company information."""

import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db


# Initialize OpenAI client with extended timeout (5 minutes for long responses)
# Note: We read from os.environ directly to avoid caching issues when API key is updated
import os
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY") or settings.openai_api_key,
    timeout=300.0  # 5 minutes timeout
)

# Prompt ID for unified company enrichment (includes both info + size classification)
# Version 25: Belgian location field (locatie_belgie)
#             - locatie_belgie: Belgian office city in native language (e.g., "Gent", "Bruxelles")
#             - For international companies: main Belgian HQ or largest Belgian office
#             - Improved sector rules: Title Case, 1-2 words max, no lists
#             - Funding factlet must be first if funding exists
#             - Stricter maturity classification: always choose best-fit, avoid "unknown"
# Version 20: size_category canonical field, auto-translated to category_nl/en/fr
# Version 15: Added hiring_model field to distinguish recruitment vs direct hiring
COMPANY_ENRICHMENT_PROMPT_ID = "pmpt_68fd06175d7c8190bd8767fddcb5486a0e87d16aa5f38bc2"
COMPANY_ENRICHMENT_PROMPT_VERSION = "25"  # v25: locatie_belgie field, stricter classification


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
        
        # Log all keys to debug location fields
        logger.info(f"LLM response keys for {company_name}: {list(enrichment_data.keys())}")
        if "locatie_belgie" in enrichment_data:
            location = enrichment_data.get('locatie_belgie')
            if location and location != "[locatie]":
                logger.info(f"✅ Belgian location found: {location}")
            else:
                logger.warning(f"⚠️ Location placeholder returned: {location}")
        else:
            logger.warning(f"⚠️ No locatie_belgie field in LLM response for {company_name}")
        
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
        # Extract maturity data (prompt v12 nests it under "maturity")
        maturity = enrichment_data.get("maturity", {})
        
        # Extract category data (prompt v12 can also nest categories as object: {en, nl, fr})
        category_obj = enrichment_data.get("category", {})
        
        # Map field names from prompt v12 output to database columns
        # Prompt v12 uses: website, careers_page, description_en/nl/fr, employee_count_range, factlets
        # Database uses: bedrijfswebsite, jobspagina, bedrijfsomschrijving_en/nl/fr, aantal_werknemers, weetjes
        
        # Extract category values from nested object or direct fields
        # Prompt v14 uses flat structure: maturity_en, maturity_nl, maturity_fr
        # Prompt v12 uses nested: maturity.category_en or category.en
        category_en = (
            enrichment_data.get("maturity_en") or  # v14 flat
            maturity.get("category_en") or         # v12 nested in maturity
            category_obj.get("en") or              # v12 nested in category
            enrichment_data.get("category_en")     # v12 flat fallback
        )
        category_nl = (
            enrichment_data.get("maturity_nl") or
            maturity.get("category_nl") or
            category_obj.get("nl") or
            enrichment_data.get("category_nl")
        )
        category_fr = (
            enrichment_data.get("maturity_fr") or
            maturity.get("category_fr") or
            category_obj.get("fr") or
            enrichment_data.get("category_fr")
        )
        
        # Prepare data for database (includes both company info and size classification)
        db_data = {
            "company_id": company_id,
            # Company info fields - map from prompt v12 field names
            "bedrijfswebsite": enrichment_data.get("website") or enrichment_data.get("bedrijfswebsite"),
            "jobspagina": enrichment_data.get("careers_page") or enrichment_data.get("jobspagina"),
            "email_hr": enrichment_data.get("email_hr"),
            "email_hr_bron": enrichment_data.get("email_hr_bron"),
            "email_algemeen": enrichment_data.get("email_algemeen"),
            # Belgian location field (v25+) - uses existing locatie_belgie column
            "locatie_belgie": enrichment_data.get("locatie_belgie"),
            "bedrijfsomschrijving_nl": enrichment_data.get("description_nl") or enrichment_data.get("bedrijfsomschrijving_nl"),
            "bedrijfsomschrijving_fr": enrichment_data.get("description_fr") or enrichment_data.get("bedrijfsomschrijving_fr"),
            "bedrijfsomschrijving_en": enrichment_data.get("description_en") or enrichment_data.get("bedrijfsomschrijving_en"),
            # Multilingual sector fields (prompt v6+)
            "sector_en": enrichment_data.get("sector_en"),
            "sector_nl": enrichment_data.get("sector_nl"),
            "sector_fr": enrichment_data.get("sector_fr"),
            # Hiring model fields (prompt v15+)
            "hiring_model": enrichment_data.get("hiring_model"),
            "hiring_model_en": enrichment_data.get("hiring_model_en"),
            "hiring_model_nl": enrichment_data.get("hiring_model_nl"),
            "hiring_model_fr": enrichment_data.get("hiring_model_fr"),
            "aantal_werknemers": enrichment_data.get("employee_count_range") or enrichment_data.get("aantal_werknemers"),
            # Weetjes (factlets) - prompt v12 uses "factlets" instead of "weetjes"
            "weetjes": enrichment_data.get("factlets") or enrichment_data.get("weetjes"),
            "ai_enriched": True,
            "ai_enriched_at": datetime.utcnow().isoformat(),
            "ai_enrichment_error": None,
            # Size classification fields (from unified prompt v12 - nested in "maturity" or "category")
            # Store category_en directly (no constraint, flexible values from LLM)
            "size_category": category_en,
            # Multilingual category fields (v9+)
            "category_en": category_en,
            "category_nl": category_nl,
            "category_fr": category_fr,
            "size_confidence": maturity.get("confidence") or enrichment_data.get("confidence"),
            # Note: summary fields removed from prompt output (no longer generated)
            # Store arrays as JSONB (Supabase handles Python lists directly)
            # Prompt v14 uses key_arguments_en or arguments_en, v12 uses key_arguments
            "size_key_arguments": (
                enrichment_data.get("key_arguments_en") or 
                enrichment_data.get("arguments_en") or 
                maturity.get("key_arguments") or 
                enrichment_data.get("key_arguments")
            ),
            "size_sources": maturity.get("sources") or enrichment_data.get("sources"),
            "size_enriched_at": datetime.utcnow().isoformat() if category_en else None,
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


def enrich_companies_batch(company_ids: list, max_companies: int = 50) -> Dict[str, Any]:
    """
    Enrich multiple companies in batch.
    
    Args:
        company_ids: List of company UUIDs to enrich
        max_companies: Maximum number of companies to process (default: 50 to avoid timeouts)
        
    Returns:
        Dictionary with statistics about the enrichment process
    """
    # Limit to max_companies to avoid timeouts
    if len(company_ids) > max_companies:
        logger.warning(f"Limiting batch from {len(company_ids)} to {max_companies} companies to avoid timeout")
        company_ids = company_ids[:max_companies]
    
    stats = {
        "total": len(company_ids),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    logger.info(f"Starting batch enrichment for {len(company_ids)} companies")
    
    for i, company_id in enumerate(company_ids, 1):
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
            
            # Log progress every 10 companies
            if i % 10 == 0 or i == 1:
                logger.info(f"Progress: {i}/{len(company_ids)} companies processed ({stats['successful']} successful, {stats['failed']} failed)")
            
            # Enrich the company
            result = enrich_company(company_id, company_name, company_url)
            
            if result["success"]:
                stats["successful"] += 1
                logger.info(f"✅ [{i}/{len(company_ids)}] Enriched: {company_name}")
            else:
                stats["failed"] += 1
                logger.warning(f"❌ [{i}/{len(company_ids)}] Failed: {company_name} - {result.get('error', 'Unknown error')}")
                stats["errors"].append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "error": result.get("error", "Unknown error")
                })
            
            # Add delay between companies to avoid rate limiting (except for last company)
            if i < len(company_ids):
                logger.debug(f"Waiting 3s before next company to avoid rate limits...")
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"Error processing company {company_id}: {e}")
            stats["failed"] += 1
            stats["errors"].append({
                "company_id": company_id,
                "error": str(e)
            })
            
            # Add delay even after errors to avoid rate limiting
            if i < len(company_ids):
                time.sleep(3)
    
    logger.info(f"Batch enrichment complete. Successful: {stats['successful']}, Failed: {stats['failed']}")
    
    return stats


def get_unenriched_companies(limit: int = 100, include_retries: bool = True) -> list:
    """
    Get list of companies that haven't been enriched yet.
    Includes automatic retry for quota errors after 24h.
    
    Args:
        limit: Maximum number of companies to return
        include_retries: If True, include companies with old errors (>24h) for retry
        
    Returns:
        List of company IDs
    """
    try:
        from datetime import datetime, timedelta
        
        # ALWAYS query from companies table to catch companies without master data
        result = db.client.table("companies")\
            .select("id, company_master_data!left(ai_enriched, ai_enrichment_error, ai_enriched_at)")\
            .limit(limit)\
            .execute()
        
        unenriched_ids = []
        retry_count = 0
        
        for company in result.data:
            master_data = company.get("company_master_data")
            
            # Case 1: No master data at all → needs enrichment
            # Check for None, empty dict, or empty list
            if not master_data or master_data == {} or master_data == []:
                unenriched_ids.append(company["id"])
                continue
            
            # Case 2: ai_enriched is False or None AND no error → needs enrichment
            if not master_data.get("ai_enriched") and not master_data.get("ai_enrichment_error"):
                unenriched_ids.append(company["id"])
                continue
            
            # Case 3: Has error AND include_retries is True → check if old enough to retry
            if include_retries and master_data.get("ai_enrichment_error"):
                enriched_at = master_data.get("ai_enriched_at")
                if enriched_at:
                    from dateutil import parser
                    enriched_time = parser.parse(enriched_at)
                    retry_cutoff = datetime.utcnow() - timedelta(hours=24)
                    
                    if enriched_time < retry_cutoff:
                        unenriched_ids.append(company["id"])
                        retry_count += 1
                else:
                    # No timestamp, retry anyway
                    unenriched_ids.append(company["id"])
                    retry_count += 1
        
        new_count = len(unenriched_ids) - retry_count
        logger.info(f"Found {len(unenriched_ids)} unenriched companies ({new_count} new, {retry_count} retries)")
        
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
