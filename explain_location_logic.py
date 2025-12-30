"""
Explain the location override logic for vague locations.
Shows which column is used for determining vague locations and how the override works.
"""

from database.client import SupabaseClient
from loguru import logger

def explain_location_logic():
    """Explain the location override logic step by step."""
    db = SupabaseClient()
    
    logger.info("=" * 80)
    logger.info("LOCATION OVERRIDE LOGIC EXPLANATION")
    logger.info("=" * 80)
    
    # Step 1: Show vague location patterns
    logger.info("\n📋 STEP 1: Vague Location Patterns (from vague_locations_config table)")
    logger.info("-" * 80)
    
    vague_config = db.client.table("vague_locations_config")\
        .select("*")\
        .eq("is_active", True)\
        .execute()
    
    logger.info(f"Found {len(vague_config.data)} active vague location patterns:")
    for pattern in vague_config.data:
        logger.info(f"  • '{pattern['pattern']}' - {pattern.get('description', 'No description')}")
    
    # Step 2: Explain the matching logic
    logger.info("\n🔍 STEP 2: How Vague Locations Are Detected")
    logger.info("-" * 80)
    logger.info("When processing a job, the system checks if the location string STARTS WITH")
    logger.info("any of the vague patterns above.")
    logger.info("")
    logger.info("Example matches:")
    logger.info("  ✓ 'Flemish Region' → VAGUE (exact match)")
    logger.info("  ✓ 'Belgium' → VAGUE (exact match)")
    logger.info("  ✗ 'Brussels' → NOT VAGUE (doesn't match any pattern)")
    logger.info("  ✗ 'Antwerp' → NOT VAGUE (doesn't match any pattern)")
    
    # Step 3: Show the override logic
    logger.info("\n🔄 STEP 3: Location Override Process")
    logger.info("-" * 80)
    logger.info("When a VAGUE location is detected:")
    logger.info("")
    logger.info("1. System looks up company_master_data.locatie_belgie for the company")
    logger.info("   - This field contains the primary Belgian city (e.g., 'Brussel', 'Antwerpen')")
    logger.info("")
    logger.info("2. If locatie_belgie exists and is valid:")
    logger.info("   - Creates override location: '{locatie_belgie}, Belgium'")
    logger.info("   - Stores this in job_postings.location_id_override")
    logger.info("")
    logger.info("3. If locatie_belgie is missing or invalid:")
    logger.info("   - No override is created")
    logger.info("   - Job keeps the vague location")
    logger.info("   - Will be enriched later when company data is available")
    
    # Step 4: Show real examples
    logger.info("\n📊 STEP 4: Real Examples from Database")
    logger.info("-" * 80)
    
    # Get vague location IDs
    vague_patterns = [p['pattern'] for p in vague_config.data]
    
    # Find locations that match vague patterns
    all_locations = db.client.table("locations")\
        .select("id, city, full_location_string")\
        .execute()
    
    vague_location_ids = []
    for loc in all_locations.data:
        city = loc.get('city', '')
        if any(city.startswith(pattern) for pattern in vague_patterns):
            vague_location_ids.append(loc['id'])
    
    logger.info(f"Found {len(vague_location_ids)} vague locations in database")
    
    # Get jobs with vague locations
    jobs_with_vague = db.client.table("job_postings")\
        .select("id, title, company_id, location_id, location_id_override, companies(name), locations!job_postings_location_id_fkey(city)")\
        .in_("location_id", vague_location_ids)\
        .eq("is_active", True)\
        .limit(10)\
        .execute()
    
    logger.info(f"\nShowing 10 example jobs with vague locations:\n")
    
    for i, job in enumerate(jobs_with_vague.data, 1):
        company_name = job.get('companies', {}).get('name', 'Unknown')
        vague_location = job.get('locations', {}).get('city', 'Unknown')
        has_override = job.get('location_id_override') is not None
        
        logger.info(f"{i}. Job: {job['title'][:50]}...")
        logger.info(f"   Company: {company_name}")
        logger.info(f"   Vague Location: {vague_location}")
        
        if has_override:
            # Get override location
            override_loc = db.client.table("locations")\
                .select("city, full_location_string")\
                .eq("id", job['location_id_override'])\
                .single()\
                .execute()
            
            logger.info(f"   ✅ Override Location: {override_loc.data.get('city')}")
            
            # Get company locatie_belgie
            company_master = db.client.table("company_master_data")\
                .select("locatie_belgie")\
                .eq("company_id", job['company_id'])\
                .maybe_single()\
                .execute()
            
            if company_master.data:
                logger.info(f"   📍 Company locatie_belgie: {company_master.data.get('locatie_belgie')}")
        else:
            logger.info(f"   ❌ No Override (company location not available)")
        
        logger.info("")
    
    # Step 5: Statistics
    logger.info("\n📈 STEP 5: Statistics")
    logger.info("-" * 80)
    
    total_vague_jobs = db.client.table("job_postings")\
        .select("id", count="exact")\
        .in_("location_id", vague_location_ids)\
        .eq("is_active", True)\
        .execute()
    
    jobs_with_override = db.client.table("job_postings")\
        .select("id", count="exact")\
        .in_("location_id", vague_location_ids)\
        .not_.is_("location_id_override", "null")\
        .eq("is_active", True)\
        .execute()
    
    logger.info(f"Total active jobs with vague locations: {total_vague_jobs.count}")
    logger.info(f"Jobs with location override: {jobs_with_override.count}")
    logger.info(f"Jobs without override: {total_vague_jobs.count - jobs_with_override.count}")
    logger.info(f"Override coverage: {(jobs_with_override.count / total_vague_jobs.count * 100):.1f}%")
    
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info("The system uses:")
    logger.info("  1. vague_locations_config.pattern → to detect vague locations")
    logger.info("  2. company_master_data.locatie_belgie → to create override location")
    logger.info("  3. job_postings.location_id_override → to store the override")
    logger.info("")
    logger.info("Display logic (in views/API):")
    logger.info("  - Uses COALESCE(location_id_override, location_id)")
    logger.info("  - This means: use override if available, otherwise use original location")
    logger.info("=" * 80)

if __name__ == "__main__":
    explain_location_logic()
