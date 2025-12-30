"""Check why some locations are missing subdivision_name_en."""

from database.client import SupabaseClient
from loguru import logger

def check_missing_subdivisions():
    """Check locations without subdivision_name_en to understand why."""
    db = SupabaseClient()
    
    # Get locations without subdivision_name_en but that are AI enriched
    result = db.client.table("locations")\
        .select("*")\
        .eq("ai_enriched", True)\
        .is_("subdivision_name_en", "null")\
        .execute()
    
    logger.info(f"Found {len(result.data)} locations without subdivision_name_en")
    
    # Analyze the data
    has_subdivision_name = 0
    has_subdivision_name_fr = 0
    has_region = 0
    has_nothing = 0
    
    for loc in result.data:
        has_sub = bool(loc.get("subdivision_name"))
        has_sub_fr = bool(loc.get("subdivision_name_fr"))
        has_reg = bool(loc.get("region"))
        
        if has_sub:
            has_subdivision_name += 1
        if has_sub_fr:
            has_subdivision_name_fr += 1
        if has_reg:
            has_region += 1
        if not (has_sub or has_sub_fr or has_reg):
            has_nothing += 1
    
    logger.info(f"\nBreakdown of missing subdivision_name_en:")
    logger.info(f"  Has subdivision_name (NL): {has_subdivision_name}")
    logger.info(f"  Has subdivision_name_fr: {has_subdivision_name_fr}")
    logger.info(f"  Has region: {has_region}")
    logger.info(f"  Has nothing: {has_nothing}")
    
    # Show detailed examples
    logger.info(f"\n--- Detailed examples (first 15) ---")
    for i, loc in enumerate(result.data[:15]):
        logger.info(f"\n{i+1}. City: {loc.get('city')}")
        logger.info(f"   Country: {loc.get('country_code')}")
        logger.info(f"   Region: {loc.get('region')}")
        logger.info(f"   subdivision_name: {loc.get('subdivision_name')}")
        logger.info(f"   subdivision_name_fr: {loc.get('subdivision_name_fr')}")
        logger.info(f"   subdivision_name_en: {loc.get('subdivision_name_en')}")
        logger.info(f"   AI enriched at: {loc.get('ai_enriched_at')}")
        logger.info(f"   AI error: {loc.get('ai_enrichment_error')}")
    
    # Check if these locations have jobs
    logger.info(f"\n--- Checking job count for these locations ---")
    location_ids = [loc["id"] for loc in result.data]
    
    jobs_result = db.client.table("job_postings")\
        .select("id, location_id")\
        .eq("is_active", True)\
        .in_("location_id", location_ids)\
        .execute()
    
    logger.info(f"Total active jobs using these locations: {len(jobs_result.data)}")
    
    # Count jobs per location
    location_job_counts = {}
    for job in jobs_result.data:
        loc_id = job["location_id"]
        location_job_counts[loc_id] = location_job_counts.get(loc_id, 0) + 1
    
    # Show top locations by job count
    sorted_locations = sorted(location_job_counts.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"\nTop 10 locations without subdivision_name_en by job count:")
    for loc_id, count in sorted_locations[:10]:
        loc = next((l for l in result.data if l["id"] == loc_id), None)
        if loc:
            logger.info(f"  {loc.get('city')} ({loc.get('country_code')}): {count} jobs")

if __name__ == "__main__":
    check_missing_subdivisions()
