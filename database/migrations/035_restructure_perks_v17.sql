-- Migration 035: Restructure perks from JSONB array to individual columns (v17)
-- Date: 2025-11-11
-- Description: Replace perks JSONB array with 6 individual perk columns for better performance and simpler queries

-- 1. Rename old perks column (preserve data for backward compatibility)
ALTER TABLE llm_enrichment 
RENAME COLUMN perks TO perks_OLD_deprecated;

-- Update comment on old column
COMMENT ON COLUMN llm_enrichment.perks_OLD_deprecated IS 
'DEPRECATED (v17): Old JSONB perks array format. Replaced by 6 individual perk_* columns. Kept for backward compatibility and potential data migration. Will be removed in future version.';

-- 2. Add 6 new individual perk columns
ALTER TABLE llm_enrichment
ADD COLUMN perk_remote_policy VARCHAR(20) NULL,
ADD COLUMN perk_salary_range VARCHAR(50) NULL,
ADD COLUMN perk_company_car VARCHAR(20) NULL,
ADD COLUMN perk_hospitalization_insurance VARCHAR(30) NULL,
ADD COLUMN perk_training_budget VARCHAR(20) NULL,
ADD COLUMN perk_team_events VARCHAR(20) NULL;

-- 3. Add comments for new columns
COMMENT ON COLUMN llm_enrichment.perk_remote_policy IS 
'ACTIVE (v17): Remote work perk. Values: "Remote", "Hybrid", or NULL. Translated labels in labels.*.perk_remote_policy';

COMMENT ON COLUMN llm_enrichment.perk_salary_range IS 
'ACTIVE (v17): Salary range if mentioned. Format: "€x-€y/month" or "€x-€y/year" or NULL. Translated labels in labels.*.perk_salary_range';

COMMENT ON COLUMN llm_enrichment.perk_company_car IS 
'ACTIVE (v17): Company car benefit. Values: "Company car" or NULL. Translated labels in labels.*.perk_company_car';

COMMENT ON COLUMN llm_enrichment.perk_hospitalization_insurance IS 
'ACTIVE (v17): Health/hospitalization insurance benefit. Values: "Health insurance" or NULL. Translated labels in labels.*.perk_hospitalization_insurance';

COMMENT ON COLUMN llm_enrichment.perk_training_budget IS 
'ACTIVE (v17): Training/learning budget benefit. Values: "Training budget" or NULL. Translated labels in labels.*.perk_training_budget';

COMMENT ON COLUMN llm_enrichment.perk_team_events IS 
'ACTIVE (v17): Team events/activities benefit. Values: "Team events" or NULL. Translated labels in labels.*.perk_team_events';

-- 4. Create indexes for filtering on perks
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perk_remote 
ON llm_enrichment(perk_remote_policy) WHERE perk_remote_policy IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perk_salary 
ON llm_enrichment(perk_salary_range) WHERE perk_salary_range IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perk_car 
ON llm_enrichment(perk_company_car) WHERE perk_company_car IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perk_insurance 
ON llm_enrichment(perk_hospitalization_insurance) WHERE perk_hospitalization_insurance IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perk_training 
ON llm_enrichment(perk_training_budget) WHERE perk_training_budget IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perk_events 
ON llm_enrichment(perk_team_events) WHERE perk_team_events IS NOT NULL;

-- 5. Update llm_enrichment_active view to include new perk columns
DROP VIEW IF EXISTS llm_enrichment_active;

CREATE OR REPLACE VIEW llm_enrichment_active AS
SELECT 
    job_posting_id,
    
    -- Active multilingual fields
    labels,
    
    -- Active perks (v17 individual columns)
    perk_remote_policy,
    perk_salary_range,
    perk_company_car,
    perk_hospitalization_insurance,
    perk_training_budget,
    perk_team_events,
    
    -- Active summaries (3 languages)
    samenvatting_kort_en,
    samenvatting_lang_en,
    samenvatting_kort_nl,
    samenvatting_lang_nl,
    samenvatting_kort_fr,
    samenvatting_lang_fr,
    
    -- Active tech stack fields
    must_have_programmeertalen,
    nice_to_have_programmeertalen,
    must_have_ecosystemen,
    nice_to_have_ecosystemen,
    
    -- Active language fields
    must_have_talen,
    nice_to_have_talen,
    
    -- Active policy field
    remote_work_policy,
    
    -- Metadata
    enrichment_completed_at,
    enrichment_error,
    enrichment_model_version,
    created_at
FROM llm_enrichment;

COMMENT ON VIEW llm_enrichment_active IS 
'View of llm_enrichment showing only active (non-deprecated) fields. Updated for v17 with individual perk columns. Frontend developers should query this view instead of the full table.';

-- 6. Summary of changes
-- ✅ Old perks JSONB column renamed to perks_OLD_deprecated
-- ✅ 6 new perk_* columns added (VARCHAR with NULL support)
-- ✅ Indexes created for efficient perk filtering
-- ✅ llm_enrichment_active view updated
-- ✅ All perk labels (NL/EN/FR) remain in labels JSONB column
-- ✅ Backward compatible: old column preserved
