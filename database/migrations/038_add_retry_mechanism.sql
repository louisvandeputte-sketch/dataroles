-- Migration: Add retry mechanism for stuck scrape runs
-- Date: 2025-11-12

-- Add retry tracking columns to scrape_runs
ALTER TABLE scrape_runs
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 4,
ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS original_run_id UUID,
ADD COLUMN IF NOT EXISTS is_retry BOOLEAN DEFAULT FALSE;

-- Add index for finding runs that need retry
CREATE INDEX IF NOT EXISTS idx_scrape_runs_next_retry 
ON scrape_runs(next_retry_at) 
WHERE next_retry_at IS NOT NULL AND status = 'pending_retry';

-- Add comments
COMMENT ON COLUMN scrape_runs.retry_count IS 'Number of times this run has been retried (0 = first attempt)';
COMMENT ON COLUMN scrape_runs.max_retries IS 'Maximum number of retry attempts allowed (default 4)';
COMMENT ON COLUMN scrape_runs.next_retry_at IS 'Timestamp when this run should be retried (NULL if no retry scheduled)';
COMMENT ON COLUMN scrape_runs.original_run_id IS 'ID of the original run if this is a retry';
COMMENT ON COLUMN scrape_runs.is_retry IS 'True if this run is a retry of a previous failed run';
