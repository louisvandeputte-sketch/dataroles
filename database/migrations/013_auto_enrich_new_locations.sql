-- Migration: Auto-enrich new locations trigger
-- Automatically marks new location records for enrichment
-- Date: 2025-10-27

-- Create function to mark new locations for enrichment
CREATE OR REPLACE FUNCTION mark_location_for_enrichment()
RETURNS TRIGGER AS $$
BEGIN
    -- Only mark for enrichment if not already enriched
    IF NEW.ai_enriched IS NULL OR NEW.ai_enriched = FALSE THEN
        NEW.ai_enriched := FALSE;
        NEW.ai_enriched_at := NULL;
        NEW.ai_enrichment_error := NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on INSERT
CREATE TRIGGER trigger_mark_location_for_enrichment
    BEFORE INSERT ON locations
    FOR EACH ROW
    EXECUTE FUNCTION mark_location_for_enrichment();

-- Add comment
COMMENT ON FUNCTION mark_location_for_enrichment() IS 'Automatically marks new location records for AI enrichment';
COMMENT ON TRIGGER trigger_mark_location_for_enrichment ON locations IS 'Ensures new locations are flagged for enrichment';
