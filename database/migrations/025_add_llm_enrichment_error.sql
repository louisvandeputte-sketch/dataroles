-- Migration: Add error tracking for LLM job enrichment
-- Date: 2025-11-07

-- Add error column to track enrichment failures
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS enrichment_error TEXT;

-- Add comment
COMMENT ON COLUMN llm_enrichment.enrichment_error IS 'Error message if LLM enrichment failed (e.g., OpenAI API error, parsing error, quota exceeded)';

-- Add index for filtering failed enrichments
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_error 
ON llm_enrichment(enrichment_error) 
WHERE enrichment_error IS NOT NULL;

-- Add index for finding jobs that need retry (failed but not completed)
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_needs_retry
ON llm_enrichment(enrichment_error, enrichment_completed_at)
WHERE enrichment_error IS NOT NULL AND enrichment_completed_at IS NULL;
