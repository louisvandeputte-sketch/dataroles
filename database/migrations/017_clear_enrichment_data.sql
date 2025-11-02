-- Migration: Clear all enrichment data
-- Resets all AI-enriched fields to prepare for re-enrichment with new prompt v9
-- Date: 2025-10-29
-- WARNING: This will remove ALL enrichment data!

-- Clear all enrichment fields
UPDATE company_master_data
SET 
    -- Company info enrichment
    bedrijfswebsite = NULL,
    jobspagina = NULL,
    email_hr = NULL,
    email_hr_bron = NULL,
    email_algemeen = NULL,
    bedrijfsomschrijving_nl = NULL,
    bedrijfsomschrijving_fr = NULL,
    bedrijfsomschrijving_en = NULL,
    sector_en = NULL,
    sector_nl = NULL,
    sector_fr = NULL,
    aantal_werknemers = NULL,
    ai_enriched = FALSE,
    ai_enriched_at = NULL,
    ai_enrichment_error = NULL,
    
    -- Size classification
    size_category = NULL,
    category_en = NULL,
    category_nl = NULL,
    category_fr = NULL,
    size_confidence = NULL,
    size_summary_en = NULL,
    size_summary_nl = NULL,
    size_summary_fr = NULL,
    size_key_arguments = NULL,
    size_sources = NULL,
    size_enriched_at = NULL,
    size_enrichment_error = NULL
WHERE ai_enriched = TRUE OR size_category IS NOT NULL;

-- Log the result
-- This will show how many records were cleared
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN ai_enriched = TRUE THEN 1 END) as still_enriched,
    COUNT(CASE WHEN size_category IS NOT NULL THEN 1 END) as still_classified
FROM company_master_data;
