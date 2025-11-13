-- Diagnose why there are duplicate ranking_positions

-- 1. Count total active Data jobs
SELECT 
    'Total Active Data Jobs' as metric,
    COUNT(*) as count
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data';

-- 2. Count jobs with ranking_position
SELECT 
    'Jobs With Ranking Position' as metric,
    COUNT(*) as count
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data'
  AND ranking_position IS NOT NULL;

-- 3. Check if there are two different ranking_updated_at timestamps
SELECT 
    ranking_updated_at,
    COUNT(*) as job_count,
    MIN(ranking_position) as min_rank,
    MAX(ranking_position) as max_rank
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data'
  AND ranking_position IS NOT NULL
GROUP BY ranking_updated_at
ORDER BY ranking_updated_at DESC;

-- 4. Show the duplicate rank 1 jobs in detail
SELECT 
    jp.id,
    jp.ranking_position,
    jp.ranking_score,
    jp.title,
    c.name as company,
    jp.source,
    le.enrichment_completed_at,
    jp.ranking_updated_at,
    jp.created_at
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE jp.ranking_position = 1
  AND jp.is_active = true
  AND jp.title_classification = 'Data'
ORDER BY jp.ranking_score DESC;
