-- Migration 062: Add hourly_multiplier to job_postings
-- Date: 2025-11-21
-- Description: Store the hourly random multiplier (0.8-1.2) that is applied to job scores
--              This multiplier changes every hour to create dynamic rankings

-- Add hourly_multiplier column to job_postings
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS hourly_multiplier DECIMAL(4,3);

-- Add comment
COMMENT ON COLUMN job_postings.hourly_multiplier IS 'Hourly random multiplier (0.8-1.2) applied to base score. Changes every hour based on MD5 hash of date-hour + job_id. Creates ±20% variation in rankings.';

-- Add index for filtering/sorting by multiplier
CREATE INDEX IF NOT EXISTS idx_job_postings_hourly_multiplier 
ON job_postings(hourly_multiplier) 
WHERE is_active = true;
