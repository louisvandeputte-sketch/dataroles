# Migration 033: Add Relevance Scores

## What This Does

Adds `relevance_score` column (0-100) to `programming_languages` and `ecosystems` tables for sorting by relevance to data professionals.

## Run Migration

### In Supabase SQL Editor:

```sql
-- Add relevance_score to programming_languages
ALTER TABLE programming_languages
ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT NULL;

COMMENT ON COLUMN programming_languages.relevance_score IS 
'AI-scored relevance (0-100) for data professionals. 0=niche/irrelevant, 100=essential/universal';

-- Add relevance_score to ecosystems
ALTER TABLE ecosystems
ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT NULL;

COMMENT ON COLUMN ecosystems.relevance_score IS 
'AI-scored relevance (0-100) for data professionals. 0=niche/irrelevant, 100=essential/universal';

-- Add indexes for sorting by relevance
CREATE INDEX IF NOT EXISTS idx_programming_languages_relevance 
ON programming_languages(relevance_score DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_ecosystems_relevance 
ON ecosystems(relevance_score DESC NULLS LAST);
```

## Verify

```sql
-- Check columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('programming_languages', 'ecosystems')
AND column_name = 'relevance_score';

-- Check indexes
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('programming_languages', 'ecosystems')
AND indexname LIKE '%relevance%';
```

## What Happens Next

After migration:
1. ✅ Auto-enrichment service will automatically score all languages/ecosystems
2. ✅ Scores every 60 seconds (10 languages + 10 ecosystems per cycle)
3. ✅ New languages/ecosystems get scored automatically
4. ✅ Can sort by relevance in UI

## Rollback (if needed)

```sql
DROP INDEX IF EXISTS idx_programming_languages_relevance;
DROP INDEX IF EXISTS idx_ecosystems_relevance;
ALTER TABLE programming_languages DROP COLUMN IF EXISTS relevance_score;
ALTER TABLE ecosystems DROP COLUMN IF EXISTS relevance_score;
```
