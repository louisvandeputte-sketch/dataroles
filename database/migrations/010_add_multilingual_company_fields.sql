-- Migration: Add multilingual company descriptions and employee count
-- Extends company enrichment with NL/FR/EN descriptions and employee count
-- Date: 2025-10-26

-- Add multilingual description fields and employee count
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS bedrijfsomschrijving_nl TEXT,
ADD COLUMN IF NOT EXISTS bedrijfsomschrijving_fr TEXT,
ADD COLUMN IF NOT EXISTS bedrijfsomschrijving_en TEXT,
ADD COLUMN IF NOT EXISTS sector_en TEXT,
ADD COLUMN IF NOT EXISTS aantal_werknemers TEXT;

-- Drop old single-language description column (data will be migrated to _nl)
-- First migrate existing data to NL version
UPDATE company_master_data 
SET bedrijfsomschrijving_nl = bedrijfsomschrijving 
WHERE bedrijfsomschrijving IS NOT NULL AND bedrijfsomschrijving_nl IS NULL;

-- Now we can drop the old column
ALTER TABLE company_master_data DROP COLUMN IF EXISTS bedrijfsomschrijving;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_company_master_data_sector 
ON company_master_data(sector_en) 
WHERE sector_en IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_master_data_employees 
ON company_master_data(aantal_werknemers) 
WHERE aantal_werknemers IS NOT NULL;

-- Add comments
COMMENT ON COLUMN company_master_data.bedrijfsomschrijving_nl IS 'Company description in Dutch (AI enriched)';
COMMENT ON COLUMN company_master_data.bedrijfsomschrijving_fr IS 'Company description in French (AI enriched)';
COMMENT ON COLUMN company_master_data.bedrijfsomschrijving_en IS 'Company description in English (AI enriched)';
COMMENT ON COLUMN company_master_data.sector_en IS 'Company sector/industry in English (AI enriched)';
COMMENT ON COLUMN company_master_data.aantal_werknemers IS 'Estimated number of employees (AI enriched)';
