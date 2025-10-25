-- Migration: Add company enrichment fields
-- Add fields for LLM-enriched company data
-- Date: 2025-10-25

-- Add enrichment fields to company_master_data
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS bedrijfswebsite TEXT,
ADD COLUMN IF NOT EXISTS jobspagina TEXT,
ADD COLUMN IF NOT EXISTS email_hr TEXT,
ADD COLUMN IF NOT EXISTS email_hr_bron TEXT,
ADD COLUMN IF NOT EXISTS email_algemeen TEXT,
ADD COLUMN IF NOT EXISTS bedrijfsomschrijving TEXT,
ADD COLUMN IF NOT EXISTS ai_enriched BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ai_enriched_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS ai_enrichment_error TEXT;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_company_master_data_ai_enriched 
ON company_master_data(ai_enriched) 
WHERE ai_enriched = TRUE;

CREATE INDEX IF NOT EXISTS idx_company_master_data_email_hr 
ON company_master_data(email_hr) 
WHERE email_hr IS NOT NULL;

-- Add comments
COMMENT ON COLUMN company_master_data.bedrijfswebsite IS 'Company website URL (AI enriched)';
COMMENT ON COLUMN company_master_data.jobspagina IS 'Company jobs/careers page URL (AI enriched)';
COMMENT ON COLUMN company_master_data.email_hr IS 'HR/recruitment contact email (AI enriched)';
COMMENT ON COLUMN company_master_data.email_hr_bron IS 'Source URL where HR email was found (AI enriched)';
COMMENT ON COLUMN company_master_data.email_algemeen IS 'General company contact email (AI enriched)';
COMMENT ON COLUMN company_master_data.bedrijfsomschrijving IS 'Company description in Dutch (AI enriched)';
COMMENT ON COLUMN company_master_data.ai_enriched IS 'Whether company data has been enriched by AI';
COMMENT ON COLUMN company_master_data.ai_enriched_at IS 'Timestamp when AI enrichment was performed';
COMMENT ON COLUMN company_master_data.ai_enrichment_error IS 'Error message if AI enrichment failed';
