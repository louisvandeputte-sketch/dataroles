-- Fix rolniveau constraint to allow array values
-- The old constraint was for string values, but we now use TEXT[] arrays

-- Drop the old constraint if it exists
ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS llm_enrichment_rolniveau_check;

-- No new constraint needed - arrays can contain any text values
-- The application logic will ensure only valid values are used
