# Company Enrichment v15 - Hiring Model

## Nieuw in v15

### Hiring Model Field

Onderscheid tussen recruitment/staffing bedrijven en bedrijven die direct inhuren:

**Canonical Field:**
```
hiring_model: "recruitment" | "direct" | "unknown"
```

**Multilingual Fields:**
```
hiring_model_en: "Recruitment" | "Direct" | "Unknown"
hiring_model_nl: "Recruitment" | "Direct" | "Onbekend"
hiring_model_fr: "Recrutement" | "Direct" | "Inconnu"
```

## Detectieregels

### 🏢 Recruitment
Bedrijf levert werving/staffing als **dienst**:
- Staffing agencies
- Interim bureaus
- Headhunting firms
- W&S (Werving & Selectie)
- RPO (Recruitment Process Outsourcing)
- Job postings met "for our client"

**Voorbeelden:**
- Randstad
- Manpower
- Robert Half
- Hays
- Accent Jobs

### 🏭 Direct
Werft **uitsluitend voor eigen bedrijf**:
- Normale organisaties
- SaaS bedrijven
- Productie bedrijven
- Consultancy (die zelf consultants in dienst neemt)
- Tech companies
- Retail

**Voorbeelden:**
- Atlas Copco
- Coolblue
- Proximus
- Colruyt
- Deloitte (voor eigen consultants)

### ❓ Unknown
Te weinig of gemengde signalen:
- Onvoldoende informatie
- Hybride modellen
- Onduidelijke business model

## Database Migratie

### Migratie 026

**Bestand:** `database/migrations/026_add_hiring_model.sql`

```sql
-- Add hiring_model columns
ALTER TABLE company_master_data
ADD COLUMN IF NOT EXISTS hiring_model TEXT,
ADD COLUMN IF NOT EXISTS hiring_model_en TEXT,
ADD COLUMN IF NOT EXISTS hiring_model_nl TEXT,
ADD COLUMN IF NOT EXISTS hiring_model_fr TEXT;

-- Add check constraint
ALTER TABLE company_master_data
ADD CONSTRAINT check_hiring_model_values 
CHECK (hiring_model IS NULL OR hiring_model IN ('recruitment', 'direct', 'unknown'));

-- Add index
CREATE INDEX IF NOT EXISTS idx_company_master_data_hiring_model 
ON company_master_data(hiring_model) 
WHERE hiring_model IS NOT NULL;
```

**Uitvoeren:**
1. Kopieer SQL uit `database/migrations/026_add_hiring_model.sql`
2. Plak in Supabase SQL Editor
3. Klik "Run"

## Code Changes

### 1. Prompt Version Update

**Bestand:** `ingestion/company_enrichment.py`

```python
COMPANY_ENRICHMENT_PROMPT_VERSION = "15"  # Was: "14"
```

### 2. Database Save Logic

```python
db_data = {
    # ... existing fields ...
    
    # Hiring model fields (prompt v15+)
    "hiring_model": enrichment_data.get("hiring_model"),
    "hiring_model_en": enrichment_data.get("hiring_model_en"),
    "hiring_model_nl": enrichment_data.get("hiring_model_nl"),
    "hiring_model_fr": enrichment_data.get("hiring_model_fr"),
    
    # ... rest of fields ...
}
```

## Testing

### Test Script

```bash
python test_hiring_model_v15.py
```

**Test Cases:**
1. **Randstad** → Expected: `recruitment`
2. **Atlas Copco** → Expected: `direct`

### Manual Testing

```python
from ingestion.company_enrichment import enrich_company

# Test recruitment company
result = enrich_company(company_id, "Randstad")

# Check result
from database.client import db
data = db.client.table("company_master_data")\
    .select("hiring_model, hiring_model_en, hiring_model_nl, hiring_model_fr")\
    .eq("company_id", company_id)\
    .single()\
    .execute()

print(data.data)
# Expected: {'hiring_model': 'recruitment', 'hiring_model_en': 'Recruitment', ...}
```

## Database Queries

### Filter by Hiring Model

