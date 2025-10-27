"""API endpoints for location management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

from database.client import db

router = APIRouter()


class LocationUpdate(BaseModel):
    """Model for updating location data."""
    city: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    country_code_3: Optional[str] = None
    country_name: Optional[str] = None
    subdivision_name: Optional[str] = None
    subdivision_name_fr: Optional[str] = None
    subdivision_name_en: Optional[str] = None
    timezone: Optional[str] = None
    city_official_name: Optional[str] = None
    city_normalized: Optional[str] = None
    region_normalized: Optional[str] = None
    country_normalized: Optional[str] = None
    city_name_nl: Optional[str] = None
    city_name_fr: Optional[str] = None
    city_name_en: Optional[str] = None
    country_name_nl: Optional[str] = None
    country_name_fr: Optional[str] = None
    country_name_en: Optional[str] = None


# ==================== LOCATIONS ====================

@router.get("/")
async def get_all_locations(
    limit: int = 1000,
    offset: int = 0,
    search: Optional[str] = None,
    country_code: Optional[str] = None,
    ai_enriched: Optional[bool] = None
):
    """Get all locations with optional filtering."""
    try:
        query = db.client.table("locations").select("*")
        
        # Apply filters
        if search:
            query = query.or_(f"city.ilike.%{search}%,country_code.ilike.%{search}%,region.ilike.%{search}%")
        
        if country_code:
            query = query.eq("country_code", country_code)
        
        if ai_enriched is not None:
            query = query.eq("ai_enriched", ai_enriched)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Order by city name
        query = query.order("city")
        
        result = query.execute()
        
        return {
            "locations": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
    except Exception as e:
        logger.error(f"Failed to get locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{location_id}")
async def get_location(location_id: str):
    """Get a single location by ID."""
    try:
        result = db.client.table("locations")\
            .select("*")\
            .eq("id", location_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{location_id}")
async def update_location(location_id: str, location_data: LocationUpdate):
    """Update a location."""
    try:
        # Prepare update data (only include non-None values)
        update_data = {k: v for k, v in location_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        result = db.client.table("locations")\
            .update(update_data)\
            .eq("id", location_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {"success": True, "location": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{location_id}")
async def delete_location(location_id: str):
    """Delete a location."""
    try:
        result = db.client.table("locations")\
            .delete()\
            .eq("id", location_id)\
            .execute()
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to delete location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATS ====================

@router.get("/stats/overview")
async def get_location_stats():
    """Get statistics about locations with data quality metrics."""
    try:
        # Get all locations to analyze data quality
        all_locations = db.client.table("locations")\
            .select("subdivision_name, subdivision_name_fr, subdivision_name_en, timezone, city_name_nl, city_name_fr, city_name_en, country_name_nl")\
            .execute()
        
        locations = all_locations.data if all_locations.data else []
        total = len(locations)
        
        # Calculate data quality metrics
        missing_subdivision = 0
        missing_timezone = 0
        missing_translations = 0
        complete = 0
        
        for loc in locations:
            has_issues = False
            
            # Check subdivision (any language)
            if not loc.get("subdivision_name") and not loc.get("subdivision_name_fr") and not loc.get("subdivision_name_en"):
                missing_subdivision += 1
                has_issues = True
            
            # Check timezone
            if not loc.get("timezone"):
                missing_timezone += 1
                has_issues = True
            
            # Check translations (city and country names in all 3 languages)
            if not (loc.get("city_name_nl") and loc.get("city_name_fr") and loc.get("city_name_en") and loc.get("country_name_nl")):
                missing_translations += 1
                has_issues = True
            
            # Complete record: has all fields
            if not has_issues:
                complete += 1
        
        return {
            "total": total,
            "missing_subdivision": missing_subdivision,
            "missing_timezone": missing_timezone,
            "missing_translations": missing_translations,
            "complete": complete
        }
    except Exception as e:
        logger.error(f"Failed to get location stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
