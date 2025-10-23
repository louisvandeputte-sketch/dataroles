-- Migration: Add masterdata tables for programming languages and ecosystems
-- This creates normalized tables for tech stack management with logos and display names

-- 1. Programming Languages Table
CREATE TABLE IF NOT EXISTS programming_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,  -- Canonical name (e.g., "Python", "SQL")
    display_name TEXT NOT NULL,  -- Editable display name (e.g., "Python 3", "PostgreSQL")
    logo_url TEXT,  -- URL to logo image
    category TEXT,  -- Optional: "General Purpose", "Query Language", "Scripting", etc.
    description TEXT,  -- Optional description
    is_active BOOLEAN DEFAULT TRUE,  -- For soft deletion
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Ecosystems Table (Tools, Frameworks, Platforms)
CREATE TABLE IF NOT EXISTS ecosystems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,  -- Canonical name (e.g., "Azure", "Databricks")
    display_name TEXT NOT NULL,  -- Editable display name (e.g., "Microsoft Azure", "Databricks Platform")
    logo_url TEXT,  -- URL to logo image
    category TEXT,  -- Optional: "Cloud Platform", "Data Tool", "Framework", etc.
    description TEXT,  -- Optional description
    is_active BOOLEAN DEFAULT TRUE,  -- For soft deletion
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Junction table: Job Postings <-> Programming Languages
CREATE TABLE IF NOT EXISTS job_programming_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_posting_id UUID NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    programming_language_id UUID NOT NULL REFERENCES programming_languages(id) ON DELETE CASCADE,
    requirement_level TEXT CHECK (requirement_level IN ('must_have', 'nice_to_have')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_posting_id, programming_language_id)
);

-- 4. Junction table: Job Postings <-> Ecosystems
CREATE TABLE IF NOT EXISTS job_ecosystems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_posting_id UUID NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    ecosystem_id UUID NOT NULL REFERENCES ecosystems(id) ON DELETE CASCADE,
    requirement_level TEXT CHECK (requirement_level IN ('must_have', 'nice_to_have')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_posting_id, ecosystem_id)
);

