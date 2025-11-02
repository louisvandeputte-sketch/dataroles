-- Migration: Assign job types to jobs that are missing them
-- Uses scrape_history and scrape_runs to determine the correct job_type
-- Date: 2025-10-29

-- Insert job_type_assignments for jobs that don't have one yet
-- This uses the job_type_id from the scrape_run that found the job
INSERT INTO job_type_assignments (job_posting_id, job_type_id, assigned_via)
SELECT DISTINCT
    sh.job_posting_id,
    sr.job_type_id,
    'migration' as assigned_via
FROM scrape_history sh
JOIN scrape_runs sr ON sh.scrape_run_id = sr.id
WHERE sr.job_type_id IS NOT NULL
  AND sh.job_posting_id NOT IN (
      SELECT job_posting_id FROM job_type_assignments
  )
ON CONFLICT (job_posting_id, job_type_id) DO NOTHING;

-- Report results
SELECT 
    COUNT(*) as total_assignments,
    COUNT(DISTINCT job_posting_id) as unique_jobs_assigned
FROM job_type_assignments
WHERE assigned_via = 'migration';

-- Show jobs still without type
SELECT 
    COUNT(*) as jobs_without_type
FROM job_postings jp
WHERE jp.id NOT IN (
    SELECT job_posting_id FROM job_type_assignments
);
