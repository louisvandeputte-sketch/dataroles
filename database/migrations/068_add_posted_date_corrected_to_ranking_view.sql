-- Migration 068: Add posted_date_corrected to job_ranking_view
-- Date: 2025-11-28
-- Description: Add posted_date_corrected (minimum of first_seen_at and posted_date) for accurate freshness scoring

DROP VIEW IF EXISTS job_ranking_view;

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
    
    -- Corrected posted date (minimum of first_seen_at and posted_date)
    LEAST(js.first_seen_at, jp.posted_date) AS posted_date_corrected,
    
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
LEFT JOIN LATERAL (
    -- Get earliest first_seen_at from all sources for this job
    SELECT MIN(first_seen_at) as first_seen_at
    FROM job_sources
    WHERE job_posting_id = jp.id
) js ON true
WHERE jp.is_active = true;

-- Add comment
COMMENT ON VIEW job_ranking_view IS 'Denormalized view for job ranking with all necessary joins pre-computed. Includes all active jobs (Data, NIS, Other) for ranking. NIS jobs will be assigned rank 999999. posted_date_corrected provides accurate job age by taking minimum of first_seen_at and posted_date.';
