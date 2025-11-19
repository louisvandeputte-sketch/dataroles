-- Migration 059: Re-enable location_id_override in vw_job_listings
-- Date: 2025-11-19
-- Description: Use location_id_override in view to show specific location when available
--              Falls back to original location_id if override is NULL

DROP VIEW IF EXISTS vw_job_listings;

CREATE OR REPLACE VIEW vw_job_listings AS
SELECT 
    e.job_posting_id,
    
    -- Job info from job_postings (for convenience)
    j.title,                   -- Job title
    j.posted_date,             -- Job posting date
    j.ranking_position,        -- Ranking position (1 = best)
    j.title_classification,    -- Title classification (Data, NIS, Other)
    
    -- Company info from companies (for convenience)
    c.logo_url,                -- Company logo URL
    c.name AS company_name,    -- Company name
    
    -- Company sector (multilingual) from company_master_data
    cmd.sector_nl,             -- Company sector in Dutch
    cmd.sector_en,             -- Company sector in English
    cmd.sector_fr,             -- Company sector in French
    
    -- Company size category (multilingual) from company_master_data
    cmd.size_category,         -- Size category enum (startup, scaleup, sme, etc.)
    cmd.category_nl,           -- Category in Dutch (startup, scaleup, kmo, etc.)
    cmd.category_en,           -- Category in English (startup, scaleup, sme, etc.)
    cmd.category_fr,           -- Category in French (startup, scaleup, pme, etc.)
    
    -- Location override: Use override if available, otherwise use original location
    -- This allows showing specific city when job location is vague (e.g., "Flemish Region")
    COALESCE(j.location_id_override, j.location_id) AS location_id,
    
    -- Contract type (multilingual) from llm_enrichment
    le.contract_nl,            -- Contract type in Dutch (Voltijds, Deeltijds, etc.)
    le.contract_en,            -- Contract type in English (Full-time, Part-time, etc.)
    le.contract_fr,            -- Contract type in French (Temps plein, Temps partiel, etc.)
    
    -- Seniority level (multilingual) from llm_enrichment
    le.seniority_nl,           -- Seniority in Dutch (Junior, Medior, Senior, etc.)
    le.seniority_en,           -- Seniority in English (Junior, Medior, Senior, etc.)
    le.seniority_fr,           -- Seniority in French (Junior, Confirmé, Senior, etc.)
    
    -- Data role type (multilingual) from llm_enrichment
    le.type_datarol_nl,        -- Data role type in Dutch (Data Engineer, Data Scientist, etc.)
    le.type_datarol_en,        -- Data role type in English (Data Engineer, Data Scientist, etc.)
    le.type_datarol_fr         -- Data role type in French (Ingénieur de données, Data Scientist, etc.)

FROM llm_enrichment e
JOIN job_postings j ON e.job_posting_id = j.id
JOIN companies c ON j.company_id = c.id
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN llm_enrichment le ON j.id = le.job_posting_id
WHERE j.is_active = TRUE
  AND j.title_classification = 'Data';

-- Add comment explaining the override logic
COMMENT ON VIEW vw_job_listings IS 'View of enriched job listings with location override support. Uses location_id_override when available (for vague locations like "Flemish Region"), otherwise falls back to original location_id. This allows showing specific city from company master data when job location is vague.';
