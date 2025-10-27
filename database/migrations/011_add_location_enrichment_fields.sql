-- Migration: Add location enrichment fields
-- Add fields for LLM-enriched location data (multilingual, normalized, administrative)
-- Date: 2025-10-27

-- Add enrichment fields to locations table
ALTER TABLE locations
ADD COLUMN IF NOT EXISTS country_code_3 TEXT,
ADD COLUMN IF NOT EXISTS country_name TEXT,
ADD COLUMN IF NOT EXISTS subdivision_name TEXT,
ADD COLUMN IF NOT EXISTS timezone TEXT,
ADD COLUMN IF NOT EXISTS city_official_name TEXT,
ADD COLUMN IF NOT EXISTS city_normalized TEXT,
ADD COLUMN IF NOT EXISTS region_normalized TEXT,
ADD COLUMN IF NOT EXISTS country_normalized TEXT,
ADD COLUMN IF NOT EXISTS city_name_nl TEXT,
ADD COLUMN IF NOT EXISTS city_name_fr TEXT,
ADD COLUMN IF NOT EXISTS city_name_en TEXT,
ADD COLUMN IF NOT EXISTS country_name_nl TEXT,
ADD COLUMN IF NOT EXISTS country_name_fr TEXT,
ADD COLUMN IF NOT EXISTS country_name_en TEXT,
ADD COLUMN IF NOT EXISTS ai_enriched BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ai_enriched_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS ai_enrichment_error TEXT;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_locations_ai_enriched 
ON locations(ai_enriched) 
WHERE ai_enriched = TRUE;

CREATE INDEX IF NOT EXISTS idx_locations_country_code_3 
ON locations(country_code_3) 
WHERE country_code_3 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_locations_subdivision 
ON locations(subdivision_name) 
WHERE subdivision_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_locations_timezone 
ON locations(timezone) 
WHERE timezone IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_locations_city_normalized 
ON locations(city_normalized) 
WHERE city_normalized IS NOT NULL;

-- Add comments
COMMENT ON COLUMN locations.country_code_3 IS 'ISO 3166-1 alpha-3 country code (AI enriched)';
COMMENT ON COLUMN locations.country_name IS 'Country name in local official language (AI enriched)';
COMMENT ON COLUMN locations.subdivision_name IS 'Province/state/region (first-level admin division) (AI enriched)';
COMMENT ON COLUMN locations.timezone IS 'IANA timezone identifier (AI enriched)';
COMMENT ON COLUMN locations.city_official_name IS 'Official local spelling of city name (AI enriched)';
COMMENT ON COLUMN locations.city_normalized IS 'Normalized city name: lowercase, no accents, underscores (AI enriched)';
COMMENT ON COLUMN locations.region_normalized IS 'Normalized subdivision name (AI enriched)';
COMMENT ON COLUMN locations.country_normalized IS 'Normalized country name (AI enriched)';
COMMENT ON COLUMN locations.city_name_nl IS 'Dutch exonym for city, if established (AI enriched)';
COMMENT ON COLUMN locations.city_name_fr IS 'French exonym for city, if established (AI enriched)';
COMMENT ON COLUMN locations.city_name_en IS 'English exonym for city, if established (AI enriched)';
COMMENT ON COLUMN locations.country_name_nl IS 'Country name in Dutch (AI enriched)';
COMMENT ON COLUMN locations.country_name_fr IS 'Country name in French (AI enriched)';
COMMENT ON COLUMN locations.country_name_en IS 'Country name in English (AI enriched)';
COMMENT ON COLUMN locations.ai_enriched IS 'Whether location data has been enriched by AI';
COMMENT ON COLUMN locations.ai_enriched_at IS 'Timestamp when AI enrichment was performed';
COMMENT ON COLUMN locations.ai_enrichment_error IS 'Error message if AI enrichment failed';