-- 5. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_programming_languages_name ON programming_languages(name);
CREATE INDEX IF NOT EXISTS idx_programming_languages_active ON programming_languages(is_active);
CREATE INDEX IF NOT EXISTS idx_ecosystems_name ON ecosystems(name);
CREATE INDEX IF NOT EXISTS idx_ecosystems_active ON ecosystems(is_active);
CREATE INDEX IF NOT EXISTS idx_job_programming_languages_job ON job_programming_languages(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_job_programming_languages_lang ON job_programming_languages(programming_language_id);
CREATE INDEX IF NOT EXISTS idx_job_ecosystems_job ON job_ecosystems(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_job_ecosystems_eco ON job_ecosystems(ecosystem_id);

-- 6. Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_programming_languages_updated_at
    BEFORE UPDATE ON programming_languages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ecosystems_updated_at
    BEFORE UPDATE ON ecosystems
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 7. Comments
COMMENT ON TABLE programming_languages IS 'Masterdata table for programming languages with logos and display names';
COMMENT ON TABLE ecosystems IS 'Masterdata table for tools, frameworks, and platforms with logos and display names';
COMMENT ON TABLE job_programming_languages IS 'Junction table linking jobs to programming languages';
COMMENT ON TABLE job_ecosystems IS 'Junction table linking jobs to ecosystems';

COMMENT ON COLUMN programming_languages.name IS 'Canonical name used for matching (normalized)';
COMMENT ON COLUMN programming_languages.display_name IS 'User-editable display name for frontend';
COMMENT ON COLUMN programming_languages.logo_url IS 'URL to logo image (can be external or stored)';
COMMENT ON COLUMN ecosystems.name IS 'Canonical name used for matching (normalized)';
COMMENT ON COLUMN ecosystems.display_name IS 'User-editable display name for frontend';
COMMENT ON COLUMN ecosystems.logo_url IS 'URL to logo image (can be external or stored)';

-- 8. Insert common programming languages (with display names matching canonical names initially)
INSERT INTO programming_languages (name, display_name, category) VALUES
    ('Python', 'Python', 'General Purpose'),
    ('SQL', 'SQL', 'Query Language'),
    ('Java', 'Java', 'General Purpose'),
    ('JavaScript', 'JavaScript', 'Web Development'),
    ('TypeScript', 'TypeScript', 'Web Development'),
    ('R', 'R', 'Statistical Computing'),
    ('Scala', 'Scala', 'General Purpose'),
    ('Go', 'Go', 'Systems Programming'),
    ('Bash', 'Bash', 'Scripting'),
    ('PowerShell', 'PowerShell', 'Scripting'),
    ('Julia', 'Julia', 'Scientific Computing'),
    ('C#', 'C#', 'General Purpose'),
    ('C++', 'C++', 'Systems Programming'),
    ('Ruby', 'Ruby', 'General Purpose'),
    ('PHP', 'PHP', 'Web Development'),
    ('Swift', 'Swift', 'Mobile Development'),
    ('Kotlin', 'Kotlin', 'Mobile Development'),
    ('Rust', 'Rust', 'Systems Programming'),
    ('DAX', 'DAX', 'Query Language'),
    ('M', 'M (Power Query)', 'Query Language'),
    ('MDX', 'MDX', 'Query Language'),
    ('VBA', 'VBA', 'Scripting')
ON CONFLICT (name) DO NOTHING;

-- 9. Insert common ecosystems (with display names matching canonical names initially)
INSERT INTO ecosystems (name, display_name, category) VALUES
    ('Apache Spark', 'Apache Spark', 'Data Processing'),
    ('Databricks', 'Databricks', 'Data Platform'),
    ('Airflow', 'Apache Airflow', 'Orchestration'),
    ('dbt', 'dbt (data build tool)', 'Data Transformation'),
    ('Kafka', 'Apache Kafka', 'Streaming'),
    ('Flink', 'Apache Flink', 'Stream Processing'),
    ('Azure', 'Microsoft Azure', 'Cloud Platform'),
    ('AWS', 'Amazon Web Services', 'Cloud Platform'),
    ('GCP', 'Google Cloud Platform', 'Cloud Platform'),
    ('Power BI', 'Microsoft Power BI', 'BI Tool'),
    ('Tableau', 'Tableau', 'BI Tool'),
    ('Looker', 'Looker', 'BI Tool'),
    ('Snowflake', 'Snowflake', 'Data Warehouse'),
    ('BigQuery', 'Google BigQuery', 'Data Warehouse'),
    ('Redshift', 'Amazon Redshift', 'Data Warehouse'),
    ('Synapse', 'Azure Synapse Analytics', 'Data Platform'),
    ('Data Factory', 'Azure Data Factory', 'ETL Tool'),
    ('Collibra', 'Collibra', 'Data Governance'),
    ('Purview', 'Microsoft Purview', 'Data Governance'),
    ('Docker', 'Docker', 'Containerization'),
    ('Kubernetes', 'Kubernetes', 'Orchestration'),
    ('Terraform', 'Terraform', 'Infrastructure as Code'),
    ('Git', 'Git', 'Version Control'),
    ('Jenkins', 'Jenkins', 'CI/CD'),
    ('MLflow', 'MLflow', 'ML Platform'),
    ('TensorFlow', 'TensorFlow', 'ML Framework'),
    ('PyTorch', 'PyTorch', 'ML Framework'),
    ('scikit-learn', 'scikit-learn', 'ML Library'),
    ('Pandas', 'Pandas', 'Data Library'),
    ('NumPy', 'NumPy', 'Data Library'),
    ('Jupyter', 'Jupyter Notebook', 'Development Tool'),
    ('VS Code', 'Visual Studio Code', 'IDE'),
    ('PostgreSQL', 'PostgreSQL', 'Database'),
    ('MySQL', 'MySQL', 'Database'),
    ('MongoDB', 'MongoDB', 'Database'),
    ('Redis', 'Redis', 'Cache/Database'),
    ('Elasticsearch', 'Elasticsearch', 'Search Engine'),
    ('S3', 'Amazon S3', 'Object Storage'),
    ('HDFS', 'Hadoop HDFS', 'Distributed Storage')
ON CONFLICT (name) DO NOTHING;
