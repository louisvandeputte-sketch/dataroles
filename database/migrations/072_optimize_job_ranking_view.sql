-- Migration 072: Optimize job_ranking_view by using posted_date_corrected from job_postings
-- Date: 2025-11-28
-- Description: Remove slow LATERAL join and use posted_date_corrected directly from job_postings table

DROP VIEW IF EXISTS job_ranking_view;

CREATE OR REPLACE VIEW job_ranking_view AS
SELECT 
    -- Job posting fields (verified from job_postings table)
    jp.id,
    jp.title,
    jp.company_id,
    jp.location_id,
    jp.posted_date,
    jp.posted_date_corrected,  -- Now directly from job_postings (migration 071)
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

-- Add comment
COMMENT ON VIEW job_ranking_view IS 'Optimized denormalized view for job ranking. Uses posted_date_corrected directly from job_postings table (no LATERAL join needed). Much faster query performance.';
