-- Migration 063: Add base_score column for stable daily score
-- Date: 2025-11-21
-- Description: Separate base_score (calculated nightly) from ranking_score (hourly with multiplier)
--              base_score = stable score from algorithm (recalculated nightly)
--              ranking_score = base_score × hourly_multiplier (recalculated hourly)

-- Add base_score column to job_postings
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS base_score NUMERIC(10, 2);

-- Add comment
COMMENT ON COLUMN job_postings.base_score IS 'Base ranking score calculated by algorithm (0-100). Stable, recalculated nightly. ranking_score = base_score × hourly_multiplier.';

-- Update existing comment for ranking_score to clarify it includes multiplier
COMMENT ON COLUMN job_postings.ranking_score IS 'Final ranking score (0-100) = base_score × hourly_multiplier. Recalculated every hour.';

-- Add index for filtering/sorting by base_score
CREATE INDEX IF NOT EXISTS idx_job_postings_base_score 
ON job_postings(base_score DESC NULLS LAST) 
WHERE is_active = true;
