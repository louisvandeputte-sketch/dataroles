-- Migration: Make source a many-to-many relationship
-- Date: 2025-11-10
-- Purpose: Allow jobs to have multiple sources (LinkedIn AND Indeed)

-- Step 1: Create job_sources junction table
CREATE TABLE IF NOT EXISTS job_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_posting_id UUID NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (source IN ('linkedin', 'indeed')),
    source_job_id TEXT NOT NULL,  -- linkedin_job_id or indeed_job_id
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_posting_id, source)  -- One entry per source per job
);

COMMENT ON TABLE job_sources IS 'Many-to-many relationship between jobs and their sources';
COMMENT ON COLUMN job_sources.source_job_id IS 'The job ID from the source platform (linkedin_job_id or indeed_job_id)';
COMMENT ON COLUMN job_sources.first_seen_at IS 'When this job was first seen from this source';
COMMENT ON COLUMN job_sources.last_seen_at IS 'When this job was last seen from this source';

-- Step 2: Create indexes
CREATE INDEX IF NOT EXISTS idx_job_sources_job_id ON job_sources(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_job_sources_source ON job_sources(source);
CREATE INDEX IF NOT EXISTS idx_job_sources_source_job_id ON job_sources(source_job_id);

-- Step 3: Migrate existing data
-- For each existing job, create a job_sources entry
INSERT INTO job_sources (job_posting_id, source, source_job_id, first_seen_at, last_seen_at)
SELECT 
    id,
    source,
    CASE 
        WHEN source = 'linkedin' THEN linkedin_job_id
        WHEN source = 'indeed' THEN indeed_job_id
    END as source_job_id,
    created_at,
    last_seen_at
FROM job_postings
WHERE (source = 'linkedin' AND linkedin_job_id IS NOT NULL)
   OR (source = 'indeed' AND indeed_job_id IS NOT NULL)
ON CONFLICT (job_posting_id, source) DO NOTHING;

-- Step 4: Add deduplication helper columns
-- Add normalized title and company for deduplication
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS title_normalized TEXT,
ADD COLUMN IF NOT EXISTS dedup_key TEXT;

-- Create normalized title (lowercase, trim, remove extra spaces)
UPDATE job_postings
SET title_normalized = LOWER(TRIM(REGEXP_REPLACE(title, '\s+', ' ', 'g')));

-- Create deduplication key (title + company)
UPDATE job_postings p
SET dedup_key = LOWER(TRIM(p.title_normalized || '|' || COALESCE(c.name, '')))
FROM companies c
WHERE p.company_id = c.id;

-- Step 5: Create unique index on dedup_key
-- NOTE: Commented out - run resolve_duplicates.py first, then create index manually
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_job_postings_dedup_key ON job_postings(dedup_key);

-- Step 6: Add comments
COMMENT ON COLUMN job_postings.title_normalized IS 'Normalized job title for deduplication (lowercase, trimmed)';
COMMENT ON COLUMN job_postings.dedup_key IS 'Deduplication key: normalized_title|company_name';

-- Note: The source column in job_postings is kept for backward compatibility
-- but the authoritative source information is now in job_sources table
