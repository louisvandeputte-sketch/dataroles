# Hoe Time Ago Kolommen Gebruiken

## Directe Database Query

### SQL Query (Supabase SQL Editor)
```sql
SELECT 
    job_posting_id,
    title,
    company_name,
    posted_date,
    posted_date_corrected,
    time_ago_nl,
    time_ago_fr,
    time_ago_en,
    ranking_position,
    type_datarol,
    seniority,
    contract
FROM vw_job_listings
ORDER BY ranking_position ASC
LIMIT 50;
```

## Python (Supabase Client)

### Voorbeeld 1: Alle jobs ophalen met time_ago
```python
from database.client import db

# Haal jobs op uit vw_job_listings
result = db.client.table("vw_job_listings")\
    .select("job_posting_id, title, company_name, time_ago_nl, time_ago_fr, time_ago_en, ranking_position")\
    .order("ranking_position", desc=False)\
    .limit(50)\
    .execute()

jobs = result.data

# Gebruik de data
for job in jobs:
    print(f"{job['title']} - {job['time_ago_nl']}")
```

### Voorbeeld 2: Filter op "Nieuw" jobs
```python
# Alleen nieuwe jobs (< 7 dagen)
result = db.client.table("vw_job_listings")\
    .select("*")\
    .eq("time_ago_nl", "Nieuw")\
    .order("ranking_position", desc=False)\
    .execute()

new_jobs = result.data
print(f"Aantal nieuwe jobs: {len(new_jobs)}")
```

### Voorbeeld 3: Zoeken met filters
```python
# Zoek Data Engineers met time_ago kolommen
result = db.client.table("vw_job_listings")\
    .select("*")\
    .eq("type_datarol", "Data Engineer")\
    .order("ranking_position", desc=False)\
    .limit(20)\
    .execute()

for job in result.data:
    print(f"{job['title']} bij {job['company_name']}")
    print(f"  Gepost: {job['time_ago_nl']}")
    print(f"  Posted: {job['time_ago_en']}")
    print(f"  Publié: {job['time_ago_fr']}")
```

### Voorbeeld 4: Met count
```python
# Haal jobs op met totaal aantal
result = db.client.table("vw_job_listings")\
    .select("*", count="exact")\
    .order("ranking_position", desc=False)\
    .range(0, 49)\
    .execute()

jobs = result.data
total = result.count

print(f"Showing {len(jobs)} of {total} jobs")
```

## JavaScript/TypeScript (Supabase Client)

### Voorbeeld 1: Fetch jobs met time_ago
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Haal jobs op
const { data: jobs, error } = await supabase
  .from('vw_job_listings')
  .select('job_posting_id, title, company_name, time_ago_nl, time_ago_fr, time_ago_en, ranking_position')
  .order('ranking_position', { ascending: true })
  .limit(50)

if (error) {
  console.error('Error:', error)
} else {
  console.log('Jobs:', jobs)
}
```

### Voorbeeld 2: Filter op nieuwe jobs
```javascript
// Alleen nieuwe jobs
const { data: newJobs, error } = await supabase
  .from('vw_job_listings')
  .select('*')
  .eq('time_ago_nl', 'Nieuw')
  .order('ranking_position', { ascending: true })

console.log(`${newJobs.length} nieuwe jobs gevonden`)
```

### Voorbeeld 3: Met pagination
```javascript
const page = 0
const pageSize = 20

const { data: jobs, error, count } = await supabase
  .from('vw_job_listings')
  .select('*', { count: 'exact' })
  .order('ranking_position', { ascending: true })
  .range(page * pageSize, (page + 1) * pageSize - 1)

console.log(`Page ${page + 1}, showing ${jobs.length} of ${count} total jobs`)
```

## REST API (Direct HTTP)

### Voorbeeld: GET request
```bash
curl "https://YOUR_PROJECT.supabase.co/rest/v1/vw_job_listings?select=job_posting_id,title,company_name,time_ago_nl,time_ago_fr,time_ago_en&order=ranking_position.asc&limit=50" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

### Met filters
```bash
# Alleen nieuwe jobs
curl "https://YOUR_PROJECT.supabase.co/rest/v1/vw_job_listings?select=*&time_ago_nl=eq.Nieuw&order=ranking_position.asc" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

## Belangrijke Opmerkingen

1. **View bevat alleen actieve Data jobs**: `vw_job_listings` filtert automatisch op:
   - `is_active = TRUE`
   - `title_classification = 'Data'`
   - Jobs met LLM enrichment

2. **Kolommen altijd beschikbaar**: De `time_ago_*` kolommen worden dynamisch berekend, dus ze zijn altijd gevuld.

3. **Geen extra joins nodig**: Alle data zit al in de view, inclusief company info, location, enrichment data, etc.

4. **Performance**: De view is geoptimaliseerd voor snelle queries.

## Beschikbare Kolommen in vw_job_listings

Naast `time_ago_nl`, `time_ago_fr`, `time_ago_en` zijn ook beschikbaar:
- `job_posting_id`
- `title`
- `posted_date`
- `posted_date_corrected`
- `first_seen_at`
- `ranking_position`
- `ranking_score`
- `base_score`
- `company_name`
- `logo_url`
- `type_datarol`
- `seniority`
- `contract`
- `city_name_nl`, `city_name_en`, `city_name_fr`
- `subdivision_name_nl`, `subdivision_name_en`, `subdivision_name_fr`
- `samenvatting_kort_nl`, `samenvatting_kort_en`, `samenvatting_kort_fr`
- En veel meer... (zie migratie 081 voor volledige lijst)
