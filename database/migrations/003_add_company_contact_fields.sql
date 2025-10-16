-- Add jobs_page_url and contact_email to company_master_data table
-- Migration: 003_add_company_contact_fields
-- Date: 2025-10-13

ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS jobs_page_url TEXT,
ADD COLUMN IF NOT EXISTS contact_email TEXT;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_company_master_data_jobs_page_url 
ON company_master_data(jobs_page_url) 
WHERE jobs_page_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_master_data_contact_email 
ON company_master_data(contact_email) 
WHERE contact_email IS NOT NULL;

-- Add comments
COMMENT ON COLUMN company_master_data.jobs_page_url IS 'URL to company careers/jobs page';
COMMENT ON COLUMN company_master_data.contact_email IS 'Contact email for recruitment/HR';
