"""
Location Geocoder - Convert city/country to coordinates using OpenAI
Uses OpenAI Responses API to geocode locations
"""

import json
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger
from openai import OpenAI

from config.settings import settings
from database.client import db

# OpenAI Responses API configuration
GEOCODER_PROMPT_ID = "pmpt_69295e6a81a881968564c739240cb7b40901cbdc9ad22b65"
GEOCODER_PROMPT_VERSION = "2"  # v2: improved geocoding prompt

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def geocode_location(city: str, country: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode a city and country to longitude/latitude coordinates.
    
    Args:
        city: City name (e.g., "Amsterdam")
        country: Country name (e.g., "Netherlands")
        
    Returns:
        Tuple of (longitude, latitude) or (None, None) if not found
        
    Example:
        >>> geocode_location("Amsterdam", "Netherlands")
        (4.9041, 52.3676)
    """
    try:
        # Combine city and country
        location_input = f"{city}, {country}"
        
        logger.info(f"🌍 Geocoding location: {location_input}")
        
        # Call OpenAI Responses API
        response = client.responses.create(
            prompt={
                "id": GEOCODER_PROMPT_ID,
                "version": GEOCODER_PROMPT_VERSION
            },
            input=location_input
        )
        
        # Parse response - Responses API has different structure
        # The response object has an 'output' attribute with the content
        if hasattr(response, 'output'):
            content = response.output
        elif hasattr(response, 'content'):
            content = response.content
        else:
            # Fallback to standard chat completion format
            content = response.choices[0].message.content
        
        # If output is a list, find the ResponseOutputText item
        if isinstance(content, list):
            extracted_text = None
            for item in content:
                # Check for ResponseOutputText with text attribute
                if hasattr(item, 'text') and item.text:
                    extracted_text = item.text
                    break
                # Fallback: check for content attribute
                elif hasattr(item, 'content') and item.content:
                    extracted_text = item.content
                    break
            content = extracted_text if extracted_text else "{}"
        
        # Parse JSON response
        try:
            # Debug: log the content type and value
            logger.debug(f"Content type: {type(content)}, Content: {content}")
            
            # If content is a string, parse as JSON
            if isinstance(content, str):
                result = json.loads(content)
            # If content is a dict, use directly
            elif isinstance(content, dict):
                result = content
            # If content has 'content' attribute (ResponseReasoningItem), extract it
            elif hasattr(content, 'content'):
                result = json.loads(content.content) if isinstance(content.content, str) else content.content
            else:
                # Try to convert to dict
                result = dict(content) if hasattr(content, '__dict__') else {}
            
            if result is None:
                logger.error(f"❌ Result is None after parsing content: {content}")
                return (None, None)
            
            longitude = result.get("longitude")
            latitude = result.get("latitude")
            
            # Validate coordinates
            if longitude is not None and latitude is not None:
                # Check valid ranges
                if -180 <= longitude <= 180 and -90 <= latitude <= 90:
                    logger.success(f"✅ Geocoded {location_input}: ({longitude}, {latitude})")
                    return (longitude, latitude)
                else:
                    logger.warning(f"⚠️ Invalid coordinates for {location_input}: ({longitude}, {latitude})")
                    return (None, None)
            else:
                logger.warning(f"⚠️ Could not geocode {location_input}: coordinates not found")
                return (None, None)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse geocoding response for {location_input}: {e}")
            logger.debug(f"Raw response: {content}")
            return (None, None)
            
    except Exception as e:
        logger.error(f"❌ Error geocoding {location_input}: {e}")
        return (None, None)


def enrich_location_coordinates(location_id: str) -> bool:
    """
    Enrich a single location with coordinates.
    
    Args:
        location_id: UUID of the location to enrich
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Fetch location data
        location = db.client.table("locations")\
            .select("id, city_name_en, country_name_en, city_official_name, country_name")\
            .eq("id", location_id)\
            .single()\
            .execute()
        
        if not location.data:
            logger.error(f"❌ Location {location_id} not found")
            return False
        
        loc = location.data
        
        # Use English names if available, otherwise use official names
        city = loc.get("city_name_en") or loc.get("city_official_name")
        country = loc.get("country_name_en") or loc.get("country_name")
        
        if not city or not country:
            logger.warning(f"⚠️ Location {location_id} missing city or country")
            return False
        
        # Geocode
        longitude, latitude = geocode_location(city, country)
        
        # Only update if we got valid coordinates
        if longitude is not None and latitude is not None:
            update_data = {
                "longitude": longitude,
                "latitude": latitude,
                "coordinates_enriched": True,
                "coordinates_enriched_at": datetime.utcnow().isoformat()
            }
            
            db.client.table("locations")\
                .update(update_data)\
                .eq("id", location_id)\
                .execute()
            
            logger.success(f"✅ Updated location {location_id} with coordinates: ({longitude}, {latitude})")
            return True
        else:
            logger.warning(f"⚠️ Could not geocode location {location_id}: {city}, {country}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error enriching location {location_id}: {e}")
        return False


def enrich_all_locations(limit: Optional[int] = None, only_missing: bool = True):
    """
    Enrich all locations with coordinates.
    
    Args:
        limit: Maximum number of locations to process (None = all)
        only_missing: Only process locations without coordinates
    """
    logger.info("🚀 Starting location geocoding...")
    
    try:
        # Build query
        query = db.client.table("locations")\
            .select("id, city_name_en, country_name_en, city_official_name, country_name, longitude, latitude")
        
        if only_missing:
            query = query.is_("coordinates_enriched", "false")
        
        # Only select locations that have city and country data
        query = query.not_.is_("city_name_en", "null").not_.is_("country_name_en", "null")
        
        if limit:
            query = query.limit(limit)
        
        # Fetch locations
        response = query.execute()
        locations = response.data
        
        if not locations:
            logger.info("✅ No locations to geocode")
            return
        
        logger.info(f"📍 Found {len(locations)} locations to geocode")
        
        # Process each location
        success_count = 0
        failed_count = 0
        
        for loc in locations:
            if enrich_location_coordinates(loc["id"]):
                success_count += 1
            else:
                failed_count += 1
        
        logger.success(f"✅ Geocoding complete! Success: {success_count}, Failed: {failed_count}")
        
    except Exception as e:
        logger.error(f"❌ Error in batch geocoding: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        # Geocode specific location by ID
        location_id = sys.argv[1]
        enrich_location_coordinates(location_id)
    else:
        # Geocode all locations without coordinates
        enrich_all_locations(limit=100, only_missing=True)
