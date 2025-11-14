-- Reset all ranking data to start fresh with view-based ranking
-- This clears all ranking scores, positions, and metadata

UPDATE job_postings
SET 
    ranking_score = NULL,
    ranking_position = 999999,  -- Default position for unranked jobs
    ranking_updated_at = NULL,
    ranking_metadata = NULL,
    needs_ranking = TRUE
WHERE title_classification = 'Data' AND is_active = TRUE;

-- Verify the reset
-- SELECT 
--     COUNT(*) as total_jobs,
--     COUNT(ranking_score) as ranked_jobs,
--     COUNT(*) FILTER (WHERE needs_ranking = TRUE) as needs_ranking
-- FROM job_postings
-- WHERE title_classification = 'Data' AND is_active = TRUE;
