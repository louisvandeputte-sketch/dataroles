-- Migration: Add source column to search_queries
-- Date: 2025-11-10

-- Add source column to track query source (linkedin or indeed)
ALTER TABLE search_queries
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'linkedin';

-- Add comment
COMMENT ON COLUMN search_queries.source IS 'Job source: linkedin or indeed';

-- Add check constraint for valid sources
ALTER TABLE search_queries
ADD CONSTRAINT check_search_query_source_values 
CHECK (source IN ('linkedin', 'indeed'));

-- Update unique constraint to include source
-- Drop old constraint
ALTER TABLE search_queries
DROP CONSTRAINT IF EXISTS search_queries_search_query_location_query_key;

-- Add new constraint with source
ALTER TABLE search_queries
ADD CONSTRAINT search_queries_search_query_location_query_source_key
UNIQUE(search_query, location_query, source);

-- Add index for source filtering
CREATE INDEX IF NOT EXISTS idx_search_queries_source ON search_queries(source);
