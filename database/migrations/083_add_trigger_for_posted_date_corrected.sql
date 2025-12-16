-- Migration 083: Add trigger to automatically update posted_date_corrected
-- Date: 2025-12-16
-- Description: Create trigger that automatically updates posted_date_corrected when:
--              1. A new job_sources record is inserted (with first_seen_at)
--              2. A job_postings record is updated with a new posted_date
--              This ensures posted_date_corrected is ALWAYS up-to-date

-- Function to update posted_date_corrected for a job
CREATE OR REPLACE FUNCTION update_posted_date_corrected()
RETURNS TRIGGER AS $$
DECLARE
    v_job_id UUID;
    v_posted_date TIMESTAMPTZ;
    v_first_seen_at TIMESTAMPTZ;
    v_corrected_date TIMESTAMPTZ;
BEGIN
    -- Determine job_id based on which table triggered this
    IF TG_TABLE_NAME = 'job_sources' THEN
        v_job_id := NEW.job_posting_id;
    ELSIF TG_TABLE_NAME = 'job_postings' THEN
        v_job_id := NEW.id;
    END IF;
    
    -- Get posted_date from job_postings
    SELECT posted_date INTO v_posted_date
    FROM job_postings
    WHERE id = v_job_id;
    
    -- Get minimum first_seen_at from job_sources
    SELECT MIN(first_seen_at) INTO v_first_seen_at
    FROM job_sources
    WHERE job_posting_id = v_job_id;
    
    -- Calculate corrected date using COALESCE to handle NULLs
    -- If both exist: use minimum
    -- If only one exists: use that one
    -- If neither exists: NULL
    v_corrected_date := LEAST(
        COALESCE(v_first_seen_at, v_posted_date),
        COALESCE(v_posted_date, v_first_seen_at)
    );
    
    -- Update job_postings with corrected date
    UPDATE job_postings
    SET posted_date_corrected = v_corrected_date
    WHERE id = v_job_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on job_sources INSERT
-- When a new source is added, recalculate posted_date_corrected
DROP TRIGGER IF EXISTS trigger_update_posted_date_corrected_on_source_insert ON job_sources;
CREATE TRIGGER trigger_update_posted_date_corrected_on_source_insert
    AFTER INSERT ON job_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_posted_date_corrected();

-- Trigger on job_postings INSERT
-- When a new job is created, set initial posted_date_corrected
DROP TRIGGER IF EXISTS trigger_update_posted_date_corrected_on_job_insert ON job_postings;
CREATE TRIGGER trigger_update_posted_date_corrected_on_job_insert
    AFTER INSERT ON job_postings
    FOR EACH ROW
    EXECUTE FUNCTION update_posted_date_corrected();

-- Trigger on job_postings UPDATE (when posted_date changes)
-- When posted_date is updated, recalculate posted_date_corrected
DROP TRIGGER IF EXISTS trigger_update_posted_date_corrected_on_job_update ON job_postings;
CREATE TRIGGER trigger_update_posted_date_corrected_on_job_update
    AFTER UPDATE OF posted_date ON job_postings
    FOR EACH ROW
    WHEN (OLD.posted_date IS DISTINCT FROM NEW.posted_date)
    EXECUTE FUNCTION update_posted_date_corrected();

-- Add comments
COMMENT ON FUNCTION update_posted_date_corrected() IS 'Automatically calculates and updates posted_date_corrected as minimum of first_seen_at and posted_date, with NULL handling';
COMMENT ON TRIGGER trigger_update_posted_date_corrected_on_source_insert ON job_sources IS 'Updates posted_date_corrected when new job_sources record is added';
COMMENT ON TRIGGER trigger_update_posted_date_corrected_on_job_insert ON job_postings IS 'Sets initial posted_date_corrected when new job is created';
COMMENT ON TRIGGER trigger_update_posted_date_corrected_on_job_update ON job_postings IS 'Recalculates posted_date_corrected when posted_date is updated';

-- Verify trigger creation
DO $$
BEGIN
    RAISE NOTICE 'Migration 083 complete: Triggers created for automatic posted_date_corrected updates';
    RAISE NOTICE '  - trigger_update_posted_date_corrected_on_source_insert';
    RAISE NOTICE '  - trigger_update_posted_date_corrected_on_job_insert';
    RAISE NOTICE '  - trigger_update_posted_date_corrected_on_job_update';
    RAISE NOTICE '';
    RAISE NOTICE 'From now on, posted_date_corrected will be AUTOMATICALLY updated for:';
    RAISE NOTICE '  1. New jobs (uses posted_date initially)';
    RAISE NOTICE '  2. New job_sources records (recalculates with first_seen_at)';
    RAISE NOTICE '  3. Updated posted_date values (recalculates)';
END $$;
