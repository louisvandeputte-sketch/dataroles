-- Migration 075: Fix tech_stack_lookup to generate dynamic logo URLs
-- Date: 2025-11-30
-- Description: Generate logo URLs dynamically based on whether logo_data exists
--              If logo_data exists, generate URL like /api/programming-languages/{id}/logo
--              If logo_data is NULL, return NULL
--              This ensures uploaded logos are visible in frontend

DROP VIEW IF EXISTS tech_stack_lookup;

CREATE OR REPLACE VIEW tech_stack_lookup AS
SELECT 
    name,
    display_name,
    -- Generate dynamic logo URL if logo_data exists
    CASE 
        WHEN logo_data IS NOT NULL THEN '/api/programming-languages/' || id || '/logo'
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
    -- Generate dynamic logo URL if logo_data exists
    CASE 
        WHEN logo_data IS NOT NULL THEN '/api/ecosystems/' || id || '/logo'
        ELSE logo_url  -- Fallback to static URL if set
    END AS logo_url,
    category,
    'ecosystem' AS type
FROM ecosystems
WHERE is_active = TRUE;

-- Indexes already exist from migration 074
-- No need to recreate them

COMMENT ON VIEW tech_stack_lookup IS 'Lightweight lookup table for tech stack logos with dynamic URL generation. If logo_data exists, generates URL like /api/{type}/{id}/logo. Frontend fetches once, caches, and uses for client-side enrichment. ~1100 items, ~50KB.';
