-- Migration: Add multilingual support to LLM enrichment
-- This adds separate columns for NL, FR, EN summaries and uses JSONB for labels

-- 1. Add language-specific summary columns
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS samenvatting_kort_nl TEXT,
ADD COLUMN IF NOT EXISTS samenvatting_kort_fr TEXT,
ADD COLUMN IF NOT EXISTS samenvatting_kort_en TEXT,
ADD COLUMN IF NOT EXISTS samenvatting_lang_nl TEXT,
ADD COLUMN IF NOT EXISTS samenvatting_lang_fr TEXT,
ADD COLUMN IF NOT EXISTS samenvatting_lang_en TEXT;

-- 2. Add JSONB column for labels (shared across languages for technical data)
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS labels JSONB;

-- 3. Keep existing columns for backward compatibility but mark as deprecated
COMMENT ON COLUMN llm_enrichment.samenvatting_kort IS 'DEPRECATED: Use samenvatting_kort_nl/fr/en instead';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang IS 'DEPRECATED: Use samenvatting_lang_nl/fr/en instead';

-- 4. Add indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_labels ON llm_enrichment USING GIN (labels);

-- 5. Comments
COMMENT ON COLUMN llm_enrichment.samenvatting_kort_nl IS 'Short summary in Dutch (4-5 sentences)';
COMMENT ON COLUMN llm_enrichment.samenvatting_kort_fr IS 'Short summary in French (4-5 sentences)';
COMMENT ON COLUMN llm_enrichment.samenvatting_kort_en IS 'Short summary in English (4-5 sentences)';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang_nl IS 'Long summary in Dutch (8-11 sentences)';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang_fr IS 'Long summary in French (8-11 sentences)';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang_en IS 'Long summary in English (8-11 sentences)';
COMMENT ON COLUMN llm_enrichment.labels IS 'Structured labels (type_datarol, rolniveau, seniority, contract, sourcing_type, languages)';