```sql
-- Get all recruitment companies
SELECT c.name, cmd.hiring_model_en, cmd.sector_en
FROM companies c
JOIN company_master_data cmd ON c.id = cmd.company_id
WHERE cmd.hiring_model = 'recruitment';

-- Get all direct hiring companies
SELECT c.name, cmd.hiring_model_en, cmd.sector_en
FROM companies c
JOIN company_master_data cmd ON c.id = cmd.company_id
WHERE cmd.hiring_model = 'direct';

-- Count by hiring model
SELECT 
    hiring_model,
    COUNT(*) as count
FROM company_master_data
WHERE hiring_model IS NOT NULL
GROUP BY hiring_model
ORDER BY count DESC;
```

### Filter Jobs by Company Hiring Model

```sql
-- Jobs from recruitment companies
SELECT 
    jp.title,
    c.name as company_name,
    cmd.hiring_model_en
FROM job_postings jp
JOIN companies c ON jp.company_id = c.id
JOIN company_master_data cmd ON c.id = cmd.company_id
WHERE cmd.hiring_model = 'recruitment'
LIMIT 100;

-- Jobs from direct hiring companies
SELECT 
    jp.title,
    c.name as company_name,
    cmd.hiring_model_en
FROM job_postings jp
JOIN companies c ON jp.company_id = c.id
JOIN company_master_data cmd ON c.id = cmd.company_id
WHERE cmd.hiring_model = 'direct'
LIMIT 100;
```

## Use Cases

### 1. Filter Out Recruitment Agencies

Voor job seekers die alleen direct hiring willen:

```sql
SELECT jp.*
FROM job_postings jp
JOIN companies c ON jp.company_id = c.id
JOIN company_master_data cmd ON c.id = cmd.company_id
WHERE cmd.hiring_model = 'direct'
  AND jp.title_classification = 'Data';
```

### 2. Analytics

```sql
-- Percentage recruitment vs direct
SELECT 
    hiring_model,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM company_master_data
WHERE hiring_model IS NOT NULL
GROUP BY hiring_model;
```

### 3. Company Search with Filter

```python
# API endpoint: GET /api/companies?hiring_model=direct
result = db.client.table("companies")\
    .select("*, company_master_data!inner(hiring_model_en, sector_en)")\
    .eq("company_master_data.hiring_model", "direct")\
    .execute()
```

## Backward Compatibility

### Existing Data

Companies enriched with v14 or earlier will have `hiring_model = NULL`:
- ✅ Queries with `WHERE hiring_model = 'direct'` will exclude them
- ✅ Re-enrich with v15 to populate the field
- ✅ Use `WHERE hiring_model IS NULL` to find unenriched companies

### Re-enrichment

```python
from ingestion.company_enrichment import get_unenriched_companies, enrich_companies_batch

# Get companies without hiring_model
result = db.client.table("company_master_data")\
    .select("company_id")\
    .is_("hiring_model", "null")\
    .limit(100)\
    .execute()

company_ids = [row["company_id"] for row in result.data]

# Re-enrich with v15
stats = enrich_companies_batch(company_ids)
print(f"Re-enriched {stats['successful']} companies with hiring_model")
```

## Migration Checklist

- [ ] Run database migration 026
- [ ] Verify columns exist in `company_master_data`
- [ ] Code updated to prompt v15
- [ ] Test with recruitment company (e.g., Randstad)
- [ ] Test with direct company (e.g., Atlas Copco)
- [ ] Verify multilingual fields are populated
- [ ] Update API endpoints to support hiring_model filter
- [ ] Update UI to show hiring_model badge/filter

## Future Enhancements

### 1. UI Badge
```jsx
{company.hiring_model === 'recruitment' && (
  <Badge color="purple">Recruitment Agency</Badge>
)}
{company.hiring_model === 'direct' && (
  <Badge color="green">Direct Hiring</Badge>
)}
```

### 2. Job Posting Filter
```jsx
<Checkbox 
  label="Hide recruitment agencies"
  onChange={(checked) => setFilter({...filter, excludeRecruitment: checked})}
/>
```

### 3. Analytics Dashboard
- % jobs from recruitment vs direct
- Top recruitment agencies by job count
- Sector breakdown by hiring model

## Support

Bij vragen of problemen:
1. Check of migratie 026 is uitgevoerd
2. Verify prompt version is "15"
3. Test met `test_hiring_model_v15.py`
4. Check database voor `hiring_model` values
