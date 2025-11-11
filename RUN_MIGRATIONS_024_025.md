# Migraties 024 & 025 Uitvoeren

## Overzicht

Je moet 2 migraties handmatig uitvoeren in Supabase SQL Editor:
- **024**: Error tracking voor job title classification
- **025**: Error tracking voor LLM job enrichment

## Stap 1: Migratie 024 - Title Classification Error

### SQL Kopiëren
```bash
cat database/migrations/024_add_title_classification_error.sql
```

### SQL Inhoud
```sql
-- Migration: Add error tracking for job title classification
-- Date: 2025-11-07

-- Add error column to track classification failures
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS title_classification_error TEXT;

-- Add comment
COMMENT ON COLUMN job_postings.title_classification_error IS 'Error message if title classification failed (e.g., OpenAI API quota exceeded)';

-- Add index for filtering failed classifications
CREATE INDEX IF NOT EXISTS idx_job_postings_title_classification_error 
ON job_postings(title_classification_error) 
WHERE title_classification_error IS NOT NULL;
```

### Uitvoeren
1. Ga naar [Supabase SQL Editor](https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new)
2. Plak de SQL hierboven
3. Klik op **Run**
4. Verify: `SELECT column_name FROM information_schema.columns WHERE table_name = 'job_postings' AND column_name = 'title_classification_error';`

## Stap 2: Migratie 025 - LLM Enrichment Error

### SQL Kopiëren
```bash
cat database/migrations/025_add_llm_enrichment_error.sql
```

### SQL Inhoud
```sql
-- Migration: Add error tracking for LLM job enrichment
-- Date: 2025-11-07

-- Add error column to track enrichment failures
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS enrichment_error TEXT;

-- Add comment
COMMENT ON COLUMN llm_enrichment.enrichment_error IS 'Error message if LLM enrichment failed (e.g., OpenAI API error, parsing error, quota exceeded)';

-- Add index for filtering failed enrichments
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_error 
ON llm_enrichment(enrichment_error) 
WHERE enrichment_error IS NOT NULL;

-- Add index for finding jobs that need retry (failed but not completed)
CREATE INDEX IF NOT EXISTS idx_llm_enrichment_needs_retry
ON llm_enrichment(enrichment_error, enrichment_completed_at)
WHERE enrichment_error IS NOT NULL AND enrichment_completed_at IS NULL;
```

### Uitvoeren
1. Ga naar [Supabase SQL Editor](https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new)
2. Plak de SQL hierboven
3. Klik op **Run**
4. Verify: `SELECT column_name FROM information_schema.columns WHERE table_name = 'llm_enrichment' AND column_name = 'enrichment_error';`

## Verificatie

### Check of migraties succesvol zijn:

```sql
-- Check migratie 024
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'job_postings' 
  AND column_name = 'title_classification_error';

-- Check migratie 025
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'llm_enrichment' 
  AND column_name = 'enrichment_error';

-- Check indexes
SELECT 
    indexname, 
    tablename
FROM pg_indexes 
WHERE indexname IN (
    'idx_job_postings_title_classification_error',
    'idx_llm_enrichment_error',
    'idx_llm_enrichment_needs_retry'
);
```

**Verwachte output:**
```
-- Migratie 024
column_name                      | data_type | is_nullable
---------------------------------|-----------|------------
title_classification_error       | text      | YES

-- Migratie 025
column_name                      | data_type | is_nullable
---------------------------------|-----------|------------
enrichment_error                 | text      | YES

-- Indexes
indexname                                | tablename
-----------------------------------------|------------------
idx_job_postings_title_classification_error | job_postings
idx_llm_enrichment_error                | llm_enrichment
idx_llm_enrichment_needs_retry          | llm_enrichment
```

## Na Migraties

### Test de Error Tracking

**Job Title Classification:**
```python
python reclassify_all_jobs.py
# Check of errors worden opgeslagen bij failures
```

**Job Enrichment:**
```python
python find_failed_job_enrichments.py
# Check of errors zichtbaar zijn
```

## Waarom Handmatig?

Supabase Python client ondersteunt geen raw SQL execution. Daarom moeten migraties handmatig via de SQL Editor worden uitgevoerd.

## Checklist

- [ ] Migratie 024 uitgevoerd in Supabase SQL Editor
- [ ] Migratie 025 uitgevoerd in Supabase SQL Editor
- [ ] Verificatie queries uitgevoerd
- [ ] Kolommen en indexes bestaan
- [ ] Error tracking werkt (test met scripts)

## Troubleshooting

### Error: "column already exists"
```sql
-- Check of kolom al bestaat
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'job_postings' AND column_name = 'title_classification_error';

-- Als kolom bestaat, skip de ALTER TABLE statement
```

### Error: "index already exists"
```sql
-- Check of index al bestaat
SELECT indexname FROM pg_indexes 
WHERE indexname = 'idx_job_postings_title_classification_error';

-- Als index bestaat, skip de CREATE INDEX statement
```

### Rollback
```sql
-- Migratie 024 rollback
ALTER TABLE job_postings DROP COLUMN IF EXISTS title_classification_error;
DROP INDEX IF EXISTS idx_job_postings_title_classification_error;

-- Migratie 025 rollback
ALTER TABLE llm_enrichment DROP COLUMN IF EXISTS enrichment_error;
DROP INDEX IF EXISTS idx_llm_enrichment_error;
DROP INDEX IF EXISTS idx_llm_enrichment_needs_retry;
```
