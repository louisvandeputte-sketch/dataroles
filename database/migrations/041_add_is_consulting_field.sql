-- Add is_consulting field to company_master_data table
-- This will be used to apply a penalty to consulting companies in ranking

ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS is_consulting BOOLEAN DEFAULT FALSE;

-- Add comment
COMMENT ON COLUMN company_master_data.is_consulting IS 'Indicates if the company is a consulting/recruitment agency. Used for ranking penalties.';

-- Optional: Update existing consulting companies if you have a list
-- UPDATE company_master_data 
-- SET is_consulting = TRUE 
-- WHERE company_id IN (
--     SELECT id FROM companies 
--     WHERE LOWER(name) LIKE '%consulting%' 
--        OR LOWER(name) LIKE '%recruitment%'
--        OR LOWER(name) LIKE '%staffing%'
-- );
