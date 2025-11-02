-- Migration: Add job title classification field
-- Pre-screens job titles to determine if they are data-related
-- Date: 2025-11-02

-- Add classification column to job_postings
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS title_classification TEXT CHECK (title_classification IN ('Data', 'NIS', NULL)),
ADD COLUMN IF NOT EXISTS title_classification_at TIMESTAMPTZ;

-- Add index for filtering
CREATE INDEX IF NOT EXISTS idx_job_postings_title_classification 
ON job_postings(title_classification) 
WHERE title_classification IS NOT NULL;

-- Add comments
COMMENT ON COLUMN job_postings.title_classification IS 'LLM classification of job title: "Data" (data-related) or "NIS" (not data-related)';
COMMENT ON COLUMN job_postings.title_classification_at IS 'Timestamp when title was classified';
