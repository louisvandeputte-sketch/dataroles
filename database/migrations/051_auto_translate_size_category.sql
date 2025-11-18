-- Migration 051: Auto-translate size_category to category_nl/en/fr
-- Date: 2025-11-18
-- Description: Create trigger to automatically set category translations when size_category is updated

-- Create function to translate size_category to all languages
CREATE OR REPLACE FUNCTION translate_size_category()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if size_category has changed or is being set
    IF NEW.size_category IS DISTINCT FROM OLD.size_category OR (TG_OP = 'INSERT' AND NEW.size_category IS NOT NULL) THEN
        -- Set translations based on size_category enum value (Title Case)
        CASE NEW.size_category
            WHEN 'startup' THEN
                NEW.category_nl := 'Startup';
                NEW.category_en := 'Startup';
                NEW.category_fr := 'Startup';
            
            WHEN 'scaleup' THEN
                NEW.category_nl := 'Scale-up';
                NEW.category_en := 'Scale-up';
                NEW.category_fr := 'Scale-up';
            
            WHEN 'sme' THEN
                NEW.category_nl := 'KMO';
                NEW.category_en := 'SME';
                NEW.category_fr := 'PME';
            
            WHEN 'established_enterprise' THEN
                NEW.category_nl := 'Gevestigde Onderneming';
                NEW.category_en := 'Established Enterprise';
                NEW.category_fr := 'Entreprise Établie';
            
            WHEN 'corporate' THEN
                NEW.category_nl := 'Corporate';
                NEW.category_en := 'Corporate';
                NEW.category_fr := 'Corporate';
            
            WHEN 'public_company' THEN
                NEW.category_nl := 'Beursgenoteerd Bedrijf';
                NEW.category_en := 'Public Company';
                NEW.category_fr := 'Société Cotée';
            
            WHEN 'government' THEN
                NEW.category_nl := 'Overheid';
                NEW.category_en := 'Government';
                NEW.category_fr := 'Gouvernement';
            
            WHEN 'unknown' THEN
                NEW.category_nl := 'Onbekend';
                NEW.category_en := 'Unknown';
                NEW.category_fr := 'Inconnu';
            
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
