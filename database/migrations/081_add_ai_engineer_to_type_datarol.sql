-- Migration: Add 'AI Engineer' to type_datarol constraint
-- Date: 2025-12-10
-- Description: Add 'AI Engineer' as a valid value for type_datarol enum constraint

-- Drop and recreate the constraint with AI Engineer included
ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS check_type_datarol;

ALTER TABLE llm_enrichment
ADD CONSTRAINT check_type_datarol 
CHECK (type_datarol IN (
    'Data Engineer', 
    'Data Analyst', 
    'Data Scientist', 
    'BI Developer', 
    'Data Architect', 
    'Data Governance', 
    'AI Engineer',  -- NEW: Added AI Engineer
    'Other', 
    'NIS'
));

-- Verify the constraint
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conname = 'check_type_datarol';

COMMENT ON CONSTRAINT check_type_datarol ON llm_enrichment IS 
'Valid data role types including AI Engineer (added 2025-12-10)';
