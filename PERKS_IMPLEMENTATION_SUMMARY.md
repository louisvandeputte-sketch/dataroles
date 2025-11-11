# ✅ Perks Feature - Implementation Complete

## Status: READY (Not Yet Executed)

Alle code en database schema zijn voorbereid. Wacht op:
1. Database migratie uitvoeren
2. LLM prompt v15 activeren in OpenAI

## Wat Is Geïmplementeerd

### 1. Database Schema ✅

**File:** `database/migrations/032_add_perks_to_enrichment.sql`

```sql
ALTER TABLE llm_enrichment
ADD COLUMN perks JSONB DEFAULT NULL;

CREATE INDEX idx_llm_enrichment_perks ON llm_enrichment USING GIN (perks);
```

**Structuur (v15 Final):**
```json
{
  "perks": [
    {"key": "remote_policy", "found": true},
    {"key": "salary_range", "found": true},
    {"key": "company_car", "found": false},
    {"key": "hospitalization_insurance", "found": true},
    {"key": "training_budget", "found": false},
    {"key": "team_events", "found": true}
  ]
}
```

**Labels stored in i18n:**
```json
{
  "labels": {
    "nl": {
      "perks": [
        {"key": "remote_policy", "label": "Hybride werken"},
        {"key": "salary_range", "label": "€3500-€4200/maand"},
        {"key": "hospitalization_insurance", "label": "Hospitalisatieverzekering"},
        {"key": "team_events", "label": "Team events"}
      ]
    }
  }
}
```

### 2. LLM Integration ✅

**File:** `ingestion/llm_enrichment.py`

**Changes:**
- ✅ Prompt version: v14 → **v15**
- ✅ Extract `perks` array from LLM response
- ✅ Save to database as JSONB
- ✅ Retry logic compatible

**Code:**
```python
# Extract perks
perks = enrichment_data.get("perks", [])

# Save to DB
db_data = {
    "perks": json.dumps(perks) if perks else None,
    # ... other fields
}
```

### 3. Schema Documentation ✅

**File:** `DATABASE_SCHEMA.json`

```json
"perks": {
  "type": "JSONB",
  "nullable": true,
  "description": "Array of job perks with multilingual labels..."
}
```

### 4. Feature Documentation ✅

**Files:**
- `PERKS_FEATURE.md` - Complete feature documentation
- `PERKS_IMPLEMENTATION_SUMMARY.md` - This file
- `RUN_MIGRATION_032.md` - Migration instructions

## Next Steps (Manual)

### Step 1: Run Database Migration

**Go to Supabase Dashboard → SQL Editor:**

```sql
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS perks JSONB DEFAULT NULL;

COMMENT ON COLUMN llm_enrichment.perks IS 'Array of job perks with multilingual labels';

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perks 
ON llm_enrichment USING GIN (perks);
```

**Verify:**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'llm_enrichment' 
AND column_name = 'perks';
```

### Step 2: Update LLM Prompt (OpenAI)

**In OpenAI Responses Dashboard:**

1. Go to prompt: `pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88`
2. Create new version: **v15**
3. Add perks detection logic:

```
Task: Analyseer de vacaturetekst en detecteer deze perks (in vaste volgorde):
- Remote policy
- Salarisrange
- Bedrijfswagen
- Hospitalisatieverzekering
- Opleidingsbudget
- Team events

Vaste vertalingen (verplicht):
- Remote policy: NL="Remote", EN="Remote", FR="Télétravail"
- Bedrijfswagen: NL="Wagen", EN="Car", FR="Voiture"
- Hospitalisatie: NL="Hospitalisatie", EN="Health", FR="Santé"
- Opleiding: NL="Opleiding", EN="Training", FR="Formation"
- Team: NL="Team", EN="Team", FR="Équipe"

Salarisrange: gebruik echte gevonden range (max 2-4 tokens)
Voorbeelden: "€3500–€4200/maand", "€70k–€85k/year", "€18/uur"

Output JSON:
{
  "perks": [
    { "key": "remote_policy", "found": false, "nl": null, "en": null, "fr": null },
    { "key": "salary_range", "found": false, "nl": null, "en": null, "fr": null },
    { "key": "company_car", "found": false, "nl": null, "en": null, "fr": null },
    { "key": "hospitalization_insurance", "found": false, "nl": null, "en": null, "fr": null },
    { "key": "training_budget", "found": false, "nl": null, "en": null, "fr": null },
    { "key": "team_events", "found": false, "nl": null, "en": null, "fr": null }
  ]
}

