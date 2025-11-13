-- Check when the latest ranking run happened and if duplicates still exist

-- 1. Most recent ranking timestamp
SELECT 
    MAX(ranking_updated_at) as latest_ranking,
    COUNT(DISTINCT ranking_updated_at) as distinct_timestamps,
    COUNT(*) as total_ranked_jobs
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data'
  AND ranking_position IS NOT NULL;

-- 2. Check if duplicates still exist after latest run
SELECT 
    ranking_position,
    COUNT(*) as count,
    STRING_AGG(title || ' (' || COALESCE(source, 'no source') || ')', ' | ') as jobs
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data'
  AND ranking_position IS NOT NULL
  AND ranking_updated_at = (
      SELECT MAX(ranking_updated_at) 
      FROM job_postings 
      WHERE is_active = true 
        AND title_classification = 'Data'
        AND ranking_position IS NOT NULL
  )
GROUP BY ranking_position
HAVING COUNT(*) > 1
ORDER BY ranking_position
LIMIT 10;

-- 3. Total count of active Data jobs
SELECT COUNT(*) as total_active_data_jobs
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data';

-- 4. Count jobs ranked in latest run
SELECT COUNT(*) as jobs_in_latest_run
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data'
  AND ranking_updated_at = (
      SELECT MAX(ranking_updated_at) 
      FROM job_postings 
      WHERE is_active = true 
        AND title_classification = 'Data'
        AND ranking_position IS NOT NULL
  );
