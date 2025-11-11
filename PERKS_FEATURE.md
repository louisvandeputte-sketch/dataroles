# Perks Feature - Job Enrichment v15

## Overzicht

Nieuwe feature voor het detecteren en opslaan van job perks (voordelen) in meertalig formaat.

## Perks Types (v15 Final)

| Perk Key | Detection | Label Storage |
|----------|-----------|---------------|
| `remote_policy` | Remote/hybrid/télétravail mentioned as perk | i18n |
| `salary_range` | Concrete salary/range mentioned | i18n |
| `company_car` | Company car/allowance mentioned | i18n |
| `hospitalization_insurance` | Health/medical insurance mentioned | i18n |
| `training_budget` | Training/courses/learning budget mentioned | i18n |
| `team_events` | Team activities/events/socials mentioned | i18n |

**Structure:**
- `perks` array: Only `{key, found}` - no labels
- Labels stored in: `labels.nl.perks`, `labels.en.perks`, `labels.fr.perks`
- Consistent with other i18n fields (summaries, role types, etc.)

## Data Structuur

### Database Schema

```sql
-- llm_enrichment table
perks JSONB  -- Array of perk objects
```

### JSON Format (v15 Final)

**Perks array (stored in `perks` column):**
```json
{
  "perks": [
    { "key": "remote_policy", "found": true },
    { "key": "salary_range", "found": true },
    { "key": "company_car", "found": false },
    { "key": "hospitalization_insurance", "found": true },
    { "key": "training_budget", "found": false },
    { "key": "team_events", "found": true }
  ]
}
```

**Perk labels (stored in `labels` column via i18n):**
```json
{
  "labels": {
    "nl": {
      "perks": [
        { "key": "remote_policy", "label": "Hybride werken" },
        { "key": "salary_range", "label": "€3500-€4200/maand" },
        { "key": "hospitalization_insurance", "label": "Hospitalisatieverzekering" },
        { "key": "team_events", "label": "Team events" }
      ]
    },
    "en": {
      "perks": [
        { "key": "remote_policy", "label": "Hybrid work" },
        { "key": "salary_range", "label": "€3500-€4200/month" },
        { "key": "hospitalization_insurance", "label": "Health insurance" },
        { "key": "team_events", "label": "Team events" }
      ]
    },
    "fr": {
      "perks": [
        { "key": "remote_policy", "label": "Travail hybride" },
        { "key": "salary_range", "label": "€3500-€4200/mois" },
        { "key": "hospitalization_insurance", "label": "Assurance santé" },
        { "key": "team_events", "label": "Événements d'équipe" }
      ]
    }
  }
}
```

**Note:** Only perks with `found: true` have labels in i18n. Perks with `found: false` have `label: null`.

## LLM Prompt Requirements (v15)

### Input
Job description text (full_description_text)

### Output
JSON met perks array zoals hierboven

### Detectie Regels (v15 Final)

**Perks Array:**
- Always output exactly 6 perks in fixed order
- Each perk: `{key: string, found: boolean}`
- No labels in perks array

**Label Extraction (for i18n):**
- Extract short descriptive label from posting text (1-4 words)
- Use language of posting (Dutch if NL, French if FR)
- For salary: include numeric range and unit
- For other perks: use most common/clear term
- Store in `labels.nl.perks`, `labels.en.perks`, `labels.fr.perks`

**Examples:**
- Remote: "Hybride werken", "Remote", "Thuiswerk 2 dagen/week"
- Salary: "€3500-€4200/maand", "€50.000-€70.000/jaar"
- Car: "Bedrijfswagen", "Firmawagen", "Company car"
- Health: "Hospitalisatieverzekering", "Ziekteverzekering"
- Training: "Opleidingsbudget", "Training", "Ontwikkeling"
- Team: "Team events", "Teamactiviteiten", "Bedrijfsfeesten"

**Not Found:**
- `found: false` in perks array
- `label: null` in all i18n.*.perks arrays

## Implementation

### Files Changed

```
✅ database/migrations/032_add_perks_to_enrichment.sql
✅ ingestion/llm_enrichment.py (v14 → v15)
✅ DATABASE_SCHEMA.json
✅ PERKS_FEATURE.md (this file)
```

### Code Changes

#### 1. LLM Enrichment (`ingestion/llm_enrichment.py`)

```python
# Prompt version updated
PROMPT_VERSION = "15"  # Was: "14"

# Extract perks from LLM response
perks = enrichment_data.get("perks", [])

# Save to database
db_data = {
    # ... other fields ...
    "perks": json.dumps(perks) if perks else None,
}
```

#### 2. Database Migration

```sql
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS perks JSONB DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perks 
ON llm_enrichment USING GIN (perks);
```

## Usage Examples

### Query Jobs with Specific Perks

```sql
-- Jobs with remote policy
SELECT jp.title, le.perks
FROM job_postings jp
JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE le.perks @> '[{"key": "remote_policy", "found": true}]';

-- Jobs with salary range
SELECT jp.title, 
       (SELECT jsonb_array_elements(le.perks) 
        WHERE jsonb_array_elements->>'key' = 'salary_range' 
        AND jsonb_array_elements->>'found' = 'true') as salary
FROM job_postings jp
JOIN llm_enrichment le ON jp.id = le.job_posting_id;

-- Jobs with company car
SELECT jp.title, le.perks
FROM job_postings jp
JOIN llm_enrichment le ON jp.id = le.job_posting_id
WHERE le.perks @> '[{"key": "company_car", "found": true}]';
```

### Python Access

