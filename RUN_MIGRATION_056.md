# Migration 056: Add Relevantie & Show in App Columns to Companies

## Run deze SQL in Supabase SQL Editor

Ga naar: https://supabase.com/dashboard → SQL Editor → New Query

```sql
-- Migration 056: Add relevantie and show_in_app columns to company_master_data
-- Date: 2025-12-30
-- Description: Add a manual relevance score (integer) and show_in_app flag for companies

-- Add relevantie column to company_master_data
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS relevantie INTEGER;

COMMENT ON COLUMN company_master_data.relevantie IS 'Manual relevance score for the company (any integer value)';

-- Add show_in_app column (defaults to true for all companies)
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS show_in_app BOOLEAN DEFAULT true;

COMMENT ON COLUMN company_master_data.show_in_app IS 'Whether to show this company in the app (default: true)';

-- Recreate companies_list_view to include relevantie and show_in_app
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
    cmd.show_in_app,
    
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id) AS job_count,
    (SELECT COUNT(*) FROM job_postings jp WHERE jp.company_id = c.id AND jp.is_active = true) AS active_job_count
FROM companies c
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
ORDER BY c.name;

COMMENT ON VIEW companies_list_view IS 'Lightweight view for companies list interface including relevantie score, show_in_app flag, canonical size_category, multilingual sectors/categories, locatie_belgie and essential job metrics.';
```

## Verification

Na het uitvoeren van de migratie, verifieer met:

```sql
-- Check if new columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'company_master_data' 
  AND column_name IN ('relevantie', 'show_in_app');

-- Check if view includes new columns
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'companies_list_view' 
  AND column_name IN ('relevantie', 'show_in_app');
```

## What changed

1. **New columns** added to `company_master_data`:
   - `relevantie` (INTEGER) - manual relevance score
   - `show_in_app` (BOOLEAN, default: true) - visibility flag
2. **Updated view**: `companies_list_view` now includes both columns
3. **UI**: `/companies` page now shows:
   - Narrower company name column
   - **Show** column with eye icon toggle (green=visible, red=hidden)
   - **Relevantie** column (editable number)
4. **API**: Companies API now returns `relevantie` and `show_in_app` in response

## Usage

- **Show in App**: Click the eye icon to toggle visibility (default: visible/green)
- **Relevantie**: Click on the cell to edit, enter any integer, press Enter to save
