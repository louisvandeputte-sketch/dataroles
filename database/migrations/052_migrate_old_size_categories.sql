-- Migration 052: Migrate old size_category values to new enum values
-- Date: 2025-11-18
-- Description: Map deprecated categories to new canonical values

-- Update old category values to new enum values
UPDATE company_master_data
SET size_category = 'established_enterprise'
WHERE size_category IN ('Midmarket', 'Subsidiary', 'midmarket', 'subsidiary');

-- Update Scaleup to scaleup (lowercase)
UPDATE company_master_data
SET size_category = 'scaleup'
WHERE size_category = 'Scaleup';

-- Log the changes
DO $$
DECLARE
    midmarket_count INT;
    subsidiary_count INT;
    scaleup_count INT;
BEGIN
    SELECT COUNT(*) INTO midmarket_count FROM company_master_data WHERE size_category = 'established_enterprise' AND (category_en = 'Midmarket' OR category_nl = 'Middelgroot Bedrijf');
    SELECT COUNT(*) INTO subsidiary_count FROM company_master_data WHERE size_category = 'established_enterprise' AND (category_en = 'Subsidiary' OR category_nl = 'Dochteronderneming');
    SELECT COUNT(*) INTO scaleup_count FROM company_master_data WHERE size_category = 'scaleup';
    
    RAISE NOTICE 'Migration complete:';
    RAISE NOTICE '  - Migrated % Midmarket → established_enterprise', midmarket_count;
    RAISE NOTICE '  - Migrated % Subsidiary → established_enterprise', subsidiary_count;
    RAISE NOTICE '  - Fixed % Scaleup → scaleup', scaleup_count;
END $$;

-- Add comment
COMMENT ON TABLE company_master_data IS 
'Company master data with enrichment. 
Migration 052: Deprecated categories (Midmarket, Subsidiary) mapped to established_enterprise.
Scaleup normalized to lowercase scaleup.';
