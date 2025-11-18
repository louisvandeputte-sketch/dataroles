-- Migration 053: Add size_category and category translations to companies_list_view
-- Date: 2025-11-18
-- Description: Add size_category (canonical) and all category translations to companies list view

-- Drop the view first to avoid column order issues
DROP VIEW IF EXISTS companies_list_view;

-- Recreate with size_category and all category translations
CREATE VIEW companies_list_view AS
SELECT 
    -- Company basic fields
    c.id,
    c.name,
    c.logo_url,
    c.industry,
    c.linkedin_company_id,
    
    -- Master data essential fields only
    cmd.id as master_data_id,
    cmd.hiring_model,
    cmd.is_consulting,
    cmd.sector_nl,
    cmd.sector_en,
    cmd.sector_fr,
    cmd.size_category,        -- Canonical category field
    cmd.category_nl,          -- Dutch translation
    cmd.category_en,          -- English translation
    cmd.category_fr,          -- French translation
    cmd.aantal_werknemers,
    cmd.bedrijfswebsite,
    cmd.jobspagina,
    cmd.email_hr,
    cmd.ai_enriched,
    cmd.ai_enriched_at,
    
    -- Job count (computed)
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id) as job_count,
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id AND jp.is_active = true) as active_job_count
    
FROM companies c
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
ORDER BY c.name;

-- Update comment
COMMENT ON VIEW companies_list_view IS 'Lightweight view for companies list interface with multilingual fields (sectors and categories in NL/EN/FR) and essential company data. size_category is the canonical field, category_nl/en/fr are auto-generated translations.';
