-- Migration 078: Add tech_stack_aliases table for name normalization
-- Date: 2025-12-04
-- Description: Create alias mapping table to standardize tech stack naming variations
--              Solves issues like "PowerBI" vs "Power BI" vs "Microsoft Power BI"

-- 1. Create aliases table
CREATE TABLE IF NOT EXISTS tech_stack_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alias TEXT NOT NULL UNIQUE,  -- Variant name (e.g., "PowerBI", "MS Power BI")
    canonical_name TEXT NOT NULL,  -- Canonical name (e.g., "Power BI")
    type TEXT NOT NULL CHECK (type IN ('language', 'ecosystem')),
    notes TEXT,  -- Optional notes about this alias
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_aliases_alias_lower 
ON tech_stack_aliases(LOWER(alias));

CREATE INDEX IF NOT EXISTS idx_aliases_canonical 
ON tech_stack_aliases(canonical_name, type);

CREATE INDEX IF NOT EXISTS idx_aliases_type 
ON tech_stack_aliases(type);

-- 3. Trigger for updated_at
CREATE TRIGGER update_tech_stack_aliases_updated_at
    BEFORE UPDATE ON tech_stack_aliases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 4. Comments
COMMENT ON TABLE tech_stack_aliases IS 'Alias mapping table for tech stack name normalization. Maps variations like "PowerBI", "MS Power BI" to canonical "Power BI"';
COMMENT ON COLUMN tech_stack_aliases.alias IS 'Variant/alternative name for a tech stack item';
COMMENT ON COLUMN tech_stack_aliases.canonical_name IS 'Canonical name that this alias maps to (must exist in programming_languages or ecosystems)';
COMMENT ON COLUMN tech_stack_aliases.type IS 'Type of tech stack: language or ecosystem';
COMMENT ON COLUMN tech_stack_aliases.notes IS 'Optional notes about why this alias exists or its source';

-- 5. Insert common aliases for standardization
-- Power BI variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('PowerBI', 'Power BI', 'ecosystem', 'Common typo without space'),
    ('MS Power BI', 'Power BI', 'ecosystem', 'With Microsoft prefix'),
    ('Microsoft Power BI', 'Power BI', 'ecosystem', 'Full Microsoft branding'),
    ('Power BI Service', 'Power BI', 'ecosystem', 'Cloud service variant'),
    ('power bi', 'Power BI', 'ecosystem', 'Lowercase variant'),
    ('powerbi', 'Power BI', 'ecosystem', 'Lowercase no space')
ON CONFLICT (alias) DO NOTHING;

-- Databricks variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('databricks', 'Databricks', 'ecosystem', 'Lowercase variant'),
    ('DataBricks', 'Databricks', 'ecosystem', 'CamelCase variant')
ON CONFLICT (alias) DO NOTHING;

