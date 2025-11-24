-- Migration 065: Replace summary_long with structured sections (v20)
-- Date: 2025-11-24
-- Description: Replace long summaries with bullet-point sections in 3 languages
--              Adds responsibilities, requirements, and offerings arrays

-- 1. Add new JSONB columns for structured sections (arrays of strings)
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

-- 2. Drop old summary_long columns
ALTER TABLE llm_enrichment
DROP COLUMN IF EXISTS samenvatting_lang,
DROP COLUMN IF EXISTS samenvatting_lang_nl,
DROP COLUMN IF EXISTS samenvatting_lang_fr,
DROP COLUMN IF EXISTS samenvatting_lang_en;

-- 3. Add comments for new columns
COMMENT ON COLUMN llm_enrichment.responsibilities IS 'Array of responsibility bullets in English (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.responsibilities_nl IS 'Array of responsibility bullets in Dutch (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.responsibilities_fr IS 'Array of responsibility bullets in French (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.requirements IS 'Array of requirement bullets in English (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.requirements_nl IS 'Array of requirement bullets in Dutch (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.requirements_fr IS 'Array of requirement bullets in French (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.offerings IS 'Array of offering bullets in English (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.offerings_nl IS 'Array of offering bullets in Dutch (max 7, typically 4-5)';
COMMENT ON COLUMN llm_enrichment.offerings_fr IS 'Array of offering bullets in French (max 7, typically 4-5)';

-- 4. Update labels column comment to mention new section headers
COMMENT ON COLUMN llm_enrichment.labels IS 'Structured labels including section headers (responsibilities_label, requirements_label, offerings_label) in NL/EN/FR';

-- 5. Add indexes for JSONB queries (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_responsibilities ON llm_enrichment USING GIN (responsibilities);
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_requirements ON llm_enrichment USING GIN (requirements);
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_offerings ON llm_enrichment USING GIN (offerings);
