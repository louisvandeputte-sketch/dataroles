-- Migration: Remove CHECK constraint on size_category
-- Allows flexible category values from LLM without database-level validation
-- Date: 2025-10-29

-- Remove the CHECK constraint
ALTER TABLE company_master_data
DROP CONSTRAINT IF EXISTS company_master_data_size_category_check;

-- Add index for performance (if not exists)
CREATE INDEX IF NOT EXISTS idx_company_size_category 
    ON company_master_data(size_category) 
    WHERE size_category IS NOT NULL;

-- Update comment to reflect flexibility
COMMENT ON COLUMN company_master_data.size_category IS 'Company maturity stage (flexible, determined by LLM). Common values: startup, scaleup, sme, midmarket, corporate, subsidiary, government, unknown';
