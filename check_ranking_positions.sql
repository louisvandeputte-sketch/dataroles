-- Check if ranking_position matches ranking_score order

SELECT 
    jp.ranking_position,
    jp.ranking_score,
    jp.title,
    c.name as company,
    le.type_datarol,
    le.enrichment_completed_at,
    jp.ranking_updated_at
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE jp.is_active = true
  AND jp.title_classification = 'Data'
ORDER BY jp.ranking_score DESC  -- Sort by SCORE (should match position)
LIMIT 20;

-- Check for duplicate ranking_positions
SELECT 
    ranking_position,
    COUNT(*) as count,
    STRING_AGG(title, ' | ') as jobs
FROM job_postings
WHERE is_active = true
  AND title_classification = 'Data'
  AND ranking_position IS NOT NULL
GROUP BY ranking_position
HAVING COUNT(*) > 1
ORDER BY ranking_position
LIMIT 10;
