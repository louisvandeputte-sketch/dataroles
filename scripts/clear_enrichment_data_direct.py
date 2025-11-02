"""
Clear all company enrichment data from the database (direct execution).
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
        # Get all enriched companies
        logger.info("Fetching enriched companies...")
        
        result = db.client.table("company_master_data")\
            .select("company_id")\
            .or_("ai_enriched.eq.true,size_category.not.is.null")\
            .execute()
        
        company_ids = [row['company_id'] for row in result.data] if result.data else []
        total = len(company_ids)
        
        logger.info(f"Found {total} companies with enrichment data")
        
        if total == 0:
            logger.info("No enrichment data to clear!")
            return True
        
        # Clear enrichment data in batches
        batch_size = 100
        cleared = 0
        
        for i in range(0, total, batch_size):
            batch = company_ids[i:i+batch_size]
            
            # Update batch
            update_data = {
                # Company info enrichment
                "bedrijfswebsite": None,
                "jobspagina": None,
                "email_hr": None,
                "email_hr_bron": None,
                "email_algemeen": None,
                "bedrijfsomschrijving_nl": None,
                "bedrijfsomschrijving_fr": None,
                "bedrijfsomschrijving_en": None,
                "sector_en": None,
                "sector_nl": None,
                "sector_fr": None,
                "aantal_werknemers": None,
                "ai_enriched": False,
                "ai_enriched_at": None,
                "ai_enrichment_error": None,
                # Size classification
                "size_category": None,
                "category_en": None,
                "category_nl": None,
                "category_fr": None,
                "size_confidence": None,
                "size_key_arguments": None,
                "size_sources": None,
                "size_enriched_at": None,
                "size_enrichment_error": None
            }
            
            for company_id in batch:
                db.client.table("company_master_data")\
                    .update(update_data)\
                    .eq("company_id", company_id)\
                    .execute()
                cleared += 1
            
            logger.info(f"Progress: {cleared}/{total} companies cleared ({(cleared/total*100):.1f}%)")
        
        logger.success(f"✅ Successfully cleared enrichment data for {cleared} companies!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clear enrichment data: {e}")
        logger.exception(e)
        return False

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("CLEAR ALL ENRICHMENT DATA")
    logger.info("="*80)
    
    success = clear_enrichment_data()
    
    if success:
        logger.success("✅ Done! You can now re-enrich companies with the new prompt v9.")
    else:
        logger.error("❌ Failed. Please run migration 017 manually in Supabase.")
