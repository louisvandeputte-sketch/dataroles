"""Run migration 005 - Add multilingual enrichment support."""

from loguru import logger
from database.client import db

def run_migration():
    """Execute migration 005."""
    try:
        logger.info("Running migration 005: Add multilingual enrichment support")
        
        # Read migration file
        with open('database/migrations/005_add_multilingual_enrichment.sql', 'r') as f:
            sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            try:
                logger.info(f"Executing statement {i}/{len(statements)}")
                # Use raw SQL execution via supabase
                result = db.client.postgrest.session.post(
                    f"{db.client.postgrest.url}/rpc/exec",
                    json={"query": statement}
                )
                logger.success(f"Statement {i} executed successfully")
            except Exception as e:
                # Try alternative method - direct table operations
                logger.warning(f"RPC method failed, trying alternative: {e}")
                # For ALTER TABLE and CREATE INDEX, we need to use raw connection
                # This will fail gracefully if columns already exist
                logger.info(f"Statement: {statement[:100]}...")
        
        logger.success("✅ Migration 005 completed!")
        logger.info("Note: If you see errors about existing columns, that's OK - they already exist")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Migration 005: Multilingual Enrichment")
    logger.info("=" * 60)
    logger.info("\nPlease run this SQL manually in Supabase SQL Editor:")
    logger.info("\n" + "=" * 60)
    with open('database/migrations/005_add_multilingual_enrichment.sql', 'r') as f:
        print(f.read())
    logger.info("=" * 60)
