-- Migration 085: Clean up invalid aantal_werknemers values and add trigger
-- Date: 2025-12-17
-- Description: Remove placeholder/invalid values and prevent them in the future

-- Step 1: Clean up existing invalid values
UPDATE company_master_data
SET aantal_werknemers = NULL
WHERE 
    aantal_werknemers IS NOT NULL
    AND (
        -- Placeholder values
        aantal_werknemers ILIKE '%[aantal]%'
        OR aantal_werknemers ILIKE '%[number]%'
        OR aantal_werknemers = '[270]'  -- Bracketed numbers
        OR aantal_werknemers ~ '^\[\d+\]$'  -- Any bracketed number pattern
        -- Unknown/not found values
        OR aantal_werknemers ILIKE 'niet gevonden'
        OR aantal_werknemers ILIKE 'onbekend'
        OR aantal_werknemers ILIKE 'unknown'
        OR aantal_werknemers ILIKE 'not found'
        OR aantal_werknemers ILIKE 'n/a'
        OR aantal_werknemers ILIKE 'na'
        -- Empty or whitespace only
        OR TRIM(aantal_werknemers) = ''
    );

-- Step 2: Create function to validate and clean aantal_werknemers
CREATE OR REPLACE FUNCTION validate_aantal_werknemers()
RETURNS TRIGGER AS $$
BEGIN
    -- If aantal_werknemers is being set
    IF NEW.aantal_werknemers IS NOT NULL THEN
        -- Check for invalid patterns
        IF NEW.aantal_werknemers ILIKE '%[aantal]%'
            OR NEW.aantal_werknemers ILIKE '%[number]%'
            OR NEW.aantal_werknemers ~ '^\[\d+\]$'  -- Bracketed numbers
            OR NEW.aantal_werknemers ILIKE 'niet gevonden'
            OR NEW.aantal_werknemers ILIKE 'onbekend'
            OR NEW.aantal_werknemers ILIKE 'unknown'
            OR NEW.aantal_werknemers ILIKE 'not found'
            OR NEW.aantal_werknemers ILIKE 'n/a'
            OR NEW.aantal_werknemers ILIKE 'na'
            OR TRIM(NEW.aantal_werknemers) = ''
        THEN
            -- Set to NULL instead of storing invalid value
            NEW.aantal_werknemers := NULL;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create trigger on company_master_data
DROP TRIGGER IF EXISTS trigger_validate_aantal_werknemers ON company_master_data;

CREATE TRIGGER trigger_validate_aantal_werknemers
    BEFORE INSERT OR UPDATE OF aantal_werknemers
    ON company_master_data
    FOR EACH ROW
    EXECUTE FUNCTION validate_aantal_werknemers();

-- Add comment
COMMENT ON FUNCTION validate_aantal_werknemers() IS 
'Validates aantal_werknemers field and sets to NULL if invalid placeholder or unknown values are detected.
Invalid patterns include: [aantal], [number], bracketed numbers, "niet gevonden", "onbekend", "unknown", etc.';

COMMENT ON TRIGGER trigger_validate_aantal_werknemers ON company_master_data IS 
'Automatically cleans invalid aantal_werknemers values before insert/update.';
