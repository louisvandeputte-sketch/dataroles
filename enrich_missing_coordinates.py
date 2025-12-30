"""
Enrich locations with longitude/latitude coordinates using OpenAI LLM.
Uses prompt: pmpt_69295e6a81a881968564c739240cb7b40901cbdc9ad22b65
"""

import json
import time
from openai import OpenAI
from database import db
from loguru import logger
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=api_key)

# Prompt ID for location coordinate enrichment
LOCATION_COORDS_PROMPT_ID = "pmpt_69295e6a81a881968564c739240cb7b40901cbdc9ad22b65"
LOCATION_COORDS_PROMPT_VERSION = "1"  # Adjust if needed


def get_locations_without_coordinates(limit=None):
    """Get all locations that don't have longitude/latitude yet."""
    query = db.client.table("locations")\
        .select("*")\
        .is_("longitude", "null")
    
    if limit:
        query = query.limit(limit)
    
    result = query.execute()
    return result.data


def format_location_for_llm(location):
    """Format location data as input for LLM."""
    parts = []
    
    if location.get("city_official_name"):
        parts.append(f"City: {location['city_official_name']}")
    elif location.get("city_name_nl"):
        parts.append(f"City: {location['city_name_nl']}")
    elif location.get("city_name_en"):
        parts.append(f"City: {location['city_name_en']}")
    
    if location.get("subdivision_name_nl"):
        parts.append(f"Region: {location['subdivision_name_nl']}")
    elif location.get("subdivision_name_en"):
        parts.append(f"Region: {location['subdivision_name_en']}")
    
    if location.get("country_name"):
        parts.append(f"Country: {location['country_name']}")
    elif location.get("country_code_3"):
        parts.append(f"Country code: {location['country_code_3']}")
    
    return ", ".join(parts) if parts else "Unknown location"


def enrich_location_coordinates(location_id, location_text):
    """Call OpenAI API to get coordinates for a location."""
    try:
        response = client.responses.create(
            prompt={
                "id": LOCATION_COORDS_PROMPT_ID,
                "version": LOCATION_COORDS_PROMPT_VERSION
            },
            input=location_text
        )
        
        # Extract the response from the OpenAI response format
        if hasattr(response, 'output') and isinstance(response.output, list):
            # Find the message output (skip reasoning items)
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    if hasattr(item, 'content') and isinstance(item.content, list):
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                text = content_item.text
                                # Try to parse as JSON
                                try:
                                    result = json.loads(text)
                                    return {
                                        "longitude": result.get("longitude"),
                                        "latitude": result.get("latitude")
                                    }
                                except json.JSONDecodeError:
                                    logger.warning(f"Could not parse LLM output as JSON: {text}")
                                    return None
        
        logger.warning(f"Unexpected response format")
        return None
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None


def update_location_coordinates(location_id, longitude, latitude):
    """Update location with coordinates."""
    try:
        db.client.table("locations")\
            .update({
                "longitude": longitude,
                "latitude": latitude,
                "coordinates_enriched": True
            })\
            .eq("id", location_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update location {location_id}: {e}")
        return False


def main():
    """Main function to enrich all locations without coordinates."""
    logger.info("="*80)
    logger.info("ENRICHING LOCATIONS WITH COORDINATES")
    logger.info("="*80)
    
    # Get locations without coordinates
    locations = get_locations_without_coordinates()
    total = len(locations)
    
    logger.info(f"\nFound {total} locations without coordinates")
    
    if total == 0:
        logger.info("✅ All locations already have coordinates!")
        return
    
    # Process each location
    successful = 0
    failed = 0
    skipped = 0
    
    for i, location in enumerate(locations, 1):
        location_id = location["id"]
        
        # Get location name for display
        city = location.get("city_official_name") or location.get("city_name_nl") or "Unknown"
        country = location.get("country_name") or "Unknown"
        
        # Skip if city is "Unknown" and no other info
        if city == "Unknown" and country == "Unknown":
            logger.warning(f"[{i}/{total}] Skipping: No location data available")
            skipped += 1
            continue
        
        logger.info(f"\n[{i}/{total}] Processing: {city}, {country}")
        
        # Format location data
        location_text = format_location_for_llm(location)
        
        # Get coordinates from LLM
        coords = enrich_location_coordinates(location_id, location_text)
        
        if coords and coords.get("longitude") and coords.get("latitude"):
            logger.info(f"  ✅ Coordinates: {coords['latitude']}, {coords['longitude']}")
            
            # Update database
            if update_location_coordinates(location_id, coords["longitude"], coords["latitude"]):
                successful += 1
                logger.success(f"  💾 Updated database")
            else:
                failed += 1
                logger.error(f"  ❌ Failed to update database")
        else:
            failed += 1
            logger.warning(f"  ⚠️  Could not get coordinates")
        
        # Rate limiting: wait 1 second between requests
        if i < total:
            time.sleep(1)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total locations processed: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {skipped}")
    if total - skipped > 0:
        logger.info(f"Success rate: {(successful/(total-skipped)*100):.1f}%")


if __name__ == "__main__":
    main()
