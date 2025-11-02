-- Migration: Assign all jobs to "Data" job type
-- Assigns the "Data" type to all jobs that don't have a type yet
-- Date: 2025-10-29

-- Step 1: Get the "Data" job type ID (should exist from migration 002)
DO $$
DECLARE
    data_type_id UUID;
BEGIN
    -- Get the Data job type ID
    SELECT id INTO data_type_id
    FROM job_types
    WHERE name = 'Data'
    LIMIT 1;
    
    -- If Data type doesn't exist, create it
    IF data_type_id IS NULL THEN
        INSERT INTO job_types (name, description, color, is_active)
        VALUES ('Data', 'Data-related positions (Data Engineer, Data Analyst, Data Scientist, etc.)', '#3B82F6', true)
        RETURNING id INTO data_type_id;
        
        RAISE NOTICE 'Created Data job type: %', data_type_id;
    ELSE
        RAISE NOTICE 'Using existing Data job type: %', data_type_id;
    END IF;
    
    -- Step 2: Assign all jobs without a type to "Data"
    INSERT INTO job_type_assignments (job_posting_id, job_type_id, assigned_via)
    SELECT 
        jp.id,
        data_type_id,
        'migration' as assigned_via
    FROM job_postings jp
    WHERE jp.id NOT IN (
        SELECT job_posting_id FROM job_type_assignments
    )
    ON CONFLICT (job_posting_id, job_type_id) DO NOTHING;
    
    -- Report results
    RAISE NOTICE 'Assigned Data type to all jobs without a type';
END $$;

-- Show final statistics
SELECT 
    'Total jobs' as metric,
    COUNT(*) as count
FROM job_postings
UNION ALL
SELECT 
    'Jobs with type assignment' as metric,
    COUNT(DISTINCT job_posting_id) as count
FROM job_type_assignments
UNION ALL
SELECT 
    'Jobs with Data type' as metric,
    COUNT(DISTINCT jta.job_posting_id) as count
FROM job_type_assignments jta
JOIN job_types jt ON jta.job_type_id = jt.id
WHERE jt.name = 'Data'
UNION ALL
SELECT 
    'Jobs without type' as metric,
    COUNT(*) as count
FROM job_postings jp
WHERE jp.id NOT IN (
    SELECT job_posting_id FROM job_type_assignments
);
