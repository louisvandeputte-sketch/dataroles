-- Migration 044: Create vw_job_listings view
-- Date: 2025-11-16
-- Description: Duplicate of llm_enrichment_active with frontend-friendly name

DROP VIEW IF EXISTS vw_job_listings;

CREATE OR REPLACE VIEW vw_job_listings AS
SELECT 
    e.job_posting_id,
    
    -- Job info from job_postings (for convenience)
    j.title,                   -- Job title
    j.posted_date,             -- Job posting date
    j.ranking_position,        -- Ranking position (1 = best)
    
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
    cmd.size_summary_nl,       -- Dutch size summary
    cmd.size_summary_en,       -- English size summary
    cmd.size_summary_fr,       -- French size summary
    cmd.size_confidence,       -- Confidence score for size classification
    
    -- Additional company metadata
    cmd.aantal_werknemers,     -- Number of employees
    cmd.founded_year,          -- Company founding year
    cmd.industry,              -- Industry (from original data)
    
    -- Location info (multilingual) from locations
    l.city_name_nl,            -- City name in Dutch
    l.city_name_en,            -- City name in English
    l.city_name_fr,            -- City name in French
    l.subdivision_name_nl,     -- Province/state/region in Dutch
    l.subdivision_name_en,     -- Province/state/region in English
    l.subdivision_name_fr,     -- Province/state/region in French
    
    -- Core classification fields (ACTIVE - used for filtering)
    e.type_datarol,            -- Data role type (Data Engineer, Data Analyst, etc.)
    e.rolniveau,               -- Role level array (Technical, Lead, Managerial)
    e.seniority,               -- Seniority array (Junior, Medior, Senior, Expert)
    e.contract,                -- Contract type array (Permanent, Freelance, Intern)
    e.sourcing_type,           -- Sourcing type (Direct, Agency)
    
    -- Multilingual labels (ACTIVE - contains all translations)
    e.labels,                  -- JSONB with NL/EN/FR translations for all fields
    
    -- Summaries in 3 languages (ACTIVE)
    e.samenvatting_kort_en,
    e.samenvatting_lang_en,
    e.samenvatting_kort_nl,
    e.samenvatting_lang_nl,
    e.samenvatting_kort_fr,
    e.samenvatting_lang_fr,
    
    -- Legacy summary fields (ACTIVE - for backward compatibility)
    e.samenvatting_kort,       -- Legacy: English summary
    e.samenvatting_lang,       -- Legacy: English summary
    
    -- Tech stack (ACTIVE)
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    
    -- Spoken/written languages (ACTIVE)
    e.must_have_talen,
    e.nice_to_have_talen,
    
    -- Remote work policy (ACTIVE)
    e.remote_work_policy,
    
    -- Perks v17 (ACTIVE - individual columns)
    e.perk_remote_policy,
    e.perk_salary_range,
    e.perk_company_car,
    e.perk_hospitalization_insurance,
    e.perk_training_budget,
    e.perk_team_events,
    
    -- Metadata (ACTIVE)
    e.enrichment_completed_at,
    e.enrichment_error,
    e.enrichment_model_version,
    e.created_at
    
    -- EXCLUDED DEPRECATED FIELDS:
    -- perks_OLD_deprecated (replaced by perk_* columns)
    -- Any other deprecated fields from migration 034
    
FROM llm_enrichment e
LEFT JOIN job_postings j ON e.job_posting_id = j.id
LEFT JOIN companies c ON j.company_id = c.id
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN locations l ON j.location_id = l.id;

COMMENT ON VIEW vw_job_listings IS 
'Frontend-friendly view for job listings with complete enrichment data.
Includes: 
- Job classification (type_datarol, rolniveau, seniority, contract, sourcing_type)
- Company info (name, logo, sector in NL/EN/FR, size category in NL/EN/FR)
- Location info (city and subdivision names in NL/EN/FR)
- Multilingual labels, summaries in 3 languages
- Tech stack, spoken languages, remote work policy
- Individual perk columns (v17)
- Metadata
Created: 2025-11-16 for frontend clarity.
Updated: 2025-11-16 to include location multilingual fields.';
