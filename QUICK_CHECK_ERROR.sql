-- Quick check: What's the actual error?

SELECT 
    search_query,
    location_query,
    jobs_found,
    jobs_new,
    jobs_updated,
    metadata->>'jobs_error' as jobs_error,
    metadata->'error_details' as error_details,
    metadata->>'batch_summary' as batch_summary
FROM scrape_runs
WHERE id = '5bd808d2-b450-438c-9bd3-40478667f1bd';
