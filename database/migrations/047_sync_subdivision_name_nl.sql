-- Migration 047: Sync subdivision_name_nl with subdivision_name
-- Date: 2025-11-17
-- Description: Ensure subdivision_name_nl always equals subdivision_name

-- Step 1: Backfill existing NULL values
UPDATE locations
SET subdivision_name_nl = subdivision_name
WHERE subdivision_name_nl IS NULL
  AND subdivision_name IS NOT NULL;

-- Step 2: Create trigger function to keep subdivision_name_nl in sync
CREATE OR REPLACE FUNCTION sync_subdivision_name_nl()
RETURNS TRIGGER AS $$
BEGIN
    -- Always set subdivision_name_nl to match subdivision_name
    NEW.subdivision_name_nl := NEW.subdivision_name;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create trigger on INSERT and UPDATE
DROP TRIGGER IF EXISTS trigger_sync_subdivision_name_nl ON locations;

CREATE TRIGGER trigger_sync_subdivision_name_nl
    BEFORE INSERT OR UPDATE OF subdivision_name
    ON locations
    FOR EACH ROW
    EXECUTE FUNCTION sync_subdivision_name_nl();

-- Add comment
COMMENT ON FUNCTION sync_subdivision_name_nl() IS 
'Automatically syncs subdivision_name_nl with subdivision_name on INSERT/UPDATE';

COMMENT ON TRIGGER trigger_sync_subdivision_name_nl ON locations IS
'Ensures subdivision_name_nl always equals subdivision_name';
