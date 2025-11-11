-- Migration 032: Add perks field to llm_enrichment table
-- Date: 2025-11-10
-- Description: Add perks JSONB array field for storing job perks (remote, salary, car, etc.)

-- Add perks column to llm_enrichment table
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS perks JSONB DEFAULT NULL;

-- Add comment
COMMENT ON COLUMN llm_enrichment.perks IS 'Array of job perks with multilingual labels (remote_policy, salary_range, company_car, hospitalization_insurance, training_budget, team_events)';

-- Create index for perks queries
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perks ON llm_enrichment USING GIN (perks);

-- Example perks structure (v15 final):
-- [
--   { "key": "remote_policy", "found": true },
--   { "key": "salary_range", "found": true },
--   { "key": "company_car", "found": false },
--   { "key": "hospitalization_insurance", "found": true },
--   { "key": "training_budget", "found": false },
--   { "key": "team_events", "found": true }
-- ]
-- Note: All perk labels (NL/EN/FR) are stored in labels JSONB column:
--   labels.nl.perks, labels.en.perks, labels.fr.perks (i18n structure)
