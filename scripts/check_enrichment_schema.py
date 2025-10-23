"""Check if enrichment table has the new multilingual columns."""

from loguru import logger
from database.client import db

def check_schema():
    """Check llm_enrichment table schema."""
    try:
        logger.info("Checking llm_enrichment table schema...")
        
        # Try to get one record to see available columns
        result = db.client.table("llm_enrichment")\
            .select("*")\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            columns = list(result.data[0].keys())
            logger.info(f"Found {len(columns)} columns:")
            for col in sorted(columns):
                logger.info(f"  - {col}")
            
            # Check for new multilingual columns
            required_cols = [
                'samenvatting_kort_nl',
                'samenvatting_kort_fr',
                'samenvatting_kort_en',
                'samenvatting_lang_nl',
                'samenvatting_lang_fr',
                'samenvatting_lang_en',
                'labels'
            ]
            
            missing = [col for col in required_cols if col not in columns]
            
            if missing:
                logger.warning(f"⚠️  Missing columns: {missing}")
                logger.warning("You need to run migration 005!")
                logger.info("\nRun this SQL in Supabase:")
                logger.info("=" * 60)
                with open('database/migrations/005_add_multilingual_enrichment.sql', 'r') as f:
                    print(f.read())
                logger.info("=" * 60)
            else:
                logger.success("✅ All required columns exist!")
        else:
            logger.warning("No records found in llm_enrichment table")
            
    except Exception as e:
        logger.error(f"Failed to check schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_schema()
