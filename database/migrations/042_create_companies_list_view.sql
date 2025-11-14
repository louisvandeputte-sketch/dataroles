-- Create a lightweight view for companies list interface
-- This combines companies and company_master_data with only essential fields
-- to reduce response size and improve loading speed

CREATE OR REPLACE VIEW companies_list_view AS
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
    cmd.sector_en,
    cmd.category_en,
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

-- Add comment
COMMENT ON VIEW companies_list_view IS 'Lightweight view for companies list interface with only essential fields to improve loading performance';
