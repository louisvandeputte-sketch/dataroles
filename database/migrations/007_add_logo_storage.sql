-- Migration: Add logo storage columns for binary image data
-- This allows uploading and storing logos directly in the database

-- 1. Add logo storage to programming_languages
ALTER TABLE programming_languages
ADD COLUMN IF NOT EXISTS logo_data BYTEA,  -- Binary image data
ADD COLUMN IF NOT EXISTS logo_filename TEXT,  -- Original filename
ADD COLUMN IF NOT EXISTS logo_content_type TEXT;  -- MIME type (image/png, image/jpeg, etc.)

-- 2. Add logo storage to ecosystems
ALTER TABLE ecosystems
ADD COLUMN IF NOT EXISTS logo_data BYTEA,  -- Binary image data
ADD COLUMN IF NOT EXISTS logo_filename TEXT,  -- Original filename
ADD COLUMN IF NOT EXISTS logo_content_type TEXT;  -- MIME type (image/png, image/jpeg, etc.)

-- 3. Add logo storage to companies
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS logo_data BYTEA,  -- Binary image data
ADD COLUMN IF NOT EXISTS logo_filename TEXT,  -- Original filename
ADD COLUMN IF NOT EXISTS logo_content_type TEXT;  -- MIME type (image/png, image/jpeg, etc.)

-- 4. Comments
COMMENT ON COLUMN programming_languages.logo_data IS 'Binary image data for uploaded logo';
COMMENT ON COLUMN programming_languages.logo_filename IS 'Original filename of uploaded logo';
COMMENT ON COLUMN programming_languages.logo_content_type IS 'MIME type of logo (image/png, image/jpeg, image/svg+xml)';

COMMENT ON COLUMN ecosystems.logo_data IS 'Binary image data for uploaded logo';
COMMENT ON COLUMN ecosystems.logo_filename IS 'Original filename of uploaded logo';
COMMENT ON COLUMN ecosystems.logo_content_type IS 'MIME type of logo (image/png, image/jpeg, image/svg+xml)';

COMMENT ON COLUMN companies.logo_data IS 'Binary image data for uploaded logo';
COMMENT ON COLUMN companies.logo_filename IS 'Original filename of uploaded logo';
COMMENT ON COLUMN companies.logo_content_type IS 'MIME type of logo (image/png, image/jpeg, image/svg+xml)';

-- Note: logo_url column remains for external URLs (optional alternative to uploaded logos)
