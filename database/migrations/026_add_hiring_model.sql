-- Migration: Add hiring_model fields for company enrichment v15
-- Date: 2025-11-09

-- Add hiring_model columns (canonical + multilingual)
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS hiring_model TEXT,
ADD COLUMN IF NOT EXISTS hiring_model_en TEXT,
ADD COLUMN IF NOT EXISTS hiring_model_nl TEXT,
ADD COLUMN IF NOT EXISTS hiring_model_fr TEXT;

-- Add comments
COMMENT ON COLUMN company_master_data.hiring_model IS 'Canonical hiring model: recruitment, direct, or unknown';
COMMENT ON COLUMN company_master_data.hiring_model_en IS 'Hiring model in English: Recruitment, Direct, or Unknown';
COMMENT ON COLUMN company_master_data.hiring_model_nl IS 'Hiring model in Dutch: Recruitment, Direct, or Onbekend';
COMMENT ON COLUMN company_master_data.hiring_model_fr IS 'Hiring model in French: Recrutement, Direct, or Inconnu';

-- Add index for filtering by hiring model
CREATE INDEX IF NOT EXISTS idx_company_master_data_hiring_model 
ON company_master_data(hiring_model) 
WHERE hiring_model IS NOT NULL;

-- Add check constraint for canonical values
ALTER TABLE company_master_data
ADD CONSTRAINT check_hiring_model_values 
CHECK (hiring_model IS NULL OR hiring_model IN ('recruitment', 'direct', 'unknown'));
