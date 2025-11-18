-- Run migrations 049 and 050 to fix NIS job rankings
-- Run this in Supabase SQL Editor

-- Migration 049: Add title_classification to vw_job_listings
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
    
FROM llm_enrichment e
LEFT JOIN job_postings j ON e.job_posting_id = j.id
LEFT JOIN companies c ON j.company_id = c.id
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN locations l ON j.location_id = l.id;

COMMENT ON VIEW vw_job_listings IS 
'Frontend-friendly view for job listings with complete enrichment data.
Includes title_classification field for filtering Data vs NIS jobs.';

-- Migration 050: Update job_ranking_view to include NIS jobs
CREATE OR REPLACE VIEW job_ranking_view AS
SELECT 
    -- Job posting fields (verified from job_postings table)
    jp.id,
    jp.title,
    jp.company_id,
    jp.location_id,
    jp.posted_date,
    jp.seniority_level,
    jp.employment_type,
    jp.function_areas,
    jp.base_salary_min,
    jp.base_salary_max,
    jp.apply_url,
    jp.num_applicants,
    jp.is_active,
    jp.title_classification,
    
    -- Company fields (verified from companies table)
    c.name as company_name,
    c.industry as company_industry,
    c.company_url,
    c.logo_data as company_logo_data,
    c.employee_count_range as company_employee_count_range,
    c.rating as company_rating,
    c.reviews_count as company_reviews_count,
    
    -- Company master data (verified from company_master_data table)
    cmd.hiring_model,
    
    -- Location fields (verified from locations table)
    l.city as location_city,
    
    -- LLM Enrichment fields (verified from llm_enrichment table)
    e.enrichment_completed_at,
    e.type_datarol as data_role_type,
    e.hard_skills as skills_must_have,
    e.samenvatting_kort_nl as samenvatting_kort,
    e.samenvatting_lang_nl as samenvatting_lang,
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    e.labels,
    
    -- Job description (verified from job_descriptions table)
    jd.full_description_text as description_text
    
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN locations l ON jp.location_id = l.id
LEFT JOIN llm_enrichment e ON jp.id = e.job_posting_id
LEFT JOIN job_descriptions jd ON jp.id = jd.job_posting_id
WHERE jp.is_active = true;
-- Now includes all active jobs (Data, NIS, Other) so NIS jobs can be ranked with 999999

COMMENT ON VIEW job_ranking_view IS 'Denormalized view for job ranking with all necessary joins pre-computed. Includes all active jobs (Data, NIS, Other) for ranking. NIS jobs will be assigned rank 999999.';

-- Done! Now run: python scripts/auto_calculate_rankings.py
