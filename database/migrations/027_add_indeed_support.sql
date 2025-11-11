-- Migration: Add Indeed support to job_postings
-- Date: 2025-11-10

-- Add source column to track job origin (linkedin or indeed)
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'linkedin',
ADD COLUMN IF NOT EXISTS indeed_job_id TEXT;

-- Add comment
COMMENT ON COLUMN job_postings.source IS 'Job source: linkedin or indeed';
COMMENT ON COLUMN job_postings.indeed_job_id IS 'Indeed job ID (jobid from Indeed API)';

-- Add unique constraint for indeed_job_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_job_indeed_id 
ON job_postings(indeed_job_id) 
WHERE indeed_job_id IS NOT NULL;

-- Add index for source filtering
CREATE INDEX IF NOT EXISTS idx_job_source ON job_postings(source);

-- Add check constraint for valid sources
ALTER TABLE job_postings
ADD CONSTRAINT check_job_source_values 
CHECK (source IN ('linkedin', 'indeed'));

-- Ensure either linkedin_job_id or indeed_job_id is set
ALTER TABLE job_postings
ADD CONSTRAINT check_job_has_source_id
CHECK (
    (source = 'linkedin' AND linkedin_job_id IS NOT NULL) OR
    (source = 'indeed' AND indeed_job_id IS NOT NULL)
);

-- Add company rating fields (Indeed provides these)
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS rating DECIMAL(2,1),
ADD COLUMN IF NOT EXISTS reviews_count INTEGER,
ADD COLUMN IF NOT EXISTS indeed_company_url TEXT;

COMMENT ON COLUMN companies.rating IS 'Company rating (e.g., 4.9 from Indeed)';
COMMENT ON COLUMN companies.reviews_count IS 'Number of company reviews';
COMMENT ON COLUMN companies.indeed_company_url IS 'Indeed company page URL';
