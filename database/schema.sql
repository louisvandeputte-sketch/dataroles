-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    linkedin_company_id TEXT UNIQUE,
    name TEXT NOT NULL,
    industry TEXT,
    company_url TEXT,
    logo_url TEXT,
    employee_count_range TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_company_linkedin_id ON companies(linkedin_company_id);
CREATE INDEX idx_company_name ON companies(name);

-- Locations table
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code TEXT,
    city TEXT,
    region TEXT,
    full_location_string TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_location_country_city ON locations(country_code, city);
CREATE INDEX idx_location_full_string ON locations(full_location_string);

-- Job postings table (main entity)
CREATE TABLE job_postings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    linkedin_job_id TEXT UNIQUE NOT NULL,
    company_id UUID REFERENCES companies(id),
    location_id UUID REFERENCES locations(id),
    title TEXT NOT NULL,
    seniority_level TEXT,
    employment_type TEXT,
    industries TEXT[],
    function_areas TEXT[],
    posted_date TIMESTAMPTZ,
    posted_time_ago TEXT,
    num_applicants INTEGER,
    base_salary_min DECIMAL(12, 2),
    base_salary_max DECIMAL(12, 2),
    salary_currency TEXT,
    salary_period TEXT,
    job_url TEXT NOT NULL,
    apply_url TEXT,
    application_available BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    detected_inactive_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_job_linkedin_id ON job_postings(linkedin_job_id);
CREATE INDEX idx_job_company ON job_postings(company_id);
CREATE INDEX idx_job_location ON job_postings(location_id);
CREATE INDEX idx_job_active ON job_postings(is_active);
CREATE INDEX idx_job_last_seen ON job_postings(last_seen_at);
CREATE INDEX idx_job_posted_date ON job_postings(posted_date);
CREATE INDEX idx_job_title ON job_postings USING gin(to_tsvector('english', title));

-- Job descriptions table (separate for text heavy content)
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID UNIQUE REFERENCES job_postings(id) ON DELETE CASCADE,
    summary TEXT,
    full_description_html TEXT,
    full_description_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_description_job ON job_descriptions(job_posting_id);

-- Job posters table
CREATE TABLE job_posters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID REFERENCES job_postings(id) ON DELETE CASCADE,
    name TEXT,
    title TEXT,
    profile_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_poster_job ON job_posters(job_posting_id);

-- LLM enrichment table (25 dummy fields for future)
CREATE TABLE llm_enrichment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID UNIQUE REFERENCES job_postings(id) ON DELETE CASCADE,
    extracted_skills JSONB,
    required_experience_years INTEGER,
    education_level TEXT,
    remote_work_policy TEXT,
    tech_stack TEXT[],
    soft_skills TEXT[],
    hard_skills TEXT[],
    certifications_mentioned TEXT[],
    programming_languages TEXT[],
    frameworks_libraries TEXT[],
    databases_mentioned TEXT[],
    cloud_platforms TEXT[],
    tools_mentioned TEXT[],
    industry_keywords TEXT[],
    seniority_classification TEXT,
    role_category TEXT,
    team_size_indicator TEXT,
    management_responsibilities BOOLEAN,
    travel_requirements TEXT,
    benefits_mentioned TEXT[],
    company_culture_keywords TEXT[],
    growth_opportunities TEXT,
    work_environment TEXT,
    urgency_indicator TEXT,
    application_complexity_score INTEGER,
    enrichment_completed_at TIMESTAMPTZ,
    enrichment_model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_enrichment_job ON llm_enrichment(job_posting_id);

-- Scrape runs table (track all scrape operations)
CREATE TABLE scrape_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_query TEXT NOT NULL,
    location_query TEXT NOT NULL,
    platform TEXT DEFAULT 'linkedin_brightdata',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'partial'
    jobs_found INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    jobs_updated INTEGER DEFAULT 0,
    jobs_deactivated INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB -- Store API params, snapshot_id, etc.
);

CREATE INDEX idx_scrape_runs_status ON scrape_runs(status, completed_at);
CREATE INDEX idx_scrape_runs_query ON scrape_runs(search_query, location_query);

-- Job scrape history (many-to-many: jobs <-> scrape runs)
CREATE TABLE job_scrape_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID REFERENCES job_postings(id) ON DELETE CASCADE,
    scrape_run_id UUID REFERENCES scrape_runs(id) ON DELETE CASCADE,
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scrape_history_job ON job_scrape_history(job_posting_id);
CREATE INDEX idx_scrape_history_run ON job_scrape_history(scrape_run_id);

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_postings_updated_at BEFORE UPDATE ON job_postings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
