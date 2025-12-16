-- Migration 082: Populate missing posted_date_corrected values
-- Date: 2025-12-16
-- Description: Fill in NULL posted_date_corrected values for jobs added after migration 071
--              Uses COALESCE to handle NULL values properly

-- Update jobs where posted_date_corrected is NULL
UPDATE job_postings jp
SET posted_date_corrected = LEAST(
    COALESCE(
        (SELECT MIN(first_seen_at) 
         FROM job_sources 
         WHERE job_posting_id = jp.id),
        jp.posted_date
    ),
    COALESCE(jp.posted_date, 
        (SELECT MIN(first_seen_at) 
         FROM job_sources 
         WHERE job_posting_id = jp.id)
    )
)
WHERE posted_date_corrected IS NULL
  AND (posted_date IS NOT NULL 
       OR EXISTS (SELECT 1 FROM job_sources WHERE job_posting_id = jp.id));

-- Verify results
DO $$
DECLARE
    null_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count FROM job_postings WHERE posted_date_corrected IS NULL;
    SELECT COUNT(*) INTO total_count FROM job_postings;
    
    RAISE NOTICE 'Migration 082 complete:';
    RAISE NOTICE '  Total jobs: %', total_count;
    RAISE NOTICE '  Jobs with NULL posted_date_corrected: %', null_count;
    RAISE NOTICE '  Jobs with posted_date_corrected: %', total_count - null_count;
END $$;
