-- Migration 039: Remove check constraints from llm_enrichment table
-- These constraints are too restrictive and cause enrichment saves to fail
-- The LLM can return various valid values that don't match the constraints

-- Drop all check constraints on llm_enrichment table
DO $$ 
DECLARE
    constraint_record RECORD;
BEGIN
    -- Find and drop all check constraints on llm_enrichment
    FOR constraint_record IN 
        SELECT conname
        FROM pg_constraint c
        JOIN pg_class cl ON cl.oid = c.conrelid
        WHERE cl.relname = 'llm_enrichment'
        AND c.contype = 'c'
    LOOP
        EXECUTE format('ALTER TABLE llm_enrichment DROP CONSTRAINT IF EXISTS %I', constraint_record.conname);
        RAISE NOTICE 'Dropped constraint: %', constraint_record.conname;
    END LOOP;
END $$;

-- Verify constraints are removed
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(c.oid) as constraint_definition
FROM pg_constraint c
JOIN pg_class cl ON cl.oid = c.conrelid
WHERE cl.relname = 'llm_enrichment'
AND c.contype = 'c';
