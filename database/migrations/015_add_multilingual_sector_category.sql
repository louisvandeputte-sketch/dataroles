-- Migration: Add multilingual sector and category fields
-- Adds NL/FR translations for sector and category
-- Date: 2025-10-28

-- Add multilingual sector fields
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS sector_nl TEXT,
ADD COLUMN IF NOT EXISTS sector_fr TEXT;

-- Add multilingual category fields
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS category_en TEXT,
ADD COLUMN IF NOT EXISTS category_nl TEXT,
ADD COLUMN IF NOT EXISTS category_fr TEXT;

-- Add comments
COMMENT ON COLUMN company_master_data.sector_nl IS 'Company sector in Dutch';
COMMENT ON COLUMN company_master_data.sector_fr IS 'Company sector in French';
COMMENT ON COLUMN company_master_data.category_en IS 'Company maturity category in English (startup, scaleup, sme, etc.)';
COMMENT ON COLUMN company_master_data.category_nl IS 'Company maturity category in Dutch (startup, scaleup, kmo, etc.)';
COMMENT ON COLUMN company_master_data.category_fr IS 'Company maturity category in French (startup, scaleup, pme, etc.)';
