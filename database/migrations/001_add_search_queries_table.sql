-- Migration: Add search_queries table and update scrape_runs
-- This creates a proper queries table with scheduling support

-- Create search_queries table
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_query TEXT NOT NULL,
    location_query TEXT NOT NULL,
    lookback_days INTEGER DEFAULT 7,
    is_active BOOLEAN DEFAULT true,
    
    -- Scheduling fields
    schedule_enabled BOOLEAN DEFAULT false,
    schedule_type TEXT,  -- 'daily', 'interval', 'weekly'
    schedule_time TIME,  -- For daily (e.g., 09:00)
    schedule_interval_hours INTEGER,  -- For interval (e.g., 6)
    schedule_days_of_week INTEGER[],  -- For weekly (0=Sunday, 6=Saturday)
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint on query+location combination
    UNIQUE(search_query, location_query)
);

-- Add indexes
CREATE INDEX idx_search_queries_active ON search_queries(is_active);
CREATE INDEX idx_search_queries_scheduled ON search_queries(schedule_enabled, next_run_at);
CREATE INDEX idx_search_queries_next_run ON search_queries(next_run_at) WHERE schedule_enabled = true;

-- Add trigger_type to scrape_runs
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS trigger_type TEXT DEFAULT 'manual';
-- Values: 'manual', 'scheduled', 'api'

-- Add search_query_id to scrape_runs (optional foreign key)
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS search_query_id UUID REFERENCES search_queries(id) ON DELETE SET NULL;

-- Create index on trigger_type
CREATE INDEX IF NOT EXISTS idx_scrape_runs_trigger_type ON scrape_runs(trigger_type);

-- Add updated_at trigger to search_queries
CREATE TRIGGER update_search_queries_updated_at
    BEFORE UPDATE ON search_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE search_queries IS 'Stored search query configurations with optional scheduling';
COMMENT ON COLUMN scrape_runs.trigger_type IS 'How the scrape was triggered: manual, scheduled, or api';
