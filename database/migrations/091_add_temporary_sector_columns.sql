-- Migration: Add temporary sector columns to company_master_data table
-- These columns will be populated using LLM parser for sector standardization

ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS sector_en_temporary TEXT,
ADD COLUMN IF NOT EXISTS sector_nl_temporary TEXT,
ADD COLUMN IF NOT EXISTS sector_fr_temporary TEXT;

COMMENT ON COLUMN company_master_data.sector_en_temporary IS 'Temporary column for LLM-standardized sector in English';
COMMENT ON COLUMN company_master_data.sector_nl_temporary IS 'Temporary column for LLM-standardized sector in Dutch';
COMMENT ON COLUMN company_master_data.sector_fr_temporary IS 'Temporary column for LLM-standardized sector in French';
