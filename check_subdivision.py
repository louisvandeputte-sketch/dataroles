"""Check how many jobs are missing subdivision_name_en."""

from database.client import SupabaseClient
from loguru import logger

def check_subdivision_coverage():
    """Check how many jobs have locations with subdivision_name_en."""
    db = SupabaseClient()
    
    # Get all active jobs with their locations
    result = db.client.table("job_postings")\
        .select("id, title, locations!job_postings_location_id_fkey(id, city, subdivision_name_en, subdivision_name, country_code)")\
        .eq("is_active", True)\
        .execute()
    
    total_jobs = len(result.data)
    jobs_with_subdivision_en = 0
    jobs_without_subdivision_en = 0
    jobs_without_any_subdivision = 0
    
    logger.info(f"Total active jobs: {total_jobs}")
    
    for job in result.data:
        location = job.get("locations")
        if location:
            has_en = location.get("subdivision_name_en")
            has_any = location.get("subdivision_name") or location.get("subdivision_name_en")
            
            if has_en:
                jobs_with_subdivision_en += 1
            else:
                jobs_without_subdivision_en += 1
                
            if not has_any:
                jobs_without_any_subdivision += 1
        else:
            jobs_without_subdivision_en += 1
            jobs_without_any_subdivision += 1
    
    logger.info(f"Jobs WITH subdivision_name_en: {jobs_with_subdivision_en}")
    logger.info(f"Jobs WITHOUT subdivision_name_en: {jobs_without_subdivision_en}")
    logger.info(f"Jobs WITHOUT any subdivision: {jobs_without_any_subdivision}")
    logger.info(f"Percentage with EN subdivision: {(jobs_with_subdivision_en / total_jobs * 100):.1f}%")
    
    # Now check locations table directly
    logger.info("\n--- Checking locations table ---")
    locations_result = db.client.table("locations")\
        .select("id, city, subdivision_name, subdivision_name_en, ai_enriched")\
        .execute()
    
    total_locations = len(locations_result.data)
    locations_with_en = sum(1 for loc in locations_result.data if loc.get("subdivision_name_en"))
    locations_without_en = total_locations - locations_with_en
    locations_ai_enriched = sum(1 for loc in locations_result.data if loc.get("ai_enriched"))
    
    logger.info(f"Total locations: {total_locations}")
    logger.info(f"Locations WITH subdivision_name_en: {locations_with_en}")
    logger.info(f"Locations WITHOUT subdivision_name_en: {locations_without_en}")
    logger.info(f"Locations AI enriched: {locations_ai_enriched}")
    logger.info(f"Percentage with EN subdivision: {(locations_with_en / total_locations * 100):.1f}%")
    
    # Show some examples of locations without subdivision_name_en
    logger.info("\n--- Examples of locations WITHOUT subdivision_name_en ---")
    examples = [loc for loc in locations_result.data if not loc.get("subdivision_name_en")][:10]
    for loc in examples:
        logger.info(f"  {loc.get('city')} - subdivision_name: {loc.get('subdivision_name')} - ai_enriched: {loc.get('ai_enriched')}")

if __name__ == "__main__":
    check_subdivision_coverage()
