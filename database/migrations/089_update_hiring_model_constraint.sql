-- Migration 089: Update hiring_model constraint for capitalized values
-- Date: 2025-12-31
-- Description: Update check constraint to accept capitalized hiring_model values (Recruitment, Direct, Unknown)

-- First, drop the old constraint so we can update values
ALTER TABLE company_master_data
DROP CONSTRAINT IF EXISTS check_hiring_model_values;

-- Update existing lowercase values to capitalized
UPDATE company_master_data 
SET hiring_model = INITCAP(hiring_model)
WHERE hiring_model IN ('recruitment', 'direct', 'unknown');

-- Add new constraint with capitalized values
ALTER TABLE company_master_data
ADD CONSTRAINT check_hiring_model_values 
CHECK (hiring_model IS NULL OR hiring_model IN ('Recruitment', 'Direct', 'Unknown'));

-- Update comment
COMMENT ON COLUMN company_master_data.hiring_model IS 'Canonical hiring model: Recruitment, Direct, or Unknown';
