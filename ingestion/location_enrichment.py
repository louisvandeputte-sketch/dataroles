"""Location enrichment using OpenAI LLM to standardize and enrich location data."""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db


# Initialize OpenAI client with extended timeout
client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=300.0  # 5 minutes timeout
)

# Prompt ID for location enrichment
LOCATION_ENRICHMENT_PROMPT_ID = "pmpt_68ff4fce6a0c8193baa5b7310f37a930074c8aedab026486"
LOCATION_ENRICHMENT_PROMPT_VERSION = "2"


def enrich_location(location_id: str, city: str, country_code: str, region: Optional[str] = None) -> Dict[str, Any]:
    """
    Enrich a single location using OpenAI LLM.
    
    Args:
        location_id: UUID of the location
        city: City name
        country_code: ISO 3166-1 alpha-2 country code
        region: Optional region/province/state
        
    Returns:
        Dictionary with success status and enrichment data or error
    """
    try:
        logger.info(f"Starting enrichment for location: {city}, {country_code} (ID: {location_id})")
        
        # Prepare input for the LLM
        location_info = f"city: {city}\ncountry_code: {country_code}"
        if region:
            location_info += f"\nregion: {region}"
        
        # Call OpenAI with the prompt
        logger.debug(f"Calling OpenAI API with input: {location_info}")
        
        response = client.responses.create(
            prompt={
                "id": LOCATION_ENRICHMENT_PROMPT_ID,
                "version": LOCATION_ENRICHMENT_PROMPT_VERSION
            },
            input=location_info
        )
        
        logger.debug(f"OpenAI response: {response}")
        
        # Extract structured output from response
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
        success = save_enrichment_to_db(location_id, enrichment_data)
        
        if success:
            logger.success(f"Successfully enriched location: {city}, {country_code}")
            return {
                "success": True,
                "location_id": location_id,
                "city": city,
                "country_code": country_code,
                "data": enrichment_data
            }
        else:
            return {
                "success": False,
                "location_id": location_id,
                "city": city,
                "country_code": country_code,
                "error": "Failed to save to database"
            }
            
    except Exception as e:
        logger.error(f"Failed to enrich location {city}, {country_code}: {e}")
        
        # Save error to database
        try:
            db.client.table("locations")\
                .update({
                    "ai_enriched": False,
                    "ai_enrichment_error": str(e),
                    "ai_enriched_at": datetime.utcnow().isoformat()
                })\
                .eq("id", location_id)\
                .execute()
        except Exception as db_error:
            logger.error(f"Failed to save error to database: {db_error}")
        
        return {
            "success": False,
            "location_id": location_id,
            "city": city,
            "country_code": country_code,
            "error": str(e)
        }


def save_enrichment_to_db(location_id: str, enrichment_data: Dict[str, Any]) -> bool:
    """
    Save enrichment data to locations table.
    
    Args:
        location_id: UUID of the location
        enrichment_data: Dictionary with enrichment fields
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare data for database
        db_data = {
            "country_code_3": enrichment_data.get("country_code_3"),
            "country_name": enrichment_data.get("country_name"),
            "subdivision_name": enrichment_data.get("subdivision_name"),
            "timezone": enrichment_data.get("timezone"),
            "city_official_name": enrichment_data.get("city_official_name"),
            "city_normalized": enrichment_data.get("city_normalized"),
            "region_normalized": enrichment_data.get("region_normalized"),
            "country_normalized": enrichment_data.get("country_normalized"),
            "city_name_nl": enrichment_data.get("city_name_nl"),
            "city_name_fr": enrichment_data.get("city_name_fr"),
            "city_name_en": enrichment_data.get("city_name_en"),
            "country_name_nl": enrichment_data.get("country_name_nl"),
            "country_name_fr": enrichment_data.get("country_name_fr"),
            "country_name_en": enrichment_data.get("country_name_en"),
            "ai_enriched": True,
            "ai_enriched_at": datetime.utcnow().isoformat(),
            "ai_enrichment_error": None
        }
        
        # Remove None values (keep only fields that were enriched)
        db_data = {k: v for k, v in db_data.items() if v is not None or k in ["ai_enriched", "ai_enrichment_error"]}
        
        # Update location record
        result = db.client.table("locations")\
            .update(db_data)\
            .eq("id", location_id)\
            .execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save enrichment data to database: {e}")
        return False


def enrich_locations_batch(location_ids: list = None, limit: int = None, force_reenrich: bool = False) -> Dict[str, Any]:
    """
    Enrich multiple locations in batch.
    
    Args:
        location_ids: Optional list of location UUIDs to enrich. If None, enriches all locations.
        limit: Optional limit on number of locations to enrich
        force_reenrich: If True, re-enrich all locations (even already enriched ones)
        
    Returns:
        Dictionary with statistics about the enrichment process
    """
    stats = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # Get locations to enrich
        if location_ids:
            # Enrich specific locations
            query = db.client.table("locations")\
                .select("id, city, country_code, region")\
                .in_("id", location_ids)
        elif force_reenrich:
            # Re-enrich ALL locations
            query = db.client.table("locations")\
                .select("id, city, country_code, region")
        else:
            # Enrich only unenriched locations
            query = db.client.table("locations")\
                .select("id, city, country_code, region")\
                .or_("ai_enriched.is.null,ai_enriched.eq.false")
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        locations = result.data if result.data else []
        
        stats["total"] = len(locations)
        logger.info(f"Starting batch enrichment for {len(locations)} locations")
        
        for location in locations:
            try:
                result = enrich_location(
                    location_id=location["id"],
                    city=location["city"],
                    country_code=location["country_code"],
                    region=location.get("region")
                )
                
                if result["success"]:
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "location_id": location["id"],
                        "city": location["city"],
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                logger.error(f"Failed to enrich location {location['id']}: {e}")
                stats["failed"] += 1
                stats["errors"].append({
                    "location_id": location["id"],
                    "city": location.get("city"),
                    "error": str(e)
                })
        
        logger.info(f"Batch enrichment complete: {stats['successful']} successful, {stats['failed']} failed")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to run batch enrichment: {e}")
        stats["errors"].append({"error": str(e)})
        return stats


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    else:
        limit = 10
    
    print(f"Enriching up to {limit} locations...")
    stats = enrich_locations_batch(limit=limit)
    
    print(f"\n📊 Results:")
    print(f"   Total: {stats['total']}")
    print(f"   Successful: {stats['successful']}")
    print(f"   Failed: {stats['failed']}")
    
    if stats['errors']:
        print(f"\n❌ Errors:")
        for error in stats['errors'][:5]:
            print(f"   - {error}")