Detectieregels:
- Found = true als perk expliciet in tekst staat
- Bij found=true: vul NL/EN/FR in met vaste vertalingen (of echte range bij salary)
- Bij found=false: NL/EN/FR = null
```

4. Test met sample job descriptions
5. Publish v15

### Step 3: Test Enrichment

**After migration + prompt update:**

```bash
# Test single job
python -c "
from ingestion.llm_enrichment import process_job_enrichment
result = process_job_enrichment('existing-job-id')
print('Perks:', result.get('data', {}).get('perks'))
"
```

**Expected output:**
```python
Perks: [
  {'key': 'remote_policy', 'found': True, 'nl': 'Remote', 'en': 'Remote', 'fr': 'Télétravail'},
  {'key': 'salary_range', 'found': True, 'nl': '€3500–€4200/maand', ...},
  # etc.
]
```

### Step 4: Enrich Jobs

**Option A: New Jobs**
- Nieuwe jobs worden automatisch verrijkt met perks (v15)

**Option B: Re-enrich Existing Jobs**
```bash
# In UI: Click "Enrich All" (will use v15)
# Or via Python:
python -c "
from ingestion.llm_enrichment import batch_enrich_jobs
from database.client import db

# Get first 50 enriched jobs
jobs = db.client.table('llm_enrichment')\
    .select('job_posting_id')\
    .not_.is_('enrichment_completed_at', 'null')\
    .limit(50)\
    .execute()

job_ids = [j['job_posting_id'] for j in jobs.data]
batch_enrich_jobs(job_ids, batch_size=50)
"
```

## Files Changed

```
✅ database/migrations/032_add_perks_to_enrichment.sql
✅ ingestion/llm_enrichment.py (v14 → v15, perks extraction)
✅ DATABASE_SCHEMA.json (perks field added)
✅ PERKS_FEATURE.md (complete documentation)
✅ PERKS_IMPLEMENTATION_SUMMARY.md (this file)
✅ RUN_MIGRATION_032.md (migration instructions)
```

## Verification Checklist

After running migration and updating prompt:

- [ ] Database column `perks` exists (JSONB type)
- [ ] GIN index created on `perks` column
- [ ] LLM prompt version is v15
- [ ] Test enrichment returns perks array
- [ ] Perks have correct structure (key, found, nl, en, fr)
- [ ] Fixed translations are used (not dynamic)
- [ ] Salary range is dynamic (actual found range)
- [ ] Not found perks have `found: false` and `null` values

## Query Examples

### Find Jobs with Remote Policy

```sql
SELECT jp.title, jp.companies.name
FROM job_postings jp
JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE le.perks @> '[{"key": "remote_policy", "found": true}]';
```

### Find Jobs with Salary Range

```sql
SELECT jp.title, 
       jsonb_array_elements(le.perks)->>'nl' as salary_nl
FROM job_postings jp
JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE le.perks @> '[{"key": "salary_range", "found": true}]';
```

### Count Jobs by Perk

```python
from database.client import db

perks_count = {}
for perk_key in ['remote_policy', 'salary_range', 'company_car', 
                  'hospitalization_insurance', 'training_budget', 'team_events']:
    count = db.client.table("llm_enrichment")\
        .select("job_posting_id", count="exact")\
        .filter("perks", "cs", f'[{{"key": "{perk_key}", "found": true}}]')\
        .execute()
    perks_count[perk_key] = count.count

print(perks_count)
# Output: {'remote_policy': 234, 'salary_range': 156, ...}
```

## Rollback Plan

If issues occur:

```sql
-- Remove column
ALTER TABLE llm_enrichment DROP COLUMN IF EXISTS perks;

-- Revert code
git checkout HEAD -- ingestion/llm_enrichment.py

-- In OpenAI: revert to prompt v14
```

## Support

**Migration issues:**
- Check Supabase SQL editor for errors
- Verify table permissions
- Check column doesn't already exist

**LLM issues:**
- Verify prompt version is v15
- Check OpenAI API logs
- Test with simple job description

**Data issues:**
- Check JSON structure matches spec
- Verify translations are correct
- Check `found` boolean values

## Summary

✅ **Code Ready:** All code changes implemented
✅ **Schema Ready:** Migration SQL prepared
✅ **Docs Ready:** Complete documentation
⏳ **Pending:** Database migration execution
⏳ **Pending:** LLM prompt v15 activation

**Estimated time to complete:** 15 minutes
1. Run migration (2 min)
2. Update LLM prompt (10 min)
3. Test enrichment (3 min)

**Ready to proceed when you are!** 🚀
