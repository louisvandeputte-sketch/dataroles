-- Restore check constraints on llm_enrichment table
-- Run this in Supabase SQL Editor to restore the constraints

-- Restore type_datarol constraint
ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS check_type_datarol;

ALTER TABLE llm_enrichment
ADD CONSTRAINT check_type_datarol 
CHECK (type_datarol IN ('Data Engineer', 'Data Analyst', 'Data Scientist', 'BI Developer', 'Data Architect', 'Data Governance', 'Other', 'NIS'));

-- Restore sourcing_type constraint
ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS check_sourcing_type;

ALTER TABLE llm_enrichment
ADD CONSTRAINT check_sourcing_type 
CHECK (sourcing_type IN ('Direct', 'Agency'));

-- Verify constraints are restored
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(c.oid) as constraint_definition
FROM pg_constraint c
JOIN pg_class cl ON cl.oid = c.conrelid
WHERE cl.relname = 'llm_enrichment'
AND c.contype = 'c'
ORDER BY conname;
