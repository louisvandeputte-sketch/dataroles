-- Migration 081: Add time_ago columns to vw_job_listings (NL, FR, EN)
-- Date: 2025-12-15
-- Description: Add multilingual time indicator columns based on posted_date_corrected
--              Jobs < 7 days: "Nieuw" / "Nouveau" / "New"
--              Jobs >= 7 days: "X dagen geleden" / "il y a X jours" / "X days ago", etc.

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
  AND j.title_classification = 'Data';

COMMENT ON VIEW vw_job_listings IS 
'Frontend-friendly view for job listings with complete enrichment data.
Includes multilingual spoken language names and time_ago columns in NL/FR/EN.
time_ago logic:
  - < 7 days: "Nieuw" / "Nouveau" / "New"
  - 7-13 days: "X dagen geleden" / "il y a X jours" / "X days ago"
  - 14-29 days: "X weken geleden" / "il y a X semaines" / "X weeks ago"
  - 30+ days: "meer dan 1 maand geleden" / "il y a plus d''un mois" / "more than 1 month ago"
Updated: 2025-12-15 to add time_ago_nl, time_ago_fr, time_ago_en columns';
