#!/usr/bin/env python3
"""Run migration 021: Add company weetjes (factlets)."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.client import db
from loguru import logger

def run_migration():
    """Execute migration 021."""
    
    migration_sql = """
-- Migration: Add company weetjes (factlets) field
-- Stores multilingual factlets with category, source, confidence, and verification date

-- Add weetjes JSONB column to company_master_data
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS weetjes JSONB;

-- Add sector_nl and sector_fr for multilingual sector support (sector_en already exists)
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS sector_nl TEXT,
ADD COLUMN IF NOT EXISTS sector_fr TEXT;

-- Add index for JSONB queries on weetjes
CREATE INDEX IF NOT EXISTS idx_company_master_data_weetjes 
ON company_master_data USING GIN (weetjes);

-- Add index for sector fields
CREATE INDEX IF NOT EXISTS idx_company_master_data_sector_nl 
ON company_master_data(sector_nl) 
WHERE sector_nl IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_master_data_sector_fr 
ON company_master_data(sector_fr) 
WHERE sector_fr IS NOT NULL;
"""
    
    try:
        logger.info("Running migration 021: Add company weetjes")
        
        # Execute migration
        db.client.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        logger.success("Migration 021 completed successfully!")
        
        # Verify columns were added
        result = db.client.table("company_master_data").select("*").limit(1).execute()
        logger.info(f"Verified company_master_data columns: {list(result.data[0].keys()) if result.data else 'No data yet'}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
