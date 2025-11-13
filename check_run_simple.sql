-- Check scrape run details
SELECT 
    id,
    search_query,
    location_query,
    status,
    jobs_found,
    jobs_new,
    jobs_updated,
    started_at,
    completed_at,
    error_message
FROM scrape_runs
WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048';

-- Check job_scrape_history for this run
SELECT 
    jsh.id,
    jsh.job_posting_id,
    jsh.detected_at,
    jp.title,
    c.name as company_name
FROM job_scrape_history jsh
LEFT JOIN job_postings jp ON jsh.job_posting_id = jp.id
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jsh.scrape_run_id = '3830cbff-3699-47d2-88e4-0ed41ce8b048'
ORDER BY jsh.detected_at DESC;

-- Count records
SELECT COUNT(*) as history_count
FROM job_scrape_history
WHERE scrape_run_id = '3830cbff-3699-47d2-88e4-0ed41ce8b048';
