-- Migration 076: Fix tech_stack_lookup logo URLs with correct API prefix
-- Date: 2025-11-30
-- Description: Logo endpoints are under /api/tech-stack/ prefix, not /api/
--              Update view to generate correct URLs

DROP VIEW IF EXISTS tech_stack_lookup;

CREATE OR REPLACE VIEW tech_stack_lookup AS
SELECT 
    name,
    display_name,
    -- Generate dynamic logo URL with CORRECT prefix
    CASE 
        WHEN logo_data IS NOT NULL THEN '/api/tech-stack/programming-languages/' || id || '/logo'
        ELSE logo_url  -- Fallback to static URL if set
    END AS logo_url,
    category,
    'language' AS type
FROM programming_languages
WHERE is_active = TRUE

UNION ALL

SELECT 
    name,
    display_name,
    -- Generate dynamic logo URL with CORRECT prefix
    CASE 
        WHEN logo_data IS NOT NULL THEN '/api/tech-stack/ecosystems/' || id || '/logo'
        ELSE logo_url  -- Fallback to static URL if set
    END AS logo_url,
    category,
    'ecosystem' AS type
FROM ecosystems
WHERE is_active = TRUE;

COMMENT ON VIEW tech_stack_lookup IS 'Lightweight lookup table for tech stack logos with correct API prefix (/api/tech-stack/). Generates dynamic URLs for logos stored in logo_data column. Frontend fetches once, caches, and uses for client-side enrichment. ~1100 items, ~50KB.';
