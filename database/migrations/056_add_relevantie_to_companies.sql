-- Migration 056: Add relevantie and show_in_app columns to company_master_data
-- Date: 2025-12-30
-- Description: Add a manual relevance score (integer) and show_in_app flag for companies

-- Add relevantie column to company_master_data
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS relevantie INTEGER;

COMMENT ON COLUMN company_master_data.relevantie IS 'Manual relevance score for the company (any integer value)';

-- Add show_in_app column (defaults to true for all companies)
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS show_in_app BOOLEAN DEFAULT true;

COMMENT ON COLUMN company_master_data.show_in_app IS 'Whether to show this company in the app (default: true)';

-- Recreate companies_list_view to include relevantie and show_in_app
DROP VIEW IF EXISTS companies_list_view;

CREATE VIEW companies_list_view AS
SELECT 
    c.id,
    c.name,
    c.logo_url,
    c.industry,
    c.linkedin_company_id,
    
    cmd.id AS master_data_id,
    cmd.hiring_model,
    cmd.is_consulting,
    cmd.sector_nl,
    cmd.sector_en,
    cmd.sector_fr,
    cmd.size_category,
    cmd.category_nl,
    cmd.category_en,
    cmd.category_fr,
    cmd.locatie_belgie,
    cmd.aantal_werknemers,
    cmd.bedrijfswebsite,
    cmd.jobspagina,
    cmd.email_hr,
    cmd.ai_enriched,
    cmd.ai_enriched_at,
    cmd.relevantie,
    cmd.show_in_app,
    
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id) AS job_count,
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id AND jp.is_active = true) AS active_job_count
FROM companies c
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
ORDER BY c.name;

COMMENT ON VIEW companies_list_view IS 'Lightweight view for companies list interface including relevantie score, show_in_app flag, canonical size_category, multilingual sectors/categories, locatie_belgie and essential job metrics.';

-- Also update job_ranking_view to include relevantie and show_in_app for ranking logic
DROP VIEW IF EXISTS job_ranking_view;

CREATE OR REPLACE VIEW job_ranking_view AS
SELECT 
    -- Job posting fields
    jp.id,
    jp.title,
    jp.company_id,
    jp.location_id,
    jp.posted_date,
    jp.posted_date_corrected,
    jp.seniority_level,
    jp.employment_type,
    jp.function_areas,
    jp.base_salary_min,
    jp.base_salary_max,
    jp.apply_url,
    jp.num_applicants,
    jp.is_active,
    jp.title_classification,
    
    -- Company fields
    c.name as company_name,
    c.industry as company_industry,
    c.company_url,
    c.logo_data as company_logo_data,
    c.employee_count_range as company_employee_count_range,
    c.rating as company_rating,
    c.reviews_count as company_reviews_count,
    
    -- Company master data
    cmd.hiring_model,
    cmd.relevantie,
    cmd.show_in_app,
    
    -- Location fields
    l.city as location_city,
    
    -- LLM Enrichment fields
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
    
    -- Job description
    jd.full_description_text as description_text
    
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN locations l ON jp.location_id = l.id
LEFT JOIN llm_enrichment e ON jp.id = e.job_posting_id
LEFT JOIN job_descriptions jd ON jp.id = jd.job_posting_id
WHERE jp.is_active = true;

COMMENT ON VIEW job_ranking_view IS 'Denormalized view for job ranking including company relevantie and show_in_app fields for ranking logic.';

-- Also update vw_job_listings to include show_in_app and filter on it
DROP VIEW IF EXISTS vw_job_listings;

