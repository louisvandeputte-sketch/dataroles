"""
Auto-enrichment service for locations.
Automatically enriches new location records in the background.
"""

import asyncio
from typing import Optional
from loguru import logger

from database.client import db
from ingestion.location_enrichment import enrich_location


class AutoEnrichService:
    """Service to automatically enrich new location records."""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
    
    async def start(self):
        """Start the auto-enrichment service."""
        self.running = True
        logger.info("🤖 Auto-enrichment service started")
        
        while self.running:
            try:
                await self.process_pending_locations()
            except Exception as e:
                logger.error(f"Error in auto-enrichment service: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the auto-enrichment service."""
        self.running = False
        logger.info("🛑 Auto-enrichment service stopped")
    
    async def process_pending_locations(self):
        """Process locations that need enrichment."""
        try:
            # Find unenriched locations (limit to 10 per batch to avoid overload)
            result = db.client.table("locations")\
                .select("id, city, country_code, region")\
                .or_("ai_enriched.is.null,ai_enriched.eq.false")\
                .is_("ai_enrichment_error", "null")\
                .limit(10)\
                .execute()
            
            locations = result.data if result.data else []
            
            if not locations:
                return  # No pending locations
            
            logger.info(f"🔄 Auto-enriching {len(locations)} pending locations")
            
            # Enrich each location
            for location in locations:
                try:
                    location_id = location["id"]
                    city = location.get("city")
                    country_code = location.get("country_code")
                    region = location.get("region")
                    
                    logger.info(f"Enriching: {city}, {country_code}")
                    
                    # Enrich the location
                    enrichment_data = enrich_location(
                        location_id=location_id,
                        city=city,
                        country_code=country_code,
                        region=region
                    )
                    
                    if enrichment_data:
                        logger.success(f"✅ Auto-enriched: {city}")
                    else:
                        logger.warning(f"⚠️ Failed to auto-enrich: {city}")
                
                except Exception as e:
                    logger.error(f"Failed to enrich location {location.get('city')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending locations: {e}")


# Global service instance
_auto_enrich_service: Optional[AutoEnrichService] = None


def get_auto_enrich_service() -> AutoEnrichService:
    """Get or create the auto-enrichment service instance."""
    global _auto_enrich_service
    if _auto_enrich_service is None:
        _auto_enrich_service = AutoEnrichService()
    return _auto_enrich_service
