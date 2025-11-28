#!/usr/bin/env python3
"""
Reset locations that are marked as enriched but have no coordinates
Usage: python ingestion/reset_failed_geocoding.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.client import db
from loguru import logger


def reset_failed_geocoding():
    """Reset locations marked as enriched but without coordinates"""
    
    logger.info("🔄 Finding locations marked as enriched but without coordinates...")
    
    # Find locations with coordinates_enriched=true but null coordinates
    result = db.client.table("locations")\
        .select("id, city_name_en, country_name_en", count="exact")\
        .eq("coordinates_enriched", True)\
        .is_("longitude", "null")\
        .execute()
    
    count = result.count or 0
    logger.info(f"📍 Found {count} locations to reset")
    
    if count == 0:
        logger.success("✅ No locations to reset!")
        return
    
    # Reset the flag
    update_result = db.client.table("locations")\
        .update({
            "coordinates_enriched": False,
            "coordinates_enriched_at": None
        })\
        .eq("coordinates_enriched", True)\
        .is_("longitude", "null")\
        .execute()
    
    logger.success(f"✅ Reset {count} locations - they will be re-geocoded")
    
    # Show some examples
    if result.data:
        logger.info("📋 Examples of reset locations:")
        for loc in result.data[:5]:
            city = loc.get("city_name_en") or "Unknown"
            country = loc.get("country_name_en") or "Unknown"
            logger.info(f"  - {city}, {country}")


if __name__ == "__main__":
    reset_failed_geocoding()
