-- Migration 071: Add posted_date_corrected as generated column to job_postings
-- Date: 2025-11-28
-- Description: Add computed column that shows minimum of first_seen_at and posted_date

-- Add posted_date_corrected as a generated column
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS posted_date_corrected TIMESTAMP WITH TIME ZONE
GENERATED ALWAYS AS (
    LEAST(
        (SELECT MIN(first_seen_at) FROM job_sources WHERE job_posting_id = job_postings.id),
        posted_date
    )
) STORED;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_job_postings_posted_date_corrected 
ON job_postings(posted_date_corrected) 
WHERE posted_date_corrected IS NOT NULL;

-- Add comment
COMMENT ON COLUMN job_postings.posted_date_corrected IS 'Corrected posted date: minimum of first_seen_at (from job_sources) and posted_date. This represents the true age of the job, accounting for re-posts.';
