-- Migration: Add company size classification fields
-- Stores LLM-enriched company maturity stage classification
-- Date: 2025-10-28

-- Add company size classification fields
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS size_category TEXT CHECK (size_category IN (
    'startup', 
    'scaleup', 
    'sme', 
    'established_enterprise', 
    'corporate', 
    'public_company', 
    'government',
    'unknown'
)),
ADD COLUMN IF NOT EXISTS size_confidence DECIMAL(3,2) CHECK (size_confidence >= 0 AND size_confidence <= 1),
ADD COLUMN IF NOT EXISTS size_summary_en TEXT,
ADD COLUMN IF NOT EXISTS size_summary_nl TEXT,
ADD COLUMN IF NOT EXISTS size_summary_fr TEXT,
ADD COLUMN IF NOT EXISTS size_key_arguments JSONB,
ADD COLUMN IF NOT EXISTS size_sources JSONB,
ADD COLUMN IF NOT EXISTS size_enriched_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS size_enrichment_error TEXT;

-- Add indexes for filtering and performance
CREATE INDEX IF NOT EXISTS idx_company_size_category 
    ON company_master_data(size_category) 
    WHERE size_category IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_size_enriched 
    ON company_master_data(size_enriched_at) 
    WHERE size_enriched_at IS NOT NULL;

-- Add comments
COMMENT ON COLUMN company_master_data.size_category IS 'Company maturity stage: startup, scaleup, sme, established_enterprise, corporate, public_company, government, unknown';
COMMENT ON COLUMN company_master_data.size_confidence IS 'LLM confidence score (0-1) for size classification';
COMMENT ON COLUMN company_master_data.size_summary_en IS 'English summary of company size classification';
COMMENT ON COLUMN company_master_data.size_summary_nl IS 'Dutch summary of company size classification';
COMMENT ON COLUMN company_master_data.size_summary_fr IS 'French summary of company size classification';
COMMENT ON COLUMN company_master_data.size_key_arguments IS 'JSON array of key arguments supporting the classification';
COMMENT ON COLUMN company_master_data.size_sources IS 'JSON array of source URLs used for classification';
COMMENT ON COLUMN company_master_data.size_enriched_at IS 'Timestamp when size classification was performed';
COMMENT ON COLUMN company_master_data.size_enrichment_error IS 'Error message if enrichment failed';
