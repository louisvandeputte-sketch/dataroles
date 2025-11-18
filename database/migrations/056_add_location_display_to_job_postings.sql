-- Migration 056: Add location_id_override to job_postings
-- Date: 2025-11-18
-- Description: Add location_id_override that points to a more specific location when job location is vague

-- Add location_id_override column
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS location_id_override UUID REFERENCES locations(id);

-- Add comment
COMMENT ON COLUMN job_postings.location_id_override IS 'Override location ID used when original location is vague (e.g., "Flemish Region"). Points to a more specific location created from company locatie_belgie. Frontend should use COALESCE(location_id_override, location_id) to get the display location.';

-- Note: This field will be populated by:
-- 1. Ingestion pipeline (processor.py) for new jobs
-- 2. Backfill script (scripts/backfill_location_override.py) for existing jobs
