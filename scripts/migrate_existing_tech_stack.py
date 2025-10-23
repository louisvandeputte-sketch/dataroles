"""Migrate existing tech stack data from llm_enrichment to masterdata tables."""

from loguru import logger
from database.client import db
from ingestion.tech_stack_processor import process_tech_stack_for_job
from uuid import UUID


def migrate_tech_stack():
    """
    Migrate tech stack data from existing enrichments to masterdata tables.
    
    This script:
    1. Finds all enriched jobs (where enrichment_completed_at is not NULL)
    2. Extracts tech stack from llm_enrichment table
    3. Creates masterdata entries and job assignments
    """
    try:
        logger.info("Starting tech stack migration...")
        
        # Get all enriched jobs
        result = db.client.table("llm_enrichment")\
            .select("job_posting_id, must_have_programmeertalen, nice_to_have_programmeertalen, must_have_ecosystemen, nice_to_have_ecosystemen")\
            .not_.is_("enrichment_completed_at", "null")\
            .execute()
        
        if not result.data:
            logger.warning("No enriched jobs found")
            return
        
        total = len(result.data)
        logger.info(f"Found {total} enriched jobs to migrate")
        
        success_count = 0
        error_count = 0
        
        for i, enrichment in enumerate(result.data, 1):
            job_id = enrichment["job_posting_id"]
            
            try:
                # Parse PostgreSQL arrays
                must_have_languages = _parse_postgres_array(enrichment.get("must_have_programmeertalen"))
                nice_to_have_languages = _parse_postgres_array(enrichment.get("nice_to_have_programmeertalen"))
                must_have_ecosystems = _parse_postgres_array(enrichment.get("must_have_ecosystemen"))
                nice_to_have_ecosystems = _parse_postgres_array(enrichment.get("nice_to_have_ecosystemen"))
                
                # Create enrichment data structure
                enrichment_data = {
                    "must_have_languages": must_have_languages,
                    "nice_to_have_languages": nice_to_have_languages,
                    "must_have_ecosystems": must_have_ecosystems,
                    "nice_to_have_ecosystems": nice_to_have_ecosystems
                }
                
                # Process tech stack
                process_tech_stack_for_job(UUID(job_id), enrichment_data)
                
                success_count += 1
                
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{total} jobs processed")
                
            except Exception as e:
                logger.error(f"Failed to migrate job {job_id}: {e}")
                error_count += 1
        
        logger.success(f"✅ Migration complete!")
        logger.success(f"   Total jobs: {total}")
        logger.success(f"   Successfully migrated: {success_count}")
        logger.success(f"   Errors: {error_count}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()


def _parse_postgres_array(value):
    """Parse PostgreSQL array format: {"item1","item2"} or {item1,item2}"""
    if not value:
        return []
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []
    
    # Remove outer braces and split by comma
    cleaned = value.replace('{', '').replace('}', '')
    if not cleaned:
        return []
    
    # Split and clean quotes
    return [item.replace('"', '').strip() for item in cleaned.split(',') if item.strip()]


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Tech Stack Migration")
    logger.info("=" * 60)
    logger.info("\nThis will:")
    logger.info("1. Extract tech stack from existing enrichments")
    logger.info("2. Create masterdata entries for languages/ecosystems")
    logger.info("3. Create job assignments")
    logger.info("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
        migrate_tech_stack()
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled")
