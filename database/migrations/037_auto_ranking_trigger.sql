-- Migration 037: Auto-trigger ranking calculation for new jobs
-- Date: 2025-11-11
-- Description: Create a trigger that marks jobs for re-ranking when new jobs are added

-- 1. Add a flag to track if rankings need recalculation
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS needs_ranking BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN job_postings.needs_ranking IS 
'Flag indicating if this job needs to be included in next ranking calculation. Set to TRUE for new jobs or when job data changes.';

-- 2. Create function to mark jobs for re-ranking when new jobs are inserted
CREATE OR REPLACE FUNCTION mark_jobs_for_reranking()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark the new job for ranking
    NEW.needs_ranking := TRUE;
    
    -- Also mark all other active jobs for re-ranking (since rankings are relative)
    -- This ensures all positions are recalculated
    UPDATE job_postings 
    SET needs_ranking = TRUE 
    WHERE is_active = TRUE 
      AND id != NEW.id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Create trigger on INSERT
DROP TRIGGER IF EXISTS trigger_mark_for_reranking_on_insert ON job_postings;

CREATE TRIGGER trigger_mark_for_reranking_on_insert
    BEFORE INSERT ON job_postings
    FOR EACH ROW
    EXECUTE FUNCTION mark_jobs_for_reranking();

-- 4. Create trigger on UPDATE (when important fields change)
CREATE OR REPLACE FUNCTION mark_for_reranking_on_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Only trigger if important ranking fields changed
    IF (
        OLD.posted_date IS DISTINCT FROM NEW.posted_date OR
        OLD.is_active IS DISTINCT FROM NEW.is_active OR
        OLD.title IS DISTINCT FROM NEW.title OR
        OLD.company_id IS DISTINCT FROM NEW.company_id OR
        OLD.location_id IS DISTINCT FROM NEW.location_id
    ) THEN
        -- Mark this job for re-ranking
        NEW.needs_ranking := TRUE;
        
        -- Mark all active jobs for re-ranking
        UPDATE job_postings 
        SET needs_ranking = TRUE 
        WHERE is_active = TRUE 
          AND id != NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_mark_for_reranking_on_update ON job_postings;

CREATE TRIGGER trigger_mark_for_reranking_on_update
    BEFORE UPDATE ON job_postings
    FOR EACH ROW
    EXECUTE FUNCTION mark_for_reranking_on_update();

-- 5. Mark all existing jobs for initial ranking
UPDATE job_postings 
SET needs_ranking = TRUE 
WHERE is_active = TRUE;

-- 6. Create index for efficient querying of jobs that need ranking
CREATE INDEX IF NOT EXISTS idx_job_postings_needs_ranking 
ON job_postings(needs_ranking) 
WHERE needs_ranking = TRUE AND is_active = TRUE;

COMMENT ON INDEX idx_job_postings_needs_ranking IS 
'Index for efficiently finding jobs that need ranking calculation';

-- Summary
-- ✅ Added needs_ranking flag to track jobs requiring ranking
-- ✅ Trigger on INSERT marks new jobs and all active jobs for re-ranking
-- ✅ Trigger on UPDATE marks jobs when important fields change
-- ✅ All existing active jobs marked for initial ranking
-- ✅ Index created for efficient querying

-- Usage:
-- After running this migration, the ranking calculation script should:
-- 1. Query jobs WHERE needs_ranking = TRUE AND is_active = TRUE
-- 2. Calculate rankings for those jobs
-- 3. Set needs_ranking = FALSE after successful ranking
