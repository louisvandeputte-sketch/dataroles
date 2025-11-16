-- Migration 045: Add subdivision_name_nl to locations
-- Date: 2025-11-16
-- Description: Add Dutch translation for subdivision names (was missing from migration 012)

-- Add subdivision_name_nl field
ALTER TABLE locations
ADD COLUMN IF NOT EXISTS subdivision_name_nl TEXT;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_locations_subdivision_nl 
ON locations(subdivision_name_nl) 
WHERE subdivision_name_nl IS NOT NULL;

-- Add comment
COMMENT ON COLUMN locations.subdivision_name_nl IS 'Province/state/region name in Dutch (AI enriched)';