CREATE OR REPLACE VIEW vw_job_listings AS
SELECT 
    e.job_posting_id,
    j.title,
    j.posted_date,
    j.ranking_position,
    j.base_score,
    j.ranking_score,
    j.hourly_multiplier,
    j.ranking_metadata,
    j.title_classification,
    js.first_seen_at,
    LEAST(js.first_seen_at, j.posted_date) as posted_date_corrected,
    
    -- Time ago in Dutch
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 7 THEN 'Nieuw'
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 14 THEN 
            FLOOR(EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400)::TEXT || ' dagen geleden'
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 30 THEN
            FLOOR(EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 604800)::TEXT || ' weken geleden'
        ELSE 'meer dan 1 maand geleden'
    END AS time_ago_nl,
    
    -- Time ago in French
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 7 THEN 'Nouveau'
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 14 THEN 
            'il y a ' || FLOOR(EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400)::TEXT || ' jours'
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 30 THEN
            'il y a ' || FLOOR(EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 604800)::TEXT || ' semaines'
        ELSE 'il y a plus d''un mois'
    END AS time_ago_fr,
    
    -- Time ago in English
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 7 THEN 'New'
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 14 THEN 
            FLOOR(EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400)::TEXT || ' days ago'
        WHEN EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 86400 < 30 THEN
            FLOOR(EXTRACT(EPOCH FROM (NOW() - LEAST(js.first_seen_at, j.posted_date))) / 604800)::TEXT || ' weeks ago'
        ELSE 'more than 1 month ago'
    END AS time_ago_en,
    
    -- Company fields
    c.id AS company_id,
    c.logo_url,
    c.name AS company_name,
    cmd.sector_nl,
    cmd.sector_en,
    cmd.sector_fr,
    cmd.size_category,
    cmd.category_nl,
    cmd.category_en,
    cmd.category_fr,
    cmd.size_summary_nl,
    cmd.size_summary_en,
    cmd.size_summary_fr,
    cmd.size_confidence,
    cmd.aantal_werknemers,
    cmd.founded_year,
    cmd.industry,
    cmd.show_in_app,
    cmd.hiring_model_nl,
    
    -- Location fields
    COALESCE(j.location_id_override, j.location_id) AS location_id,
    l.city_name_nl,
    l.city_name_en,
    l.city_name_fr,
    l.subdivision_name_nl,
    l.subdivision_name_en,
    l.subdivision_name_fr,
    l.country_name_nl,
    l.country_name_en,
    l.country_name_fr,
    l.longitude,
    l.latitude,
    l.country_code_3,
    l.timezone,
    l.city_official_name,
    l.country_name,
    
    -- Job enrichment fields
    e.type_datarol,
    e.rolniveau,
    e.seniority,
    e.contract,
    e.sourcing_type,
    e.labels,
    e.samenvatting_kort_en,
    e.samenvatting_kort_nl,
    e.samenvatting_kort_fr,
    e.samenvatting_kort,
    e.samenvatting_lang_en,
    e.samenvatting_lang_nl,
    e.samenvatting_lang_fr,
    e.samenvatting_lang,
    e.responsibilities,
    e.responsibilities_nl,
    e.responsibilities_fr,
    e.requirements,
    e.requirements_nl,
    e.requirements_fr,
    e.offerings,
    e.offerings_nl,
    e.offerings_fr,
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    
    -- Spoken languages in English (original)
    e.must_have_talen,
    e.nice_to_have_talen,
    
    -- Spoken languages in Dutch
    translate_language_array(e.must_have_talen, 'nl') AS must_have_talen_nl,
    translate_language_array(e.nice_to_have_talen, 'nl') AS nice_to_have_talen_nl,
    
    -- Spoken languages in French
    translate_language_array(e.must_have_talen, 'fr') AS must_have_talen_fr,
    translate_language_array(e.nice_to_have_talen, 'fr') AS nice_to_have_talen_fr,
    
    e.created_at
FROM llm_enrichment e
JOIN job_postings j ON e.job_posting_id = j.id
JOIN companies c ON j.company_id = c.id
LEFT JOIN locations l ON l.id = COALESCE(j.location_id_override, j.location_id)
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN LATERAL (
    SELECT MIN(job_sources.first_seen_at) AS first_seen_at
    FROM job_sources
    WHERE job_sources.job_posting_id = j.id
) js ON TRUE
WHERE j.is_active = TRUE
  AND j.title_classification = 'Data'
  AND (cmd.show_in_app IS NULL OR cmd.show_in_app = TRUE);

COMMENT ON VIEW vw_job_listings IS 
'Frontend-friendly view for job listings with complete enrichment data.
Filters: is_active=TRUE, title_classification=Data, show_in_app=TRUE (or NULL).
Includes company_id, show_in_app, and multilingual spoken language names.
Updated: 2025-12-30 to add show_in_app filter';
