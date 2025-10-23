# Tech Stack Masterdata System

## Overview
Masterdata systeem voor programming languages en ecosystems, vergelijkbaar met het companies systeem. Elke tech stack item heeft een logo, display name en wordt automatisch gekoppeld aan jobs via LLM enrichment.

## Database Schema

### Tables

**1. `programming_languages`**
```sql
- id (UUID, PK)
- name (TEXT, UNIQUE) -- Canonical name voor matching
- display_name (TEXT) -- Bewerkbare weergavenaam
- logo_url (TEXT) -- URL naar logo afbeelding
- category (TEXT) -- Optioneel: "General Purpose", "Query Language", etc.
- description (TEXT) -- Optionele beschrijving
- is_active (BOOLEAN) -- Voor soft deletion
- created_at, updated_at (TIMESTAMPTZ)
```

**2. `ecosystems`**
```sql
- id (UUID, PK)
- name (TEXT, UNIQUE) -- Canonical name voor matching
- display_name (TEXT) -- Bewerkbare weergavenaam
- logo_url (TEXT) -- URL naar logo afbeelding
- category (TEXT) -- Optioneel: "Cloud Platform", "Data Tool", etc.
- description (TEXT) -- Optionele beschrijving
- is_active (BOOLEAN) -- Voor soft deletion
- created_at, updated_at (TIMESTAMPTZ)
```

**3. `job_programming_languages` (Junction Table)**
```sql
- id (UUID, PK)
- job_posting_id (UUID, FK → job_postings)
- programming_language_id (UUID, FK → programming_languages)
- requirement_level (TEXT) -- 'must_have' of 'nice_to_have'
- created_at (TIMESTAMPTZ)
- UNIQUE(job_posting_id, programming_language_id)
```

**4. `job_ecosystems` (Junction Table)**
```sql
- id (UUID, PK)
- job_posting_id (UUID, FK → job_postings)
- ecosystem_id (UUID, FK → ecosystems)
- requirement_level (TEXT) -- 'must_have' of 'nice_to_have'
- created_at (TIMESTAMPTZ)
- UNIQUE(job_posting_id, ecosystem_id)
```

## Workflow

### 1. LLM Enrichment → Masterdata
```
Job Enrichment
    ↓
Extract tech stack
    ↓
For each language/ecosystem:
    ├─ Check if exists in masterdata (by name)
    ├─ If not exists: Create new entry
    │   └─ name = canonical name
    │   └─ display_name = same as name (initially)
    │   └─ logo_url = NULL (to be added later)
    └─ Create job assignment
        └─ Link job ↔ tech stack item
        └─ Store requirement_level
```

### 2. Automatische Detectie
- **Nieuwe languages/ecosystems** worden automatisch toegevoegd tijdens enrichment
- **Canonical name** wordt gebruikt voor matching (case-sensitive)
- **Display name** kan later aangepast worden via UI
- **Logo's** kunnen later toegevoegd worden

### 3. Handmatige Aanpassingen
Via API endpoints kun je:
- Display names aanpassen
- Logo's toevoegen
- Categorieën toewijzen
- Beschrijvingen toevoegen
- Items deactiveren (soft delete)

## API Endpoints

### Programming Languages

**GET** `/api/tech-stack/programming-languages`
- Query params: `active_only=true`
- Returns: List van alle programming languages

**GET** `/api/tech-stack/programming-languages/{id}`
- Returns: Specifieke programming language

**POST** `/api/tech-stack/programming-languages`
```json
{
  "name": "Python",
  "display_name": "Python 3",
  "category": "General Purpose",
  "description": "High-level programming language",
  "logo_url": "https://..."
}
```

**PATCH** `/api/tech-stack/programming-languages/{id}`
```json
{
  "display_name": "Python 3.11",
  "logo_url": "https://...",
  "category": "General Purpose"
}
```

**DELETE** `/api/tech-stack/programming-languages/{id}`
- Query params: `hard_delete=false` (soft delete by default)

### Ecosystems

**GET** `/api/tech-stack/ecosystems`
**GET** `/api/tech-stack/ecosystems/{id}`
**POST** `/api/tech-stack/ecosystems`
**PATCH** `/api/tech-stack/ecosystems/{id}`
**DELETE** `/api/tech-stack/ecosystems/{id}`

(Same structure as programming languages)

### Stats

**GET** `/api/tech-stack/stats`
```json
{
  "programming_languages": {
    "total": 50,
    "active": 48
  },
  "ecosystems": {
    "total": 75,
    "active": 70
  },
  "assignments": {
    "job_languages": 1250,
    "job_ecosystems": 980
  }
}
```

## Code Structure

### Database Client (`database/client.py`)
```python
# Programming Languages
db.get_programming_language_by_name(name)
db.insert_programming_language(data)
db.upsert_programming_language(data)
db.get_all_programming_languages(active_only=True)

# Ecosystems
db.get_ecosystem_by_name(name)
db.insert_ecosystem(data)
db.upsert_ecosystem(data)
db.get_all_ecosystems(active_only=True)

# Job Assignments
db.assign_programming_language_to_job(job_id, language_id, requirement_level)
db.assign_ecosystem_to_job(job_id, ecosystem_id, requirement_level)
db.get_job_programming_languages(job_id)
db.get_job_ecosystems(job_id)
```

