-- Check run b7848148-895c-42ce-86de-f1245799ea61

SELECT 
    search_query,
    location_query,
    jobs_found,
    jobs_new,
    jobs_updated,
    metadata->>'jobs_error' as jobs_error,
    metadata->'error_details' as error_details,
    metadata->>'batch_summary' as batch_summary,
    started_at,
    completed_at
FROM scrape_runs
WHERE id = 'b7848148-895c-42ce-86de-f1245799ea61';
