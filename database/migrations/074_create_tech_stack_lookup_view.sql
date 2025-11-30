-- Migration 074: Create tech_stack_lookup view for client-side logo enrichment
-- Date: 2025-11-30
-- Description: Create lightweight lookup view for tech stack logos
--              Frontend fetches once (~100ms, ~50KB), caches, and merges with job data client-side
--              Much faster than subqueries in main view (~300ms total vs ~17s for 20 jobs)

-- Create lookup view combining both programming languages and ecosystems
CREATE OR REPLACE VIEW tech_stack_lookup AS
SELECT 
    name,
    display_name,
    logo_url,
    category,
    'language' AS type
FROM programming_languages
WHERE is_active = TRUE

UNION ALL

SELECT 
    name,
    display_name,
    logo_url,
    category,
    'ecosystem' AS type
FROM ecosystems
WHERE is_active = TRUE;

-- Add indexes for fast case-insensitive lookups
CREATE INDEX IF NOT EXISTS idx_programming_languages_name_lower 
ON programming_languages(LOWER(name))
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_ecosystems_name_lower 
ON ecosystems(LOWER(name))
WHERE is_active = TRUE;

-- Add comment
COMMENT ON VIEW tech_stack_lookup IS 'Lightweight lookup table for tech stack logos and metadata. Contains ~1100 items (~50KB). Frontend should fetch once on app load, cache in memory, and use for client-side enrichment of job listings. Much faster than database-side joins.';