```python
from database.client import db

# Get job with perks
job = db.client.table("job_postings")\
    .select("*, llm_enrichment(perks)")\
    .eq("id", job_id)\
    .single()\
    .execute()

perks = job.data["llm_enrichment"]["perks"]

# Filter found perks
found_perks = [p for p in perks if p["found"]]

# Get salary range
salary = next((p for p in perks if p["key"] == "salary_range" and p["found"]), None)
if salary:
    print(f"Salary (NL): {salary['nl']}")
    print(f"Salary (EN): {salary['en']}")
    print(f"Salary (FR): {salary['fr']}")
```

### UI Display (Example)

```javascript
// Get perks for display
const perks = job.llm_enrichment?.perks || [];
const foundPerks = perks.filter(p => p.found);

// Display in current language (e.g., 'nl')
const lang = 'nl';
foundPerks.forEach(perk => {
    console.log(perk[lang]);  // "Remote", "€3500–€4200/maand", etc.
});
```

## Migration Steps

### 1. Run Database Migration

Go to Supabase Dashboard → SQL Editor:

```sql
ALTER TABLE llm_enrichment
ADD COLUMN IF NOT EXISTS perks JSONB DEFAULT NULL;

COMMENT ON COLUMN llm_enrichment.perks IS 'Array of job perks with multilingual labels';

CREATE INDEX IF NOT EXISTS idx_llm_enrichment_perks 
ON llm_enrichment USING GIN (perks);
```

### 2. Verify Column

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'llm_enrichment' 
AND column_name = 'perks';
```

Expected:
```
column_name | data_type
------------|----------
perks       | jsonb
```

### 3. Update LLM Prompt (OpenAI)

In OpenAI Responses dashboard:
- Create new version (v15) of prompt
- Add perks detection logic
- Test with sample job descriptions

### 4. Test Enrichment

```bash
# Test single job enrichment
python -c "
from ingestion.llm_enrichment import process_job_enrichment
result = process_job_enrichment('test-job-id')
print(result)
"
```

### 5. Re-enrich Existing Jobs (Optional)

To add perks to already enriched jobs:

```python
from ingestion.llm_enrichment import batch_enrich_jobs, get_unenriched_jobs
from database.client import db

# Get all enriched jobs (to re-enrich with perks)
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

job_ids = [j["job_posting_id"] for j in enriched.data]

# Re-enrich in batches
batch_enrich_jobs(job_ids[:50], batch_size=50)
```

## Testing

### Test Perk Detection

Create test job descriptions:

```python
test_cases = [
    {
        "description": "Remote work possible. Salary €3500-€4200/month. Company car included.",
        "expected_perks": ["remote_policy", "salary_range", "company_car"]
    },
    {
        "description": "On-site only. Training budget available. Team building events.",
        "expected_perks": ["training_budget", "team_events"]
    },
    {
        "description": "Health insurance provided. €70k-€85k per year.",
        "expected_perks": ["hospitalization_insurance", "salary_range"]
    }
]

for test in test_cases:
    result = enrich_job_with_llm("test-id", test["description"])
    perks = result[0]["perks"]
    found_keys = [p["key"] for p in perks if p["found"]]
    assert set(found_keys) == set(test["expected_perks"])
```

### Verify Translations

```python
# Check that fixed translations are used
perks = [
    {"key": "remote_policy", "nl": "Remote", "en": "Remote", "fr": "Télétravail"},
    {"key": "company_car", "nl": "Wagen", "en": "Car", "fr": "Voiture"},
    # etc.
]

for perk in enriched_perks:
    if perk["key"] != "salary_range" and perk["found"]:
        expected = next(p for p in perks if p["key"] == perk["key"])
        assert perk["nl"] == expected["nl"]
        assert perk["en"] == expected["en"]
        assert perk["fr"] == expected["fr"]
```

## UI Integration (Future)

### Display Perks as Badges

```html
<div class="perks">
    <template x-for="perk in job.llm_enrichment?.perks?.filter(p => p.found)">
        <span class="perk-badge" x-text="perk[currentLang]"></span>
    </template>
</div>
```

### Filter by Perks

```javascript
// Filter jobs with remote policy
const remoteJobs = jobs.filter(job => {
    const perks = job.llm_enrichment?.perks || [];
    return perks.some(p => p.key === 'remote_policy' && p.found);
});
```

### Perk Icons

```javascript
const perkIcons = {
    'remote_policy': '🏠',
    'salary_range': '💰',
    'company_car': '🚗',
    'hospitalization_insurance': '🏥',
    'training_budget': '📚',
    'team_events': '🎉'
};
```

## Performance

### Index Usage

```sql
-- Fast query using GIN index
EXPLAIN ANALYZE
SELECT * FROM llm_enrichment
WHERE perks @> '[{"key": "remote_policy", "found": true}]';
```

### Storage

- Average perks array: ~500 bytes
- 1000 jobs: ~500 KB
- Negligible storage impact

## Future Enhancements

- [ ] UI filters for perks
- [ ] Perk statistics dashboard
- [ ] Perk trend analysis
- [ ] Custom perk detection
- [ ] Perk importance scoring
- [ ] Salary range parsing and normalization
- [ ] Perk recommendations based on user preferences

## Rollback

If issues occur:

```sql
-- Remove perks column
ALTER TABLE llm_enrichment DROP COLUMN IF EXISTS perks;

-- Revert prompt version
-- In ingestion/llm_enrichment.py:
PROMPT_VERSION = "14"
```

## Support

For issues or questions:
1. Check logs for LLM response format
2. Verify prompt version is v15
3. Check database column exists
4. Test with sample job description
