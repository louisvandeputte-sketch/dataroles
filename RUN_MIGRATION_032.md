# Migration 032: Add Perks Field

## Run This Migration

**Go to Supabase Dashboard → SQL Editor → New Query**

Paste and run:

```sql
-- Add perks column to llm_enrichment table
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS perks JSONB DEFAULT NULL;

-- Add comment
COMMENT ON COLUMN llm_enrichment.perks IS 'Array of job perks with multilingual labels';

-- Create index for perks queries
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perks ON llm_enrichment USING GIN (perks);
```

## Verify

```sql
-- Check column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'llm_enrichment' 
AND column_name = 'perks';
```

Expected output:
```
column_name | data_type
------------|----------
perks       | jsonb
```
