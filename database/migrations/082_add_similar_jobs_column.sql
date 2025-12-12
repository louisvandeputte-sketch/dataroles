-- Migration 082: add similar_job_ids to job_postings for nightly similarity results
-- Ensures frontend can read precomputed similar jobs directly from API responses

ALTER TABLE job_postings
  ADD COLUMN IF NOT EXISTS similar_job_ids JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_job_postings_similar_job_ids
  ON job_postings
  USING GIN (similar_job_ids);
