-- Migration: Cleanup company_master_data table
-- Remove unnecessary columns to simplify the schema
-- Date: 2025-10-25

-- Drop columns that are not needed
ALTER TABLE company_master_data
DROP COLUMN IF EXISTS company_number,
DROP COLUMN IF EXISTS description,
DROP COLUMN IF EXISTS employee_count,
DROP COLUMN IF EXISTS employee_count_range,
DROP COLUMN IF EXISTS revenue_eur,
DROP COLUMN IF EXISTS revenue_range,
DROP COLUMN IF EXISTS profitability,
DROP COLUMN IF EXISTS growth_rate,
DROP COLUMN IF EXISTS growth_trend,
DROP COLUMN IF EXISTS tech_stack,
DROP COLUMN IF EXISTS office_locations,
DROP COLUMN IF EXISTS company_culture,
DROP COLUMN IF EXISTS benefits,
DROP COLUMN IF EXISTS remote_policy,
DROP COLUMN IF EXISTS custom_fields,
DROP COLUMN IF EXISTS data_source,
DROP COLUMN IF EXISTS verified,
DROP COLUMN IF EXISTS notes,
DROP COLUMN IF EXISTS last_verified_at;

-- Keep these columns:
-- - id (primary key)
-- - company_id (foreign key to companies)
-- - industry
-- - founded_year
-- - website
-- - jobs_page_url
-- - contact_email
-- - created_at
-- - updated_at

-- Add comment to clarify the simplified structure
COMMENT ON TABLE company_master_data IS 'Simplified company master data with essential fields only. Additional fields will be added as needed.';
