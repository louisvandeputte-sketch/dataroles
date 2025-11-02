"""
Clear all company enrichment data from the database.
This resets all AI-enriched fields to NULL, allowing fresh enrichment with the new prompt.
"""

import sys
from loguru import logger
from database.client import db

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

def clear_enrichment_data():
    """Clear all enrichment data from company_master_data table."""
    
    logger.info("Starting to clear all enrichment data...")
    
    try:
        # Count records before clearing
        count_result = db.client.table("company_master_data")\
            .select("id", count="exact")\
            .execute()
        
        total_records = count_result.count if hasattr(count_result, 'count') else 0
        logger.info(f"Found {total_records} records in company_master_data")
        
        # Clear all enrichment fields
        logger.info("Clearing enrichment fields...")
        
        result = db.client.rpc('clear_all_enrichment_data').execute()
        
        logger.success(f"✅ Successfully cleared enrichment data!")
        logger.info("All AI-enriched fields have been reset to NULL")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clear enrichment data: {e}")
        logger.info("Trying alternative method with UPDATE statement...")
        
        try:
            # Alternative: Direct UPDATE (if RPC doesn't exist)
            # Note: This requires executing SQL directly in Supabase
            logger.warning("Please run the following SQL in Supabase SQL Editor:")
            print("\n" + "="*80)
            print("""
UPDATE company_master_data
SET 
    -- Company info enrichment
    bedrijfswebsite = NULL,
    jobspagina = NULL,
    email_hr = NULL,
    email_hr_bron = NULL,
    email_algemeen = NULL,
    bedrijfsomschrijving_nl = NULL,
    bedrijfsomschrijving_fr = NULL,
    bedrijfsomschrijving_en = NULL,
    sector_en = NULL,
    sector_nl = NULL,
    sector_fr = NULL,
    aantal_werknemers = NULL,
    ai_enriched = FALSE,
    ai_enriched_at = NULL,
    ai_enrichment_error = NULL,
    
    -- Size classification
    size_category = NULL,
    category_en = NULL,
    category_nl = NULL,
    category_fr = NULL,
    size_confidence = NULL,
    size_summary_en = NULL,
    size_summary_nl = NULL,
    size_summary_fr = NULL,
    size_key_arguments = NULL,
    size_sources = NULL,
    size_enriched_at = NULL,
    size_enrichment_error = NULL
WHERE ai_enriched = TRUE OR size_category IS NOT NULL;
            """)
            print("="*80 + "\n")
            
            return False
            
        except Exception as e2:
            logger.error(f"❌ Alternative method also failed: {e2}")
            return False

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("CLEAR ALL ENRICHMENT DATA")
    logger.info("="*80)
    logger.warning("⚠️  This will remove ALL enrichment data from the database!")
    logger.warning("⚠️  This action cannot be undone!")
    
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        success = clear_enrichment_data()
        if success:
            logger.success("✅ Done! You can now re-enrich companies with the new prompt v9.")
        else:
            logger.warning("⚠️  Please run the SQL statement manually in Supabase.")
    else:
        logger.info("❌ Operation cancelled.")
