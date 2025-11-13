-- Deep dive into run 5bd808d2-b450-438c-9bd3-40478667f1bd

-- 1. Get full run details
SELECT 
    id,
    search_query,
    location_query,
    source,
    status,
    trigger_type,
    started_at,
    completed_at,
    jobs_found,
    jobs_new,
    jobs_updated,
    error_message,
    metadata
FROM scrape_runs
WHERE id = '5bd808d2-b450-438c-9bd3-40478667f1bd';

-- 2. Extract error details from metadata
SELECT 
    metadata->>'jobs_error' as jobs_error,
    metadata->'error_details' as error_details,
    metadata->>'batch_summary' as batch_summary,
    metadata->>'snapshot_id' as snapshot_id
FROM scrape_runs
WHERE id = '5bd808d2-b450-438c-9bd3-40478667f1bd';

-- 3. Check job_scrape_history
SELECT COUNT(*) as history_count
FROM job_scrape_history
WHERE scrape_run_id = '5bd808d2-b450-438c-9bd3-40478667f1bd';

-- 4. Check if any jobs were created around this time
SELECT 
    jp.id,
    jp.title,
    jp.source,
    jp.created_at,
    jp.indeed_job_id,
    jp.linkedin_job_id,
    c.name as company_name
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jp.created_at BETWEEN 
    (SELECT started_at - INTERVAL '1 minute' FROM scrape_runs WHERE id = '5bd808d2-b450-438c-9bd3-40478667f1bd')
    AND
    (SELECT completed_at + INTERVAL '1 minute' FROM scrape_runs WHERE id = '5bd808d2-b450-438c-9bd3-40478667f1bd')
ORDER BY jp.created_at DESC;
