-- Migration: Make linkedin_job_id nullable for Indeed jobs
-- Date: 2025-11-10

-- Drop the NOT NULL constraint on linkedin_job_id
-- This allows Indeed jobs to have NULL linkedin_job_id
ALTER TABLE job_postings
ALTER COLUMN linkedin_job_id DROP NOT NULL;

-- The check constraint from 027 ensures that either linkedin_job_id or indeed_job_id is set
-- (source = 'linkedin' AND linkedin_job_id IS NOT NULL) OR
-- (source = 'indeed' AND indeed_job_id IS NOT NULL)

COMMENT ON COLUMN job_postings.linkedin_job_id IS 'LinkedIn job ID (NULL for Indeed jobs)';
