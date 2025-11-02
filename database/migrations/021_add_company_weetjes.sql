-- Migration: Add company weetjes (factlets) field
-- Stores multilingual factlets with category, source, confidence, and verification date
-- Date: 2025-11-01

-- Add weetjes JSONB column to company_master_data
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS weetjes JSONB;

-- Add sector_nl and sector_fr for multilingual sector support (sector_en already exists)
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS sector_nl TEXT,
ADD COLUMN IF NOT EXISTS sector_fr TEXT;

-- Add index for JSONB queries on weetjes
CREATE INDEX IF NOT EXISTS idx_company_master_data_weetjes 
ON company_master_data USING GIN (weetjes);

-- Add index for sector fields
CREATE INDEX IF NOT EXISTS idx_company_master_data_sector_nl 
ON company_master_data(sector_nl) 
WHERE sector_nl IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_master_data_sector_fr 
ON company_master_data(sector_fr) 
WHERE sector_fr IS NOT NULL;

-- Add comments
COMMENT ON COLUMN company_master_data.weetjes IS 'Array of 1-3 multilingual factlets (weetjes) with category, texts (EN/NL/FR), source, confidence, and verification date (AI enriched, prompt v11+)';
COMMENT ON COLUMN company_master_data.sector_nl IS 'Company sector/industry in Dutch (AI enriched)';
COMMENT ON COLUMN company_master_data.sector_fr IS 'Company sector/industry in French (AI enriched)';

-- Example weetjes structure:
-- [
--   {
--     "category": "global_reach",
--     "text_en": "Active in 12 European countries with regional hubs in Belgium, France and Germany.",
--     "text_nl": "Actief in 12 Europese landen met regionale hubs in België, Frankrijk en Duitsland.",
--     "text_fr": "Actif dans 12 pays européens avec des hubs régionaux en Belgique, France et Allemagne.",
--     "source": "https://example.com/about",
--     "confidence": 0.92,
--     "date_verified": "2025-11-01"
--   },
--   {
--     "category": "recent_award",
--     "text_en": "Won the 2024 Digital Innovation Award for data automation.",
--     "text_nl": "Wint de Digital Innovation Award 2024 voor data-automatisatie.",
--     "text_fr": "Lauréat du Digital Innovation Award 2024 pour l'automatisation des données.",
--     "source": "https://example.com/news",
--     "confidence": 0.88,
--     "date_verified": "2025-11-01"
--   }
-- ]
