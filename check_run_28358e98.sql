-- Check error details for run 28358e98-c8fb-486b-8646-9fafcfaa1039
SELECT 
    id,
    source,
    status,
    jobs_found,
    jobs_new,
    jobs_updated,
    jobs_error,
    metadata,
    created_at
FROM scrape_runs 
WHERE id = '28358e98-c8fb-486b-8646-9fafcfaa1039';

-- Check if any jobs were created
SELECT COUNT(*) as job_count
FROM job_scrape_history 
WHERE scrape_run_id = '28358e98-c8fb-486b-8646-9fafcfaa1039';
