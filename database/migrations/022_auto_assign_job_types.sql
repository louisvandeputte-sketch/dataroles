-- Migration: Auto-assign job types via trigger
-- Ensures every job gets a type assignment automatically
-- Date: 2025-11-02

-- Create function to auto-assign job type when a job is added to scrape history
CREATE OR REPLACE FUNCTION auto_assign_job_type()
RETURNS TRIGGER AS $$
DECLARE
    v_job_type_id UUID;
BEGIN
    -- Check if job already has an assignment
    IF EXISTS (
        SELECT 1 FROM job_type_assignments 
        WHERE job_posting_id = NEW.job_posting_id
    ) THEN
        RETURN NEW;
    END IF;
    
    -- Get job_type_id from the scrape_run
    SELECT job_type_id INTO v_job_type_id
    FROM scrape_runs
    WHERE id = NEW.scrape_run_id;
    
    -- If scrape_run has a job_type_id, create assignment
    IF v_job_type_id IS NOT NULL THEN
        INSERT INTO job_type_assignments (job_posting_id, job_type_id, assigned_via)
        VALUES (NEW.job_posting_id, v_job_type_id, 'trigger')
        ON CONFLICT (job_posting_id, job_type_id) DO NOTHING;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on job_scrape_history
DROP TRIGGER IF EXISTS trigger_auto_assign_job_type ON job_scrape_history;
CREATE TRIGGER trigger_auto_assign_job_type
    AFTER INSERT ON job_scrape_history
    FOR EACH ROW
    EXECUTE FUNCTION auto_assign_job_type();

-- Add comment
COMMENT ON FUNCTION auto_assign_job_type() IS 'Automatically assigns job type to jobs when they are added to scrape history';
COMMENT ON TRIGGER trigger_auto_assign_job_type ON job_scrape_history IS 'Ensures every job gets a type assignment from its scrape_run';
