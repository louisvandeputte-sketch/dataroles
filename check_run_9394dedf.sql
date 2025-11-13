-- Check the latest run: 9394dedf-62ef-40cb-ad26-3c5e9f9c05dc

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
    metadata->'batch_summary' as batch_summary,
    metadata
FROM scrape_runs
WHERE id = '9394dedf-62ef-40cb-ad26-3c5e9f9c05dc';

-- 2. Check job_scrape_history for this run
SELECT 
    COUNT(*) as jobs_in_history
FROM job_scrape_history
WHERE scrape_run_id = '9394dedf-62ef-40cb-ad26-3c5e9f9c05dc';

-- 3. Check if any jobs exist from this run
SELECT 
    jsh.job_posting_id,
    jp.title,
    c.name as company_name,
    jp.created_at,
    jp.source
FROM job_scrape_history jsh
LEFT JOIN job_postings jp ON jsh.job_posting_id = jp.id
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jsh.scrape_run_id = '9394dedf-62ef-40cb-ad26-3c5e9f9c05dc';

-- 4. Check jobs created around the same time
SELECT 
    jp.id,
    jp.title,
    jp.source,
    jp.created_at,
    c.name as company_name,
    jp.indeed_job_id,
    jp.linkedin_job_id
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jp.created_at BETWEEN 
    (SELECT started_at - INTERVAL '1 minute' FROM scrape_runs WHERE id = '9394dedf-62ef-40cb-ad26-3c5e9f9c05dc')
    AND
    (SELECT completed_at + INTERVAL '1 minute' FROM scrape_runs WHERE id = '9394dedf-62ef-40cb-ad26-3c5e9f9c05dc')
ORDER BY jp.created_at DESC;
