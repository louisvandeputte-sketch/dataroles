# Frontend Guide: Data Role Type Filter

## Overzicht

Voor het filteren op **type datarol** (Data Engineer, Data Analyst, etc.) moet je frontend developer verwijzen naar de `llm_enrichment_active` view via de bestaande jobs API.

## Database Structuur

### Kolom: `type_datarol`
- **Locatie**: `llm_enrichment.type_datarol` (ook in `llm_enrichment_active` view)
- **Type**: `TEXT` (single value, geen array)
- **Index**: ✅ `idx_llm_type_datarol` (al aanwezig voor snelle queries)
- **Mogelijke waarden**:
  ```
  - 'Data Engineer'
  - 'Data Analyst'
  - 'Data Scientist'
  - 'BI Developer'
  - 'Data Architect'
  - 'Data Governance'
  - 'Other'
  - 'NIS'
  ```

### Multilingual Labels (JSONB)
De `labels` kolom bevat vertalingen in NL/EN/FR:

```json
{
  "type_datarol": {
    "nl": "Data Engineer",
    "en": "Data Engineer",
    "fr": "Ingénieur de Données"
  }
}
```

## API Implementatie

### Huidige Status
❌ **NIET geïmplementeerd** - De jobs API heeft momenteel geen `type_datarol` filter parameter.

### Wat Er Moet Gebeuren

#### 1. API Parameter Toevoegen

**File**: `web/api/jobs.py`

```python
@router.get("/jobs")
async def list_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None,
    company_ids: Optional[str] = None,
    location_ids: Optional[str] = None,
    type_ids: Optional[str] = None,
    seniority: Optional[str] = None,
    employment: Optional[str] = None,
    posted_date: Optional[str] = None,
    ai_enriched: Optional[str] = None,
    title_classification: Optional[str] = None,
    type_datarol: Optional[str] = None,  # 🆕 TOEVOEGEN
    source: Optional[str] = None,
    is_active: Optional[bool] = None,
    run_id: Optional[str] = None,
    # ... rest
):
```

#### 2. Database Client Update

**File**: `database/client.py`

In de `search_jobs` method:

```python
def search_jobs(
    self,
    # ... existing parameters ...
    type_datarol: Optional[str] = None,  # 🆕 TOEVOEGEN
    # ... rest
):
    # ... existing code ...
    
    # 🆕 TOEVOEGEN na title_classification filter
    # Filter by data role type (from llm_enrichment)
    if type_datarol:
        query = query.eq("llm_enrichment.type_datarol", type_datarol)
```

#### 3. JOIN Verificatie

De query moet al een JOIN hebben met `llm_enrichment`. Controleer in `client.py`:

```python
query = self.client.table("job_postings")\
    .select("""
        *,
        companies(*),
        locations(*),
        llm_enrichment(*)  # ✅ Deze JOIN moet er zijn
    """)
```

## Frontend Gebruik

### API Call Voorbeeld

```javascript
// Fetch Data Engineer jobs
const response = await fetch('/api/jobs/?type_datarol=Data Engineer&limit=50');
const data = await response.json();

// Fetch Data Analyst jobs in Belgium
const response = await fetch('/api/jobs/?type_datarol=Data Analyst&location=Belgium');
```

### Filter UI Component

```javascript
// Type Datarol filter dropdown
const dataRoleTypes = [
  { value: '', label: 'All Roles' },
  { value: 'Data Engineer', label: 'Data Engineer' },
  { value: 'Data Analyst', label: 'Data Analyst' },
  { value: 'Data Scientist', label: 'Data Scientist' },
  { value: 'BI Developer', label: 'BI Developer' },
  { value: 'Data Architect', label: 'Data Architect' },
  { value: 'Data Governance', label: 'Data Governance' },
  { value: 'Other', label: 'Other' },
  { value: 'NIS', label: 'NIS' }
];

// Alpine.js voorbeeld
<select x-model="filters.type_datarol" @change="loadJobs()">
  <template x-for="type in dataRoleTypes" :key="type.value">
    <option :value="type.value" x-text="type.label"></option>
  </template>
</select>
```

### Multilingual Labels Ophalen

Als je de vertalingen wilt tonen:

```javascript
// Job object heeft llm_enrichment.labels
const job = {
  title: "Senior Data Engineer",
  llm_enrichment: {
    type_datarol: "Data Engineer",
    labels: {
      type_datarol: {
        nl: "Data Engineer",
        en: "Data Engineer", 
        fr: "Ingénieur de Données"
      }
    }
  }
};

// Toon in gewenste taal
const currentLang = 'nl';
const roleLabel = job.llm_enrichment?.labels?.type_datarol?.[currentLang] 
                  || job.llm_enrichment?.type_datarol;
```

## Performance Optimalisatie

### Huidige Optimalisaties ✅
1. **Index**: `idx_llm_type_datarol` op `llm_enrichment.type_datarol`
2. **View**: `llm_enrichment_active` bevat alleen actieve velden
3. **Type**: `TEXT` (simpel, geen array parsing nodig)

### Geen Extra Optimalisatie Nodig ❌
- **JSON kolom NIET nodig** - `type_datarol` is al een simpele TEXT kolom
- **Geen GIN index nodig** - Geen array of JSONB filtering
- **Bestaande index is voldoende** - B-tree index op TEXT is perfect voor equality checks

### Query Performance
```sql
-- Snelle query dankzij index
EXPLAIN ANALYZE
SELECT * FROM llm_enrichment 
WHERE type_datarol = 'Data Engineer';

-- Expected: Index Scan using idx_llm_type_datarol
```

## Aanbevolen Implementatie Volgorde

1. ✅ **Database**: Geen wijzigingen nodig (index bestaat al)
2. 🔧 **Backend**: Update `database/client.py` - voeg `type_datarol` parameter toe
3. 🔧 **API**: Update `web/api/jobs.py` - voeg `type_datarol` parameter toe
4. 🎨 **Frontend**: Voeg filter dropdown toe aan jobs pagina

## Test Queries

```sql
-- Test 1: Hoeveel jobs per type?
SELECT type_datarol, COUNT(*) 
FROM llm_enrichment 
GROUP BY type_datarol 
ORDER BY COUNT(*) DESC;

-- Test 2: Data Engineers met enrichment
SELECT j.title, e.type_datarol, e.seniority
FROM job_postings j
JOIN llm_enrichment e ON j.id = e.job_posting_id
WHERE e.type_datarol = 'Data Engineer'
AND e.enrichment_completed_at IS NOT NULL
LIMIT 10;

-- Test 3: Via active view
SELECT job_posting_id, title, type_datarol, seniority
FROM llm_enrichment_active
WHERE type_datarol = 'Data Scientist'
LIMIT 10;
```

## Samenvatting

### Voor Frontend Developer:
- **Kolom**: `llm_enrichment.type_datarol` (via `llm_enrichment_active` view)
- **API Parameter**: `type_datarol` (moet nog geïmplementeerd worden)
- **Waarden**: Zie lijst hierboven (8 mogelijke types)
- **Performance**: ✅ Al geoptimaliseerd met index
- **Multilingual**: Gebruik `labels.type_datarol.{nl|en|fr}` voor vertalingen

### Geen Extra Database Werk Nodig:
- ❌ Geen nieuwe JSON kolom nodig
- ❌ Geen nieuwe index nodig
- ✅ Alles is al geoptimaliseerd

### Wel Backend Werk Nodig:
- 🔧 API parameter toevoegen
- 🔧 Database client filter toevoegen
- 🧪 Tests schrijven
