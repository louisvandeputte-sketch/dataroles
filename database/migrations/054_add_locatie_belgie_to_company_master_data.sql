-- Migration 054: Add locatie_belgie field to company_master_data
-- Date: 2025-11-18
-- Description: store Belgian HQ/location city captured by company enrichment prompt v20

ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS locatie_belgie TEXT;

COMMENT ON COLUMN company_master_data.locatie_belgie IS 'Primary city of Belgian headquarters or largest Belgian office (e.g., Brussel, Antwerpen, Gent).';
