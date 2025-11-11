-- Migration: Add ranking score to job_postings
-- Date: 2025-11-10
-- Purpose: Add ranking score and metadata for job ranking system

-- Add ranking columns to job_postings
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS ranking_score NUMERIC(10, 2),
ADD COLUMN IF NOT EXISTS ranking_position INTEGER,
ADD COLUMN IF NOT EXISTS ranking_updated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS ranking_metadata JSONB;

-- Create index on ranking_score for fast sorting
CREATE INDEX IF NOT EXISTS idx_job_postings_ranking_score 
ON job_postings(ranking_score DESC NULLS LAST) 
WHERE is_active = true;

-- Create index on ranking_position
CREATE INDEX IF NOT EXISTS idx_job_postings_ranking_position 
ON job_postings(ranking_position ASC NULLS LAST) 
WHERE is_active = true;

-- Comments
COMMENT ON COLUMN job_postings.ranking_score IS 'Calculated ranking score (0-100) based on multiple factors';
COMMENT ON COLUMN job_postings.ranking_position IS 'Final ranking position (1 = best)';
COMMENT ON COLUMN job_postings.ranking_updated_at IS 'When ranking was last calculated';
COMMENT ON COLUMN job_postings.ranking_metadata IS 'JSON with score breakdown (freshness_score, quality_score, etc.)';
