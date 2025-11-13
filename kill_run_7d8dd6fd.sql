-- Hard kill run 7d8dd6fd-f4a9-4584-9d5c-a9a256678949
UPDATE scrape_runs 
SET 
    status = 'failed',
    completed_at = NOW(),
    metadata = COALESCE(metadata, '{}'::jsonb) || '{"killed_manually": true, "killed_at": "2025-11-13T22:34:00Z"}'::jsonb
WHERE id = '7d8dd6fd-f4a9-4584-9d5c-a9a256678949'
AND status IN ('pending', 'running');

-- Verify the update
SELECT 
    id,
    status,
    jobs_found,
    jobs_new,
    jobs_error,
    created_at,
    completed_at,
    metadata
FROM scrape_runs 
WHERE id = '7d8dd6fd-f4a9-4584-9d5c-a9a256678949';
