-- Migration 046: Add source column to scrape_runs
-- Date: 2025-11-16
-- Description: Add source column to track whether run was for LinkedIn or Indeed jobs

-- Add source column
ALTER TABLE scrape_runs
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'linkedin';

-- Add comment
COMMENT ON COLUMN scrape_runs.source IS 'Job source: linkedin or indeed';

-- Add check constraint for valid sources
ALTER TABLE scrape_runs
ADD CONSTRAINT check_scrape_run_source_values 
CHECK (source IN ('linkedin', 'indeed'));

-- Add index for source filtering
CREATE INDEX IF NOT EXISTS idx_scrape_runs_source ON scrape_runs(source);

-- Update existing runs to set source based on search_query_id if available
UPDATE scrape_runs sr
SET source = sq.source
FROM search_queries sq
WHERE sr.search_query_id = sq.id
  AND sr.source = 'linkedin';  -- Only update if still default

-- For runs without search_query_id, try to infer from metadata
UPDATE scrape_runs
SET source = 'indeed'
WHERE metadata->>'source' = 'indeed'
  AND source = 'linkedin';  -- Only update if still default
