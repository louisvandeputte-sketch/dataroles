-- Migration 033: Add relevance_score to programming_languages and ecosystems
-- Date: 2025-11-10
-- Description: Add AI-scored relevance (0-100) for data professionals

-- Add relevance_score to programming_languages
ALTER TABLE programming_languages
ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT NULL;

COMMENT ON COLUMN programming_languages.relevance_score IS 
'AI-scored relevance (0-100) for data professionals. 0=niche/irrelevant, 100=essential/universal';

-- Add relevance_score to ecosystems
ALTER TABLE ecosystems
ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT NULL;

COMMENT ON COLUMN ecosystems.relevance_score IS 
'AI-scored relevance (0-100) for data professionals. 0=niche/irrelevant, 100=essential/universal';

-- Add indexes for sorting by relevance
CREATE INDEX IF NOT EXISTS idx_programming_languages_relevance 
ON programming_languages(relevance_score DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_ecosystems_relevance 
ON ecosystems(relevance_score DESC NULLS LAST);
