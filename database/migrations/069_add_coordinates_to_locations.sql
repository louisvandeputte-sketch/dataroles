-- Migration 069: Add geographic coordinates to locations
-- Date: 2025-11-28
-- Description: Add longitude and latitude columns for geocoding support

-- Add coordinate columns
ALTER TABLE locations
ADD COLUMN IF NOT EXISTS longitude DECIMAL(10, 7),
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 7),
ADD COLUMN IF NOT EXISTS coordinates_enriched BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS coordinates_enriched_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for spatial queries
CREATE INDEX IF NOT EXISTS idx_locations_longitude 
ON locations(longitude) 
WHERE longitude IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_locations_latitude 
ON locations(latitude) 
WHERE latitude IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_locations_coordinates_enriched 
ON locations(coordinates_enriched) 
WHERE coordinates_enriched = TRUE;

-- Add composite index for both coordinates (useful for proximity searches)
CREATE INDEX IF NOT EXISTS idx_locations_coordinates 
ON locations(latitude, longitude) 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Add comments
COMMENT ON COLUMN locations.longitude IS 'Geographic longitude coordinate (WGS84), range: -180 to 180';
COMMENT ON COLUMN locations.latitude IS 'Geographic latitude coordinate (WGS84), range: -90 to 90';
COMMENT ON COLUMN locations.coordinates_enriched IS 'Whether coordinates have been enriched via geocoding API';
COMMENT ON COLUMN locations.coordinates_enriched_at IS 'Timestamp when coordinates were enriched';

-- Add constraint to ensure valid coordinate ranges
ALTER TABLE locations
ADD CONSTRAINT check_longitude_range 
CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180));

ALTER TABLE locations
ADD CONSTRAINT check_latitude_range 
CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90));
