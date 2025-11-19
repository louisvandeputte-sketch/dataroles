-- Migration 060: Create vague_locations_config table
-- Date: 2025-11-19
-- Description: Configuration table to maintain list of vague location patterns
--              that should use company location override

-- Create table for vague location patterns
CREATE TABLE IF NOT EXISTS vague_locations_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comment
COMMENT ON TABLE vague_locations_config IS 'Configuration table for vague location patterns. When a job location matches one of these patterns, the system will try to use the company location override from company_master_data.locatie_belgie';

-- Insert default vague location patterns
INSERT INTO vague_locations_config (pattern, description, is_active) VALUES
    ('Flemish Region', 'Vague region-level location in Flanders', TRUE),
    ('Walloon Region', 'Vague region-level location in Wallonia', TRUE),
    ('Brussels-Capital Region', 'Vague region-level location in Brussels', TRUE),
    ('Belgium', 'Country-level location (too vague)', TRUE),
    ('België', 'Country-level location in Dutch (too vague)', TRUE)
ON CONFLICT (pattern) DO NOTHING;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_vague_locations_active ON vague_locations_config(is_active) WHERE is_active = TRUE;

-- Add RLS policies (optional - for security)
ALTER TABLE vague_locations_config ENABLE ROW LEVEL SECURITY;

-- Allow read access to all authenticated users
CREATE POLICY "Allow read access to vague_locations_config" 
    ON vague_locations_config FOR SELECT 
    USING (true);

-- Only service role can modify (you can adjust this)
CREATE POLICY "Allow service role to manage vague_locations_config" 
    ON vague_locations_config FOR ALL 
    USING (auth.role() = 'service_role');
