-- Migration 061: Add Belgian headquarters location to company_master_data
-- Date: 2025-11-21
-- Description: Add hoofdkantoor_be (Belgian office location) for company enrichment prompt v21

-- Add Belgian headquarters city field (in native language)
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS hoofdkantoor_be TEXT;

-- Add comment
COMMENT ON COLUMN company_master_data.hoofdkantoor_be IS 'Primary Belgian office location - city name in native language (e.g., "Gent", "Antwerpen", "Bruxelles", "Zaventem"). For international companies: main Belgian HQ or largest Belgian office.';
