-- Analysis query: Count jobs posted before 2025-12-05 with title_classification = 'Data'
-- This helps determine the scope for re-enrichment

-- Count total jobs matching criteria
SELECT 
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN e.enrichment_completed_at IS NOT NULL THEN 1 END) as already_enriched,
    COUNT(CASE WHEN e.enrichment_completed_at IS NULL THEN 1 END) as not_enriched,
    COUNT(CASE WHEN e.enrichment_error IS NOT NULL THEN 1 END) as has_errors,
    MIN(j.posted_date) as oldest_job,
    MAX(j.posted_date) as newest_job
FROM job_postings j
LEFT JOIN llm_enrichment e ON j.id = e.job_posting_id
WHERE j.posted_date < '2025-12-05'
  AND j.title_classification = 'Data'
  AND j.is_active = true;

-- Sample of jobs to re-enrich (first 10)
SELECT 
    j.id,
    j.title,
    j.posted_date,
    j.company_id,
    c.name as company_name,
    e.enrichment_completed_at,
    e.enrichment_error,
    CASE 
        WHEN e.enrichment_completed_at IS NOT NULL THEN 'Already enriched'
        WHEN e.enrichment_error IS NOT NULL THEN 'Has error'
        ELSE 'Not enriched'
    END as status
FROM job_postings j
LEFT JOIN companies c ON j.company_id = c.id
LEFT JOIN llm_enrichment e ON j.id = e.job_posting_id
WHERE j.posted_date < '2025-12-05'
  AND j.title_classification = 'Data'
  AND j.is_active = true
ORDER BY j.posted_date ASC
LIMIT 10;

-- Breakdown by month
SELECT 
    DATE_TRUNC('month', j.posted_date) as month,
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN e.enrichment_completed_at IS NOT NULL THEN 1 END) as enriched,
    COUNT(CASE WHEN e.enrichment_completed_at IS NULL THEN 1 END) as not_enriched
FROM job_postings j
LEFT JOIN llm_enrichment e ON j.id = e.job_posting_id
WHERE j.posted_date < '2025-12-05'
  AND j.title_classification = 'Data'
  AND j.is_active = true
GROUP BY DATE_TRUNC('month', j.posted_date)
ORDER BY month DESC;
