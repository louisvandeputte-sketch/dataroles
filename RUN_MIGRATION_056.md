# Migration 056: Add Relevantie Column to Companies

## Run deze SQL in Supabase SQL Editor

Ga naar: https://supabase.com/dashboard → SQL Editor → New Query

```sql
-- Migration 056: Add relevantie column to company_master_data
-- Date: 2025-12-30
-- Description: Add a manual relevance score (integer) for companies

-- Add relevantie column to company_master_data
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS relevantie INTEGER;

COMMENT ON COLUMN company_master_data.relevantie IS 'Manual relevance score for the company (any integer value)';

-- Recreate companies_list_view to include relevantie
DROP VIEW IF EXISTS companies_list_view;

CREATE VIEW companies_list_view AS
SELECT 
    c.id,
    c.name,
    c.logo_url,
    c.industry,
    c.linkedin_company_id,
    
    cmd.id AS master_data_id,
    cmd.hiring_model,
    cmd.is_consulting,
    cmd.sector_nl,
    cmd.sector_en,
    cmd.sector_fr,
    cmd.size_category,
    cmd.category_nl,
    cmd.category_en,
    cmd.category_fr,
    cmd.locatie_belgie,
    cmd.aantal_werknemers,
    cmd.bedrijfswebsite,
    cmd.jobspagina,
    cmd.email_hr,
    cmd.ai_enriched,
    cmd.ai_enriched_at,
    cmd.relevantie,
    
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id) AS job_count,
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id AND jp.is_active = true) AS active_job_count
FROM companies c
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
ORDER BY c.name;

COMMENT ON VIEW companies_list_view IS 'Lightweight view for companies list interface including relevantie score, canonical size_category, multilingual sectors/categories, locatie_belgie and essential job metrics.';
```

## Verification

Na het uitvoeren van de migratie, verifieer met:

```sql
-- Check if relevantie column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'company_master_data' 
  AND column_name = 'relevantie';

-- Check if view includes relevantie
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'companies_list_view' 
  AND column_name = 'relevantie';

-- Test: set a relevantie value
UPDATE company_master_data 
SET relevantie = 10 
WHERE company_id = (SELECT id FROM companies LIMIT 1);
```

## What changed

1. **New column**: `relevantie` (INTEGER) added to `company_master_data` table
2. **Updated view**: `companies_list_view` now includes `relevantie` column
3. **UI**: `/companies` page now shows editable Relevantie column
4. **API**: Companies API now returns `relevantie` in response

## Usage

- Click on the Relevantie cell in the companies table to edit
- Enter any integer value (positive or negative)
- Press Enter or click outside to save
- Press Escape to cancel
