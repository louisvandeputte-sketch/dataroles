-- Check metadata for scrape run 3830cbff-3699-47d2-88e4-0ed41ce8b048

-- 1. Get run details with metadata
SELECT 
    id,
    search_query,
    location_query,
    status,
    started_at,
    completed_at,
    jobs_found,
    jobs_new,
    jobs_updated,
    metadata->>'jobs_error' as jobs_error,
    metadata->'error_details' as error_details,
    metadata
FROM scrape_runs
WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048';

-- 2. Check job_scrape_history for this run
SELECT 
    COUNT(*) as jobs_in_history
FROM job_scrape_history
WHERE scrape_run_id = '3830cbff-3699-47d2-88e4-0ed41ce8b048';

-- 3. If there are jobs, show them
SELECT 
    jsh.job_posting_id,
    jp.title,
    c.name as company_name,
    jp.created_at
FROM job_scrape_history jsh
LEFT JOIN job_postings jp ON jsh.job_posting_id = jp.id
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jsh.scrape_run_id = '3830cbff-3699-47d2-88e4-0ed41ce8b048'
ORDER BY jsh.detected_at DESC;

-- 4. Check if any jobs were created around the same time (within 10 minutes)
SELECT 
    jp.id,
    jp.title,
    jp.source,
    jp.created_at,
    c.name as company_name
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jp.created_at BETWEEN 
    (SELECT started_at - INTERVAL '1 minute' FROM scrape_runs WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048')
    AND
    (SELECT COALESCE(completed_at, started_at + INTERVAL '10 minutes') FROM scrape_runs WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048')
ORDER BY jp.created_at DESC;