-- Azure variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('Microsoft Azure', 'Azure', 'ecosystem', 'Full Microsoft branding'),
    ('MS Azure', 'Azure', 'ecosystem', 'Short Microsoft prefix'),
    ('azure', 'Azure', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- AWS variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('Amazon AWS', 'AWS', 'ecosystem', 'Full Amazon branding'),
    ('Amazon Web Services', 'AWS', 'ecosystem', 'Full name'),
    ('aws', 'AWS', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- GCP variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('Google Cloud Platform', 'GCP', 'ecosystem', 'Full name'),
    ('Google Cloud', 'GCP', 'ecosystem', 'Short name'),
    ('gcp', 'GCP', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Python variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('python', 'Python', 'language', 'Lowercase variant'),
    ('Python 3', 'Python', 'language', 'Version specific'),
    ('Python3', 'Python', 'language', 'Version specific no space')
ON CONFLICT (alias) DO NOTHING;

-- SQL variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('sql', 'SQL', 'language', 'Lowercase variant'),
    ('Sql', 'SQL', 'language', 'Title case variant')
ON CONFLICT (alias) DO NOTHING;

-- R variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('r', 'R', 'language', 'Lowercase variant'),
    ('R language', 'R', 'language', 'With language suffix')
ON CONFLICT (alias) DO NOTHING;

-- Spark variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('Apache Spark', 'Spark', 'ecosystem', 'Full Apache branding'),
    ('spark', 'Spark', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- PySpark variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('pyspark', 'PySpark', 'language', 'Lowercase variant'),
    ('Pyspark', 'PySpark', 'language', 'Title case variant'),
    ('Py Spark', 'PySpark', 'language', 'With space')
ON CONFLICT (alias) DO NOTHING;

-- dbt variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('DBT', 'dbt', 'ecosystem', 'Uppercase variant'),
    ('Dbt', 'dbt', 'ecosystem', 'Title case variant'),
    ('data build tool', 'dbt', 'ecosystem', 'Full name')
ON CONFLICT (alias) DO NOTHING;

-- Terraform variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('TerraForm', 'Terraform', 'ecosystem', 'CamelCase variant'),
    ('terraform', 'Terraform', 'ecosystem', 'Lowercase variant'),
    ('Terra Form', 'Terraform', 'ecosystem', 'With space')
ON CONFLICT (alias) DO NOTHING;

-- Docker variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('docker', 'Docker', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Kubernetes variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('kubernetes', 'Kubernetes', 'ecosystem', 'Lowercase variant'),
    ('K8s', 'Kubernetes', 'ecosystem', 'Common abbreviation'),
    ('k8s', 'Kubernetes', 'ecosystem', 'Lowercase abbreviation')
ON CONFLICT (alias) DO NOTHING;

-- PostgreSQL variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('Postgres', 'PostgreSQL', 'ecosystem', 'Short name'),
    ('postgres', 'PostgreSQL', 'ecosystem', 'Lowercase short name'),
    ('postgresql', 'PostgreSQL', 'ecosystem', 'Lowercase variant'),
    ('Postgresql', 'PostgreSQL', 'ecosystem', 'Title case variant')
ON CONFLICT (alias) DO NOTHING;

-- JavaScript variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('javascript', 'JavaScript', 'language', 'Lowercase variant'),
    ('Javascript', 'JavaScript', 'language', 'Title case variant'),
    ('JS', 'JavaScript', 'language', 'Common abbreviation'),
    ('js', 'JavaScript', 'language', 'Lowercase abbreviation')
ON CONFLICT (alias) DO NOTHING;

-- TypeScript variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('typescript', 'TypeScript', 'language', 'Lowercase variant'),
    ('Typescript', 'TypeScript', 'language', 'Title case variant'),
    ('TS', 'TypeScript', 'language', 'Common abbreviation'),
    ('ts', 'TypeScript', 'language', 'Lowercase abbreviation')
ON CONFLICT (alias) DO NOTHING;

-- .NET variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('.net', '.NET', 'ecosystem', 'Lowercase variant'),
    ('dotnet', '.NET', 'ecosystem', 'Alternative spelling'),
    ('DotNet', '.NET', 'ecosystem', 'CamelCase alternative'),
    ('.NET Core', '.NET', 'ecosystem', 'Version specific'),
    ('.NET Framework', '.NET', 'ecosystem', 'Version specific')
ON CONFLICT (alias) DO NOTHING;

-- PowerShell variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('powershell', 'PowerShell', 'language', 'Lowercase variant'),
    ('Powershell', 'PowerShell', 'language', 'Title case variant'),
    ('pwsh', 'PowerShell', 'language', 'Common abbreviation')
ON CONFLICT (alias) DO NOTHING;

-- Tableau variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('tableau', 'Tableau', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Snowflake variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('snowflake', 'Snowflake', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- BigQuery variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('bigquery', 'BigQuery', 'ecosystem', 'Lowercase variant'),
    ('Big Query', 'BigQuery', 'ecosystem', 'With space'),
    ('Google BigQuery', 'BigQuery', 'ecosystem', 'Full Google branding')
ON CONFLICT (alias) DO NOTHING;

-- Airflow variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('airflow', 'Airflow', 'ecosystem', 'Lowercase variant'),
    ('Apache Airflow', 'Airflow', 'ecosystem', 'Full Apache branding')
ON CONFLICT (alias) DO NOTHING;

-- Kafka variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('kafka', 'Kafka', 'ecosystem', 'Lowercase variant'),
    ('Apache Kafka', 'Kafka', 'ecosystem', 'Full Apache branding')
ON CONFLICT (alias) DO NOTHING;

-- Excel variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('excel', 'Excel', 'ecosystem', 'Lowercase variant'),
    ('Microsoft Excel', 'Excel', 'ecosystem', 'Full Microsoft branding'),
    ('MS Excel', 'Excel', 'ecosystem', 'Short Microsoft prefix')
ON CONFLICT (alias) DO NOTHING;

-- Git variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('git', 'Git', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Java variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('java', 'Java', 'language', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- DAX variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('dax', 'DAX', 'language', 'Lowercase variant'),
    ('Dax', 'DAX', 'language', 'Title case variant')
ON CONFLICT (alias) DO NOTHING;

-- MATLAB variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('Matlab', 'MATLAB', 'language', 'Title case variant'),
    ('matlab', 'MATLAB', 'language', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- PL/SQL variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('PLSQL', 'PL/SQL', 'language', 'No slash variant'),
    ('plsql', 'PL/SQL', 'language', 'Lowercase no slash'),
    ('PL-SQL', 'PL/SQL', 'language', 'Hyphen variant'),
    ('pl/sql', 'PL/SQL', 'language', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- T-SQL variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('TSQL', 'T-SQL', 'language', 'No hyphen variant'),
    ('tsql', 'T-SQL', 'language', 'Lowercase no hyphen'),
    ('t-sql', 'T-SQL', 'language', 'Lowercase variant'),
    ('Transact-SQL', 'T-SQL', 'language', 'Full name')
ON CONFLICT (alias) DO NOTHING;

-- Node.js variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('NodeJS', 'Node.js', 'ecosystem', 'No dot variant'),
    ('nodejs', 'Node.js', 'ecosystem', 'Lowercase no dot'),
    ('node.js', 'Node.js', 'ecosystem', 'Lowercase variant'),
    ('Node', 'Node.js', 'ecosystem', 'Short name')
ON CONFLICT (alias) DO NOTHING;

-- React variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('react', 'React', 'ecosystem', 'Lowercase variant'),
    ('ReactJS', 'React', 'ecosystem', 'With JS suffix'),
    ('React.js', 'React', 'ecosystem', 'With .js suffix')
ON CONFLICT (alias) DO NOTHING;

-- Angular variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('angular', 'Angular', 'ecosystem', 'Lowercase variant'),
    ('AngularJS', 'Angular', 'ecosystem', 'Legacy version name')
ON CONFLICT (alias) DO NOTHING;

-- MongoDB variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('mongodb', 'MongoDB', 'ecosystem', 'Lowercase variant'),
    ('Mongodb', 'MongoDB', 'ecosystem', 'Title case variant'),
    ('Mongo', 'MongoDB', 'ecosystem', 'Short name')
ON CONFLICT (alias) DO NOTHING;

-- Redis variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('redis', 'Redis', 'ecosystem', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Elasticsearch variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('elasticsearch', 'Elasticsearch', 'ecosystem', 'Lowercase variant'),
    ('ElasticSearch', 'Elasticsearch', 'ecosystem', 'CamelCase variant'),
    ('Elastic Search', 'Elasticsearch', 'ecosystem', 'With space')
ON CONFLICT (alias) DO NOTHING;

-- CUDA variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('cuda', 'CUDA', 'language', 'Lowercase variant'),
    ('Cuda', 'CUDA', 'language', 'Title case variant')
ON CONFLICT (alias) DO NOTHING;

-- Rust variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('rust', 'Rust', 'language', 'Lowercase variant'),
    ('RUST', 'Rust', 'language', 'Uppercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Go variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('go', 'Go', 'language', 'Lowercase variant'),
    ('Golang', 'Go', 'language', 'Alternative name'),
    ('golang', 'Go', 'language', 'Lowercase alternative')
ON CONFLICT (alias) DO NOTHING;

-- Scala variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('scala', 'Scala', 'language', 'Lowercase variant')
ON CONFLICT (alias) DO NOTHING;

-- Bash variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('bash', 'Bash', 'language', 'Lowercase variant'),
    ('BASH', 'Bash', 'language', 'Uppercase variant')
ON CONFLICT (alias) DO NOTHING;

-- S/4HANA variations
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes) VALUES
    ('S/4HANA', 'S/4 HANA', 'ecosystem', 'No space variant'),
    ('S4HANA', 'S/4 HANA', 'ecosystem', 'No slash no space'),
    ('S/4 Hana', 'S/4 HANA', 'ecosystem', 'Lowercase HANA'),
    ('S4 Hana', 'S/4 HANA', 'ecosystem', 'No slash lowercase'),
    ('SAP S/4HANA', 'S/4 HANA', 'ecosystem', 'With SAP prefix')
ON CONFLICT (alias) DO NOTHING;
