-- Migration 086: Update public_company translation to shorter version
-- Date: 2025-12-22
-- Description: Update existing records with 'Beursgenoteerd Bedrijf' to 'Beursgenoteerd'

-- Update existing records that have the old translation
UPDATE company_master_data
SET category_nl = 'Beursgenoteerd'
WHERE size_category = 'public_company'
  AND category_nl = 'Beursgenoteerd Bedrijf';

-- Log the update
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated % company records with new public_company translation', updated_count;
END $$;
