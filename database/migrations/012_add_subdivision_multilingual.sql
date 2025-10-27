-- Migration: Add multilingual subdivision names
-- Add French and English translations for subdivision names
-- Date: 2025-10-27

-- Add multilingual subdivision fields
ALTER TABLE locations
ADD COLUMN IF NOT EXISTS subdivision_name_fr TEXT,
ADD COLUMN IF NOT EXISTS subdivision_name_en TEXT;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_locations_subdivision_fr 
ON locations(subdivision_name_fr) 
WHERE subdivision_name_fr IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_locations_subdivision_en 
ON locations(subdivision_name_en) 
WHERE subdivision_name_en IS NOT NULL;

-- Add comments
COMMENT ON COLUMN locations.subdivision_name_fr IS 'Province/state/region name in French (AI enriched)';
COMMENT ON COLUMN locations.subdivision_name_en IS 'Province/state/region name in English (AI enriched)';
