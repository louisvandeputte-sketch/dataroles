-- Migration: Update size category values
-- Updates allowed categories and migrates old values to new ones
-- Date: 2025-10-29

-- Step 1: Drop the old CHECK constraint
ALTER TABLE company_master_data
DROP CONSTRAINT IF EXISTS company_master_data_size_category_check;

-- Step 2: Migrate old category values to new ones
-- established_enterprise → midmarket (closest match)
UPDATE company_master_data
SET size_category = 'midmarket'
WHERE size_category = 'established_enterprise';

-- public_company → corporate (closest match, as they're large companies)
UPDATE company_master_data
SET size_category = 'corporate'
WHERE size_category = 'public_company';

-- Step 3: Add new CHECK constraint with updated categories
ALTER TABLE company_master_data
ADD CONSTRAINT company_master_data_size_category_check
CHECK (size_category IN (
    'startup',
    'scaleup',
    'sme',
    'midmarket',
    'corporate',
    'subsidiary',
    'government',
    'unknown'
));

-- Update comment
COMMENT ON COLUMN company_master_data.size_category IS 'Company maturity stage: startup, scaleup, sme, midmarket, corporate, subsidiary, government, unknown';
