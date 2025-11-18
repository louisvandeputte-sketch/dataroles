-- Migration 051: Auto-translate size_category to category_nl/en/fr
-- Date: 2025-11-18
-- Description: Create trigger to automatically set category translations when size_category is updated

-- Create function to translate size_category to all languages
CREATE OR REPLACE FUNCTION translate_size_category()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if size_category has changed or is being set
    IF NEW.size_category IS DISTINCT FROM OLD.size_category OR (TG_OP = 'INSERT' AND NEW.size_category IS NOT NULL) THEN
        -- Set translations based on size_category enum value
        CASE NEW.size_category
            WHEN 'startup' THEN
                NEW.category_nl := 'startup';
                NEW.category_en := 'startup';
                NEW.category_fr := 'startup';
            
            WHEN 'scaleup' THEN
                NEW.category_nl := 'scaleup';
                NEW.category_en := 'scaleup';
                NEW.category_fr := 'scaleup';
            
            WHEN 'sme' THEN
                NEW.category_nl := 'kmo';
                NEW.category_en := 'sme';
                NEW.category_fr := 'pme';
            
            WHEN 'established_enterprise' THEN
                NEW.category_nl := 'gevestigde onderneming';
                NEW.category_en := 'established enterprise';
                NEW.category_fr := 'entreprise établie';
            
            WHEN 'corporate' THEN
                NEW.category_nl := 'corporate';
                NEW.category_en := 'corporate';
                NEW.category_fr := 'corporate';
            
            WHEN 'public_company' THEN
                NEW.category_nl := 'beursgenoteerd bedrijf';
                NEW.category_en := 'public company';
                NEW.category_fr := 'société cotée';
            
            WHEN 'government' THEN
                NEW.category_nl := 'overheid';
                NEW.category_en := 'government';
                NEW.category_fr := 'gouvernement';
            
            WHEN 'unknown' THEN
                NEW.category_nl := 'onbekend';
                NEW.category_en := 'unknown';
                NEW.category_fr := 'inconnu';
            
            ELSE
                -- If size_category is NULL or invalid, clear translations
                NEW.category_nl := NULL;
                NEW.category_en := NULL;
                NEW.category_fr := NULL;
        END CASE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on company_master_data
DROP TRIGGER IF EXISTS trigger_translate_size_category ON company_master_data;

CREATE TRIGGER trigger_translate_size_category
    BEFORE INSERT OR UPDATE OF size_category
    ON company_master_data
    FOR EACH ROW
    EXECUTE FUNCTION translate_size_category();

-- Update existing records to have correct translations
UPDATE company_master_data
SET size_category = size_category  -- This will trigger the function
WHERE size_category IS NOT NULL;

-- Add comments
COMMENT ON FUNCTION translate_size_category() IS 
'Automatically translates size_category enum to category_nl, category_en, category_fr. 
Triggered on INSERT or UPDATE of size_category field.';

COMMENT ON TRIGGER trigger_translate_size_category ON company_master_data IS 
'Automatically sets category translations (NL/EN/FR) when size_category is changed.';
