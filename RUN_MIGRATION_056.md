# Migration 056: Add Relevantie & Show in App Columns to Companies

## Run deze SQL in Supabase SQL Editor

Ga naar: https://supabase.com/dashboard → SQL Editor → New Query

```sql
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
```

## Verification

Na het uitvoeren van de migratie, verifieer met:

```sql
-- Check if new columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'company_master_data' 
  AND column_name IN ('relevantie', 'show_in_app');

-- Check if view includes new columns
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'companies_list_view' 
  AND column_name IN ('relevantie', 'show_in_app');
```

## What changed

1. **New columns** added to `company_master_data`:
   - `relevantie` (INTEGER) - manual relevance score
   - `show_in_app` (BOOLEAN, default: true) - visibility flag
2. **Updated views**:
   - `companies_list_view` - includes both columns for UI
   - `job_ranking_view` - includes both columns for ranking logic
3. **UI**: `/companies` page now shows:
   - Narrower company name column
   - **Show** column with eye icon toggle (green=visible, red=hidden)
   - **Relevantie** column (editable number)
4. **API**: Companies API now returns `relevantie` and `show_in_app` in response

## Usage

- **Show in App**: Click the eye icon to toggle visibility (default: visible/green)
- **Relevantie**: Click on the cell to edit, enter any integer, press Enter to save
