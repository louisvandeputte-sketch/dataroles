-- Migration: Add error tracking for job title classification
-- Date: 2025-11-07

-- Add error column to track classification failures
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS title_classification_error TEXT;

-- Add comment
COMMENT ON COLUMN job_postings.title_classification_error IS 'Error message if title classification failed (e.g., OpenAI API quota exceeded)';

-- Add index for filtering failed classifications
CREATE INDEX IF NOT EXISTS idx_job_postings_title_classification_error 
ON job_postings(title_classification_error) 
WHERE title_classification_error IS NOT NULL;
