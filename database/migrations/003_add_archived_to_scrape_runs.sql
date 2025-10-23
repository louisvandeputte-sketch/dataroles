-- Add archived column to scrape_runs table
ALTER TABLE scrape_runs 
ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_scrape_runs_archived ON scrape_runs(archived);

-- Comment
COMMENT ON COLUMN scrape_runs.archived IS 'Whether this run has been archived by the user';
