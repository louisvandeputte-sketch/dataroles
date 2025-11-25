# Supabase Migration Instructions

## Run deze SQL queries in Supabase SQL Editor

### Step 1: Add new columns to llm_enrichment table

```sql
-- Migration 065: Add structured section columns
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS responsibilities JSONB,
ADD COLUMN IF NOT EXISTS responsibilities_nl JSONB,
ADD COLUMN IF NOT EXISTS responsibilities_fr JSONB,
ADD COLUMN IF NOT EXISTS requirements JSONB,
ADD COLUMN IF NOT EXISTS requirements_nl JSONB,
ADD COLUMN IF NOT EXISTS requirements_fr JSONB,
ADD COLUMN IF NOT EXISTS offerings JSONB,
ADD COLUMN IF NOT EXISTS offerings_nl JSONB,
ADD COLUMN IF NOT EXISTS offerings_fr JSONB;

-- Mark old columns as deprecated
COMMENT ON COLUMN llm_enrichment.samenvatting_lang IS 'DEPRECATED (v20): No longer populated. Use structured sections (responsibilities/requirements/offerings) instead.';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang_nl IS 'DEPRECATED (v20): No longer populated. Use structured sections instead.';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang_fr IS 'DEPRECATED (v20): No longer populated. Use structured sections instead.';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang_en IS 'DEPRECATED (v20): No longer populated. Use structured sections instead.';

-- Add comments for new columns
COMMENT ON COLUMN llm_enrichment.responsibilities IS 'Array of responsibility bullets in English (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.responsibilities_nl IS 'Array of responsibility bullets in Dutch (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.responsibilities_fr IS 'Array of responsibility bullets in French (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.requirements IS 'Array of requirement bullets in English (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.requirements_nl IS 'Array of requirement bullets in Dutch (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.requirements_fr IS 'Array of requirement bullets in French (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.offerings IS 'Array of offering bullets in English (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.offerings_nl IS 'Array of offering bullets in Dutch (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.offerings_fr IS 'Array of offering bullets in French (max 7, typically 4-5)';

-- Update labels column comment
COMMENT ON COLUMN llm_enrichment.labels IS 'Structured labels including section headers (responsibilities_label, requirements_label, offerings_label) in NL/EN/FR';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_responsibilities ON llm_enrichment USING GIN (responsibilities);
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_requirements ON llm_enrichment USING GIN (requirements);
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_offerings ON llm_enrichment USING GIN (offerings);
```

### Step 2: Update vw_job_listings view

