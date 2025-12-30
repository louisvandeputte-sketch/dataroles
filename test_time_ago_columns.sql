-- Test query to verify time_ago columns contain data
-- Run this AFTER executing migration 081

-- Sample of jobs with time_ago columns
SELECT 
    job_posting_id,
    title,
    company_name,
    posted_date,
    posted_date_corrected,
    time_ago_nl,
    time_ago_fr,
    time_ago_en,
    EXTRACT(EPOCH FROM (NOW() - posted_date_corrected)) / 86400 AS days_old
FROM vw_job_listings
ORDER BY posted_date_corrected DESC
LIMIT 20;

-- Count jobs by time_ago category (Dutch)
SELECT 
    time_ago_nl,
    COUNT(*) as job_count
FROM vw_job_listings
GROUP BY time_ago_nl
ORDER BY 
    CASE 
        WHEN time_ago_nl = 'Nieuw' THEN 1
        WHEN time_ago_nl LIKE '% dagen geleden' THEN 2
        WHEN time_ago_nl LIKE '% weken geleden' THEN 3
        ELSE 4
    END,
    time_ago_nl;

-- Verify all three language columns are populated
SELECT 
    COUNT(*) as total_jobs,
    COUNT(time_ago_nl) as has_nl,
    COUNT(time_ago_fr) as has_fr,
    COUNT(time_ago_en) as has_en,
    COUNT(CASE WHEN time_ago_nl IS NULL OR time_ago_fr IS NULL OR time_ago_en IS NULL THEN 1 END) as missing_any
FROM vw_job_listings;

-- Show examples of each category in all three languages
SELECT DISTINCT
    CASE 
        WHEN time_ago_nl = 'Nieuw' THEN 1
        WHEN time_ago_nl LIKE '% dagen geleden' THEN 2
        WHEN time_ago_nl LIKE '% weken geleden' THEN 3
        ELSE 4
    END as sort_order,
    time_ago_nl,
    time_ago_fr,
    time_ago_en,
    COUNT(*) OVER (PARTITION BY time_ago_nl) as count_in_category
FROM vw_job_listings
ORDER BY sort_order, time_ago_nl;
