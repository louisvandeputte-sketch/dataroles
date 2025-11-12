-- Migration 040: Set default high rank for new jobs
-- New jobs get rank 999999 until properly ranked
-- This ensures they appear at bottom until enriched and ranked

-- Set default ranking_position for new jobs
ALTER TABLE job_postings 
ALTER COLUMN ranking_position SET DEFAULT 999999;

-- Set default needs_ranking to TRUE for new jobs
ALTER TABLE job_postings 
ALTER COLUMN needs_ranking SET DEFAULT TRUE;

-- Update existing jobs without ranking to high rank
UPDATE job_postings
SET ranking_position = 999999
WHERE ranking_position IS NULL
AND is_active = TRUE;

-- Mark all jobs without ranking for re-ranking
UPDATE job_postings
SET needs_ranking = TRUE
WHERE ranking_position IS NULL OR ranking_position = 999999
AND is_active = TRUE;

COMMENT ON COLUMN job_postings.ranking_position IS 'Job ranking position (lower = better). Default 999999 for new/unenriched jobs.';
COMMENT ON COLUMN job_postings.needs_ranking IS 'TRUE if job needs ranking calculation. Auto-set after enrichment.';
