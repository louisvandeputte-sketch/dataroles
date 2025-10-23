-- Update llm_enrichment table to match new parser schema
-- This migration adds new fields and updates existing ones

-- Add new fields for the updated parser
ALTER TABLE llm_enrichment 
ADD COLUMN IF NOT EXISTS type_datarol TEXT,
ADD COLUMN IF NOT EXISTS rolniveau TEXT[], -- Array of: Technical, Lead, Managerial
ADD COLUMN IF NOT EXISTS seniority TEXT[], -- Array of: Junior, Medior, Senior
ADD COLUMN IF NOT EXISTS contract TEXT[], -- Array of: Vast, Freelance, Intern
ADD COLUMN IF NOT EXISTS sourcing_type TEXT, -- Direct or Agency
ADD COLUMN IF NOT EXISTS samenvatting_kort TEXT,
ADD COLUMN IF NOT EXISTS samenvatting_lang TEXT,
ADD COLUMN IF NOT EXISTS must_have_programmeertalen TEXT[],
ADD COLUMN IF NOT EXISTS nice_to_have_programmeertalen TEXT[],
ADD COLUMN IF NOT EXISTS must_have_ecosystemen TEXT[],
ADD COLUMN IF NOT EXISTS nice_to_have_ecosystemen TEXT[],
ADD COLUMN IF NOT EXISTS must_have_talen TEXT[],
ADD COLUMN IF NOT EXISTS nice_to_have_talen TEXT[];

-- Add check constraints for enum values
ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS check_type_datarol,
ADD CONSTRAINT check_type_datarol 
CHECK (type_datarol IN ('Data Engineer', 'Data Analyst', 'Data Scientist', 'BI Developer', 'Data Architect', 'Data Governance', 'Other', 'NIS'));

ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS check_sourcing_type,
ADD CONSTRAINT check_sourcing_type 
CHECK (sourcing_type IN ('Direct', 'Agency'));

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS idx_llm_type_datarol ON llm_enrichment(type_datarol);
CREATE INDEX IF NOT EXISTS idx_llm_sourcing_type ON llm_enrichment(sourcing_type);

-- For TEXT[] arrays, use btree indexes (simpler, works for equality and containment)
-- Or skip indexes for now - arrays are small and queries will still be fast
-- GIN indexes on TEXT[] require additional setup that may not be available in Supabase
-- CREATE INDEX IF NOT EXISTS idx_llm_rolniveau ON llm_enrichment USING GIN(rolniveau);
-- CREATE INDEX IF NOT EXISTS idx_llm_seniority ON llm_enrichment USING GIN(seniority);
-- CREATE INDEX IF NOT EXISTS idx_llm_contract ON llm_enrichment USING GIN(contract);

-- Comments for documentation
COMMENT ON COLUMN llm_enrichment.type_datarol IS 'Type of data role: Data Engineer, Data Analyst, etc.';
COMMENT ON COLUMN llm_enrichment.rolniveau IS 'Role level(s): Technical, Lead, Managerial';
COMMENT ON COLUMN llm_enrichment.seniority IS 'Seniority level(s): Junior, Medior, Senior';
COMMENT ON COLUMN llm_enrichment.contract IS 'Contract type(s): Vast, Freelance, Intern';
COMMENT ON COLUMN llm_enrichment.sourcing_type IS 'Sourcing type: Direct or Agency';
COMMENT ON COLUMN llm_enrichment.samenvatting_kort IS 'Short summary of the job posting';
COMMENT ON COLUMN llm_enrichment.samenvatting_lang IS 'Long summary of the job posting';
COMMENT ON COLUMN llm_enrichment.must_have_programmeertalen IS 'Required programming languages';
COMMENT ON COLUMN llm_enrichment.nice_to_have_programmeertalen IS 'Nice to have programming languages';
COMMENT ON COLUMN llm_enrichment.must_have_ecosystemen IS 'Required ecosystems/platforms';
COMMENT ON COLUMN llm_enrichment.nice_to_have_ecosystemen IS 'Nice to have ecosystems/platforms';
COMMENT ON COLUMN llm_enrichment.must_have_talen IS 'Required languages (NL, EN, FR, etc.)';
COMMENT ON COLUMN llm_enrichment.nice_to_have_talen IS 'Nice to have languages';
