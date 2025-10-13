-- Migration: Add job types system
-- This allows categorizing jobs by type (Data, Engineering, etc.)

-- 1. Create job_types table
CREATE TABLE IF NOT EXISTS job_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#3B82F6',  -- Tailwind blue-500 as default
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_job_types_active ON job_types(is_active);
CREATE INDEX idx_job_types_name ON job_types(name);

-- 2. Add job_type_id to search_queries
ALTER TABLE search_queries 
ADD COLUMN IF NOT EXISTS job_type_id UUID REFERENCES job_types(id) ON DELETE SET NULL;

CREATE INDEX idx_search_queries_type ON search_queries(job_type_id);

-- 3. Add job_type_id to scrape_runs (for tracking)
ALTER TABLE scrape_runs
ADD COLUMN IF NOT EXISTS job_type_id UUID REFERENCES job_types(id) ON DELETE SET NULL;

CREATE INDEX idx_scrape_runs_type ON scrape_runs(job_type_id);

-- 4. Create many-to-many relationship: jobs <-> types
CREATE TABLE IF NOT EXISTS job_type_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID REFERENCES job_postings(id) ON DELETE CASCADE,
    job_type_id UUID REFERENCES job_types(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_via TEXT DEFAULT 'scrape',  -- 'scrape', 'manual', 'ai'
    UNIQUE(job_posting_id, job_type_id)
);

-- Add indexes
CREATE INDEX idx_job_type_assignments_job ON job_type_assignments(job_posting_id);
CREATE INDEX idx_job_type_assignments_type ON job_type_assignments(job_type_id);

-- Add updated_at trigger to job_types
CREATE TRIGGER update_job_types_updated_at
    BEFORE UPDATE ON job_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default "Data" type
INSERT INTO job_types (name, description, color, is_active)
VALUES ('Data', 'Data-related positions (Data Engineer, Data Analyst, Data Scientist, etc.)', '#3B82F6', true)
ON CONFLICT (name) DO NOTHING;

-- Comments
COMMENT ON TABLE job_types IS 'Job type categories for classification';
COMMENT ON TABLE job_type_assignments IS 'Many-to-many relationship between jobs and types';
COMMENT ON COLUMN search_queries.job_type_id IS 'Type of jobs this query searches for';
COMMENT ON COLUMN scrape_runs.job_type_id IS 'Type of jobs this run searched for';
