-- Debug ranking issue: Check top 10 jobs and their scores

SELECT 
    jp.ranking_position,
    jp.ranking_score,
    jp.title,
    c.name as company,
    jp.source,
    jp.posted_date,
    jp.is_active,
    le.type_datarol as ai_role_type,
    le.enrichment_completed_at,
    jp.ranking_metadata,
    jp.ranking_updated_at,
    -- Check most recent scrape
    (SELECT MAX(jsh.detected_at) 
     FROM job_scrape_history jsh 
     WHERE jsh.job_posting_id = jp.id) as last_scraped_at
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE jp.is_active = true
  AND jp.title_classification = 'Data'
ORDER BY jp.ranking_position ASC
LIMIT 10;

-- Check specifically the two problem jobs
SELECT 
    jp.id,
    jp.ranking_position,
    jp.ranking_score,
    jp.title,
    c.name as company,
    jp.source,
    le.type_datarol,
    le.enrichment_completed_at,
    jp.ranking_metadata::text,
    (SELECT MAX(jsh.detected_at) 
     FROM job_scrape_history jsh 
     WHERE jsh.job_posting_id = jp.id) as last_scraped_at
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE jp.title ILIKE '%Data Scientist Service Medior%'
   OR jp.title ILIKE '%Cloud DataOps Platform Engineer%'
ORDER BY jp.ranking_position;
