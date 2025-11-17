# Migration 047: Subdivision Name NL Sync

## Overview
This migration ensures that `subdivision_name_nl` in the `locations` table always equals `subdivision_name`.

## Problem
- `subdivision_name` contains Dutch province names (e.g., "Vlaams-Brabant")
- `subdivision_name_nl` should be identical but was NULL for all 286 locations
- Frontend needs `subdivision_name_nl` for filtering

## Solution

### 1. Backfill Existing Data
```sql
UPDATE locations
SET subdivision_name_nl = subdivision_name
WHERE subdivision_name_nl IS NULL
  AND subdivision_name IS NOT NULL;
```

### 2. Automatic Sync with Trigger
A database trigger automatically keeps `subdivision_name_nl` in sync:

```sql
CREATE TRIGGER trigger_sync_subdivision_name_nl
    BEFORE INSERT OR UPDATE OF subdivision_name
    ON locations
    FOR EACH ROW
    EXECUTE FUNCTION sync_subdivision_name_nl();
```

**How it works:**
- On INSERT: `subdivision_name_nl` is automatically set to `subdivision_name`
- On UPDATE of `subdivision_name`: `subdivision_name_nl` is automatically updated
- No manual intervention needed

## Execution

### On Railway (Production)
1. Go to Railway dashboard
2. Open PostgreSQL database
3. Click "Query" tab
4. Copy and paste contents of `database/migrations/047_sync_subdivision_name_nl.sql`
5. Execute

### Locally (Development)
```bash
# Run migration via psql
psql $DATABASE_URL -f database/migrations/047_sync_subdivision_name_nl.sql

# Or via Python test script
python test_subdivision_sync.py
```

## Verification

### Check Sync Status
```sql
-- Count NULL subdivision_name_nl
SELECT COUNT(*) 
FROM locations 
WHERE subdivision_name_nl IS NULL;
-- Expected: 0

-- Sample data
SELECT subdivision_name, subdivision_name_nl 
FROM locations 
WHERE subdivision_name IS NOT NULL 
LIMIT 10;
-- Expected: Both columns should match
```

### Test Trigger
```sql
-- Insert test location
INSERT INTO locations (city, country_code, subdivision_name)
VALUES ('Test City', 'BE', 'Test Province');

-- Check if subdivision_name_nl was auto-set
SELECT subdivision_name, subdivision_name_nl 
FROM locations 
WHERE city = 'Test City';
-- Expected: subdivision_name_nl = 'Test Province'

-- Update test
UPDATE locations 
SET subdivision_name = 'Updated Province'
WHERE city = 'Test City';

-- Check if subdivision_name_nl was auto-updated
SELECT subdivision_name, subdivision_name_nl 
FROM locations 
WHERE city = 'Test City';
-- Expected: subdivision_name_nl = 'Updated Province'

-- Cleanup
DELETE FROM locations WHERE city = 'Test City';
```

## Impact

### Before Migration
```
subdivision_name: "Vlaams-Brabant"
subdivision_name_nl: NULL
subdivision_name_en: "Flemish Brabant"
```

### After Migration
```
subdivision_name: "Vlaams-Brabant"
subdivision_name_nl: "Vlaams-Brabant"  ← Auto-synced
subdivision_name_en: "Flemish Brabant"
```

## Benefits
1. ✅ **Consistency**: `subdivision_name_nl` always matches `subdivision_name`
2. ✅ **Automatic**: Trigger handles sync on INSERT/UPDATE
3. ✅ **No Manual Work**: Developers don't need to set both fields
4. ✅ **Frontend Ready**: API can use `subdivision_name_nl` for filtering

## Related Files
- Migration: `database/migrations/047_sync_subdivision_name_nl.sql`
- Test Script: `test_subdivision_sync.py`
- API Filter: `subdivision_name_en` (for English province names)

## Notes
- This migration only affects the `locations` table
- The trigger runs BEFORE INSERT/UPDATE, so it's very fast
- `subdivision_name_en` and `subdivision_name_fr` remain independent (English/French translations)
- The sync is one-way: `subdivision_name` → `subdivision_name_nl`
