-- Migration 071: Add posted_date_corrected to job_postings
-- Date: 2025-11-28
-- Description: Add column for corrected posted date (minimum of first_seen_at and posted_date)
--              Frontend displays both dates in same column when they differ

-- Add posted_date_corrected column
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS posted_date_corrected TIMESTAMP WITH TIME ZONE;

-- Populate posted_date_corrected with minimum of first_seen_at and posted_date
UPDATE job_postings jp
SET posted_date_corrected = LEAST(
    COALESCE(
        (SELECT MIN(first_seen_at) 
         FROM job_sources 
         WHERE job_posting_id = jp.id),
        jp.posted_date
    ),
    jp.posted_date
);

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_job_postings_posted_date_corrected 
ON job_postings(posted_date_corrected) 
WHERE posted_date_corrected IS NOT NULL;

-- Add comment
COMMENT ON COLUMN job_postings.posted_date_corrected IS 'Corrected posted date: minimum of first_seen_at (from job_sources) and posted_date. Displayed in frontend below posted_date in orange when different.';
