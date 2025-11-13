-- Check the latest run: 231a7f61-0d52-4ba7-a460-676c08002ecf

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
WHERE id = '231a7f61-0d52-4ba7-a460-676c08002ecf';