### Tech Stack Processor (`ingestion/tech_stack_processor.py`)
```python
# Main function called after LLM enrichment
process_tech_stack_for_job(job_id, enrichment_data)

# Helper functions
_process_programming_language(job_id, language_name, requirement_level)
_process_ecosystem(job_id, ecosystem_name, requirement_level)

# Get tech stack for a job
get_job_tech_stack(job_id)
```

### LLM Enrichment Integration
In `ingestion/llm_enrichment.py`, na succesvolle enrichment:
```python
if success:
    # Process tech stack (programming languages and ecosystems)
    from ingestion.tech_stack_processor import process_tech_stack_for_job
    process_tech_stack_for_job(UUID(job_id), enrichment_data)
```

## Migration

### Run Database Migration
```sql
-- File: database/migrations/006_add_tech_stack_masterdata.sql
-- Run in Supabase SQL Editor
```

Dit creëert:
- 4 nieuwe tabellen
- Indexes voor performance
- Triggers voor updated_at
- Pre-populated data (22 languages, 39 ecosystems)

### Migrate Existing Data
```bash
# Migrate tech stack from existing enrichments
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/migrate_existing_tech_stack.py
```

Dit script:
1. Haalt alle enriched jobs op
2. Extraheert tech stack uit `llm_enrichment` tabel
3. Creëert masterdata entries
4. Creëert job assignments

## Pre-populated Data

### Programming Languages (22)
Python, SQL, Java, JavaScript, TypeScript, R, Scala, Go, Bash, PowerShell, Julia, C#, C++, Ruby, PHP, Swift, Kotlin, Rust, DAX, M, MDX, VBA

### Ecosystems (39)
Apache Spark, Databricks, Airflow, dbt, Kafka, Flink, Azure, AWS, GCP, Power BI, Tableau, Looker, Snowflake, BigQuery, Redshift, Synapse, Data Factory, Collibra, Purview, Docker, Kubernetes, Terraform, Git, Jenkins, MLflow, TensorFlow, PyTorch, scikit-learn, Pandas, NumPy, Jupyter, VS Code, PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, S3, HDFS

## Logo Management

### Opties voor logo's:

**1. Externe URLs**
```json
{
  "logo_url": "https://cdn.example.com/logos/python.png"
}
```

**2. Lokale opslag** (toekomstig)
- Upload endpoint toevoegen
- Opslaan in `/web/static/logos/`
- URL: `/static/logos/python.png`

**3. Logo services**
- [Simple Icons](https://simpleicons.org/)
- [DevIcon](https://devicon.dev/)
- [Skill Icons](https://skillicons.dev/)

### Voorbeeld: Skill Icons
```
https://skillicons.dev/icons?i=python,sql,azure,databricks
```

## Best Practices

### Naming Conventions
- **Canonical name**: Exact match met LLM output (case-sensitive)
- **Display name**: User-friendly naam voor UI
- Voorbeeld:
  - name: `Azure` (voor matching)
  - display_name: `Microsoft Azure` (voor weergave)

### Categories
Gebruik consistente categorieën:
- **Languages**: General Purpose, Query Language, Scripting, Web Development, etc.
- **Ecosystems**: Cloud Platform, Data Tool, BI Tool, Framework, Database, etc.

### Logo URLs
- Gebruik HTTPS
- Voorkeur voor SVG (schaalt beter)
- Fallback naar PNG (min. 128x128px)
- Test URLs voordat je opslaat

### Soft Delete
- Gebruik `is_active=false` in plaats van hard delete
- Behoudt historische data
- Kan later weer geactiveerd worden

## Future Enhancements

### UI Pages
- [ ] Tech Stack management pagina
- [ ] Logo upload functionaliteit
- [ ] Bulk edit voor display names
- [ ] Category management
- [ ] Usage statistics per tech stack item

### Analytics
- [ ] Most used languages/ecosystems
- [ ] Trending tech stack
- [ ] Tech stack combinations
- [ ] Company tech stack profiles

### Normalization
- [ ] Alias mapping (bijv. "ADF" → "Azure Data Factory")
- [ ] Auto-correct common typos
- [ ] Merge duplicates tool
- [ ] Suggest display names based on usage

## Testing

### Test API Endpoints
```bash
# Get all languages
curl http://localhost:8000/api/tech-stack/programming-languages

# Get all ecosystems
curl http://localhost:8000/api/tech-stack/ecosystems

# Get stats
curl http://localhost:8000/api/tech-stack/stats

# Update display name
curl -X PATCH http://localhost:8000/api/tech-stack/programming-languages/{id} \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Python 3.11"}'
```

### Test Enrichment Flow
1. Enrich een job via UI
2. Check `job_programming_languages` tabel
3. Check `job_ecosystems` tabel
4. Verify masterdata entries created
5. Check requirement levels correct

## Troubleshooting

### Duplicate Entries
Als je duplicaten ziet (bijv. "Python" en "python"):
```sql
-- Find duplicates
SELECT name, COUNT(*) 
FROM programming_languages 
GROUP BY LOWER(name) 
HAVING COUNT(*) > 1;

-- Merge manually via API or SQL
```

### Missing Logos
```sql
-- Find items without logos
SELECT name, display_name 
FROM programming_languages 
WHERE logo_url IS NULL 
ORDER BY name;
```

### Failed Assignments
Check logs voor errors tijdens enrichment:
```
Failed to process tech stack for job {job_id}: {error}
```

Mogelijke oorzaken:
- Invalid UUID
- Foreign key constraint violation
- Duplicate assignment (wordt automatisch geskipt)
