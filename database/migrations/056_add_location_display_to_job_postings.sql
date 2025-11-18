-- Migration 056: Add location_display fields to job_postings
-- Date: 2025-11-18
-- Description: Add multilingual display location fields that show company location when job location is vague

-- Add location_display columns (multilingual)
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS location_display_nl TEXT,
ADD COLUMN IF NOT EXISTS location_display_en TEXT,
ADD COLUMN IF NOT EXISTS location_display_fr TEXT;

-- Add comments
COMMENT ON COLUMN job_postings.location_display_nl IS 'Display location in Dutch. Uses company locatie_belgie when job location is vague (e.g., "Flemish Region"). Otherwise uses location.city_name_nl.';
COMMENT ON COLUMN job_postings.location_display_en IS 'Display location in English. Uses company locatie_belgie when job location is vague (e.g., "Flemish Region"). Otherwise uses location.city_name_en.';
COMMENT ON COLUMN job_postings.location_display_fr IS 'Display location in French. Uses company locatie_belgie when job location is vague (e.g., "Flemish Region"). Otherwise uses location.city_name_fr.';

-- Note: These fields will be populated by:
-- 1. Ingestion pipeline (processor.py) for new jobs
-- 2. Backfill script (scripts/backfill_location_display.py) for existing jobs