```sql
-- Migration 066: Update view with structured sections
DROP VIEW IF EXISTS vw_job_listings;

CREATE OR REPLACE VIEW vw_job_listings AS
SELECT 
    e.job_posting_id,
    
    -- Job info from job_postings (for convenience)
    j.title,                   -- Job title
    j.posted_date,             -- Job posting date
    j.ranking_position,        -- Ranking position (1 = best)
    j.base_score,              -- Base score (stable, nightly calculation)
    j.ranking_score,           -- Final score (base × hourly_multiplier, hourly)
    j.hourly_multiplier,       -- Hourly random multiplier (0.8-1.2)
    j.ranking_metadata,        -- Score breakdown (F/Q/T/R scores)
    j.title_classification,    -- Title classification (Data, NIS, Other)
    
    -- Company info from companies (for convenience)
    c.logo_url,                -- Company logo URL
    c.name AS company_name,    -- Company name
    
    -- Company sector (multilingual) from company_master_data
    cmd.sector_nl,             -- Company sector in Dutch
    cmd.sector_en,             -- Company sector in English
    cmd.sector_fr,             -- Company sector in French
    
    -- Company size category (multilingual) from company_master_data
    cmd.size_category,         -- Size category enum (startup, scaleup, sme, etc.)
    cmd.category_nl,           -- Category in Dutch (startup, scaleup, kmo, etc.)
    cmd.category_en,           -- Category in English (startup, scaleup, sme, etc.)
    cmd.category_fr,           -- Category in French (startup, scaleup, pme, etc.)
    cmd.size_summary_nl,       -- Dutch size summary
    cmd.size_summary_en,       -- English size summary
    cmd.size_summary_fr,       -- French size summary
    cmd.size_confidence,       -- Confidence score for size classification
    
    -- Additional company metadata
    cmd.aantal_werknemers,     -- Number of employees
    cmd.founded_year,          -- Company founding year
    cmd.industry,              -- Industry (from original data)
    
    -- Location info (multilingual) - WITH OVERRIDE SUPPORT
    COALESCE(j.location_id_override, j.location_id) AS location_id,
    l.city_name_nl,
    l.city_name_en,
    l.city_name_fr,
    l.subdivision_name_nl,
    l.subdivision_name_en,
    l.subdivision_name_fr,
    
    -- Core classification fields (ACTIVE - used for filtering)
    e.type_datarol,            -- Data role type (Data Engineer, Data Analyst, etc.)
    e.rolniveau,               -- Role level array (Technical, Lead, Managerial)
    e.seniority,               -- Seniority array (Junior, Medior, Senior, Expert)
    e.contract,                -- Contract type array (Permanent, Freelance, Intern)
    e.sourcing_type,           -- Sourcing type (Direct, Agency)
    
    -- Multilingual labels (ACTIVE - contains all translations + section headers)
    e.labels,                  -- JSONB with NL/EN/FR translations for all fields + section headers
    
    -- Short summaries in 3 languages (ACTIVE)
    e.samenvatting_kort_en,
    e.samenvatting_kort_nl,
    e.samenvatting_kort_fr,
    
    -- Legacy short summary field (ACTIVE - for backward compatibility)
    e.samenvatting_kort,       -- Legacy: English summary
    
    -- DEPRECATED: Long summaries (no longer populated in v20, kept for backwards compatibility)
    e.samenvatting_lang_en,
    e.samenvatting_lang_nl,
    e.samenvatting_lang_fr,
    e.samenvatting_lang,       -- Legacy: English summary
    
    -- NEW: Structured sections in 3 languages (v20)
    e.responsibilities,        -- Array of responsibility bullets (EN)
    e.responsibilities_nl,     -- Array of responsibility bullets (NL)
    e.responsibilities_fr,     -- Array of responsibility bullets (FR)
    e.requirements,            -- Array of requirement bullets (EN)
    e.requirements_nl,         -- Array of requirement bullets (NL)
    e.requirements_fr,         -- Array of requirement bullets (FR)
    e.offerings,               -- Array of offering bullets (EN)
    e.offerings_nl,            -- Array of offering bullets (NL)
    e.offerings_fr,            -- Array of offering bullets (FR)
    
    -- Tech stack (ACTIVE)
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    
    -- Spoken/written languages (ACTIVE)
    e.must_have_talen,
    e.nice_to_have_talen,
    
    -- Metadata (ACTIVE)
    e.created_at

FROM llm_enrichment e
JOIN job_postings j ON e.job_posting_id = j.id
JOIN companies c ON j.company_id = c.id
LEFT JOIN locations l ON l.id = COALESCE(j.location_id_override, j.location_id)
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
WHERE j.is_active = TRUE
  AND j.title_classification = 'Data';

COMMENT ON VIEW vw_job_listings IS 'View of enriched job listings with structured sections (v20). Includes responsibilities/requirements/offerings arrays instead of summary_long. Section headers in labels JSONB.';
```

## Verification

After running both migrations, verify:

```sql
-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'llm_enrichment' 
  AND column_name IN ('responsibilities', 'responsibilities_nl', 'responsibilities_fr', 
                      'requirements', 'requirements_nl', 'requirements_fr',
                      'offerings', 'offerings_nl', 'offerings_fr');

-- Check view includes new columns
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'vw_job_listings' 
  AND column_name LIKE '%responsib%' 
   OR column_name LIKE '%requirement%' 
   OR column_name LIKE '%offering%';

-- Test query
SELECT 
    job_posting_id,
    responsibilities,
    requirements,
    offerings,
    labels
FROM vw_job_listings
LIMIT 1;
```

## What's included in the view:

### New fields (v20):
- `responsibilities` (JSONB array) - EN
- `responsibilities_nl` (JSONB array) - NL
- `responsibilities_fr` (JSONB array) - FR
- `requirements` (JSONB array) - EN
- `requirements_nl` (JSONB array) - NL
- `requirements_fr` (JSONB array) - FR
- `offerings` (JSONB array) - EN
- `offerings_nl` (JSONB array) - NL
- `offerings_fr` (JSONB array) - FR

### Labels field includes:
```json
{
  "en": {
    "responsibilities_label": "Your responsibilities",
    "requirements_label": "What we expect",
    "offerings_label": "What we offer",
    ...
  },
  "nl": {
    "responsibilities_label": "Jouw verantwoordelijkheden",
    "requirements_label": "Wat wij verwachten",
    "offerings_label": "Wat wij bieden",
    ...
  },
  "fr": {
    "responsibilities_label": "Vos responsabilités",
    "requirements_label": "Ce que nous attendons",
    "offerings_label": "Ce que nous offrons",
    ...
  }
}
```

### Deprecated fields (kept for backwards compatibility):
- `samenvatting_lang` (TEXT) - EN
- `samenvatting_lang_nl` (TEXT) - NL
- `samenvatting_lang_fr` (TEXT) - FR
- `samenvatting_lang_en` (TEXT) - EN

These are no longer populated by v20 enrichments but remain in the database for old enrichments.
