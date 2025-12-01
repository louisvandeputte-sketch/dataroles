-- Migration: Create job_verification_runs table
-- Purpose: Track job verification runs and their statistics

CREATE TABLE IF NOT EXISTS job_verification_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL CHECK (source IN ('linkedin', 'indeed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    
    -- Statistics
    jobs_checked INTEGER DEFAULT 0,
    jobs_still_active INTEGER DEFAULT 0,
    jobs_marked_inactive INTEGER DEFAULT 0,
    jobs_errors INTEGER DEFAULT 0,
    
    -- Configuration
    batch_size INTEGER DEFAULT 100,
    only_data_jobs BOOLEAN DEFAULT true,
    
    -- Error details
    error_message TEXT,
    
    -- Metadata
    trigger_type TEXT DEFAULT 'scheduled' CHECK (trigger_type IN ('scheduled', 'manual')),
    metadata JSONB,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create table for tracking individual jobs marked inactive in each run
CREATE TABLE IF NOT EXISTS job_verification_inactive_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_run_id UUID NOT NULL REFERENCES job_verification_runs(id) ON DELETE CASCADE,
    job_posting_id UUID NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    
    -- Job details at time of marking inactive
    job_title TEXT,
    company_name TEXT,
    source TEXT,
    url TEXT,
    reason TEXT, -- 'not_found', 'no_title', 'api_error'
    
    marked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(verification_run_id, job_posting_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_verification_runs_source_started 
    ON job_verification_runs(source, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_verification_runs_status 
    ON job_verification_runs(status);

CREATE INDEX IF NOT EXISTS idx_verification_inactive_jobs_run 
    ON job_verification_inactive_jobs(verification_run_id);

CREATE INDEX IF NOT EXISTS idx_verification_inactive_jobs_job 
    ON job_verification_inactive_jobs(job_posting_id);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_verification_runs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_verification_runs_updated_at
    BEFORE UPDATE ON job_verification_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_verification_runs_updated_at();

-- Comments
COMMENT ON TABLE job_verification_runs IS 'Tracks job verification runs that check if jobs still exist on LinkedIn/Indeed';
COMMENT ON TABLE job_verification_inactive_jobs IS 'Records which jobs were marked inactive in each verification run';
COMMENT ON COLUMN job_verification_runs.source IS 'Source platform: linkedin or indeed';
COMMENT ON COLUMN job_verification_runs.trigger_type IS 'How the run was triggered: scheduled or manual';
COMMENT ON COLUMN job_verification_inactive_jobs.reason IS 'Why the job was marked inactive: not_found, no_title, or api_error';
