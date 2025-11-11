# Multi-Source Implementation Plan

## Doel
Jobs kunnen van meerdere bronnen komen (LinkedIn EN Indeed) en beide sources worden getoond als badges.

## Database Wijzigingen

### Migratie 030: `job_sources` Table

```sql
CREATE TABLE job_sources (
    id UUID PRIMARY KEY,
    job_posting_id UUID REFERENCES job_postings(id),
    source TEXT CHECK (source IN ('linkedin', 'indeed')),
    source_job_id TEXT,  -- linkedin_job_id or indeed_job_id
    first_seen_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    UNIQUE(job_posting_id, source)
);
```

### Deduplicatie Kolommen

```sql
ALTER TABLE job_postings
ADD COLUMN title_normalized TEXT,
ADD COLUMN dedup_key TEXT;

CREATE UNIQUE INDEX idx_job_postings_dedup_key ON job_postings(dedup_key);
```

**Dedup key format:** `normalized_title|company_name`

## Code Wijzigingen

### 1. Deduplicator (✅ Created)
- `ingestion/deduplicator_v2.py`
- Nieuwe functies:
  - `check_job_exists_by_dedup(title, company)` - Check op title+company
  - `add_source_to_job(job_id, source, source_job_id)` - Voeg source toe
  - `check_source_exists_for_job()` - Check of source al bestaat
  - `update_source_last_seen()` - Update timestamp

### 2. Processor Updates (TODO)
- `ingestion/processor.py`
- Wijzig `process_job_posting()`:
  ```python
  # OLD: Check by source-specific ID
  exists, job_id, existing = check_job_exists(job_id, source)
  
  # NEW: Check by title + company
  exists, job_id, existing = check_job_exists_by_dedup(title, company_name)
  
  if exists:
      # Check if THIS source already exists
      if check_source_exists_for_job(job_id, source, source_job_id):
          # Update last_seen
          update_source_last_seen(job_id, source)
      else:
          # Add new source to existing job
          add_source_to_job(job_id, source, source_job_id)
  else:
      # Create new job + first source
      job_id = create_job(...)
      add_source_to_job(job_id, source, source_job_id)
  ```

### 3. Database Client Updates (TODO)
- `database/client.py`
- Nieuwe functies:
  - `insert_job_posting()` - Set dedup_key bij insert
  - `update_job_posting()` - Update dedup_key bij update

### 4. API Updates (TODO)
- `web/api/jobs.py`
- Wijzig `list_jobs()`:
  ```python
  # Join met job_sources
  query = db.client.table("job_postings")\
      .select("*, job_sources(source, source_job_id)")
  ```

### 5. UI Updates (TODO)
- `web/templates/jobs.html`
- Wijzig source kolom:
  ```html
  <!-- OLD: Single badge -->
  <span x-show="job.source === 'linkedin'">LinkedIn</span>
  
  <!-- NEW: Multiple badges -->
  <template x-for="source in job.job_sources">
      <span x-show="source.source === 'linkedin'">LinkedIn</span>
      <span x-show="source.source === 'indeed'">Indeed</span>
  </template>
  ```

## Migratie Strategie

### Stap 1: Run Migratie 030
```sql
-- Creates job_sources table
-- Migrates existing data
-- Adds dedup_key column
```

### Stap 2: Update Code
- Processor
- Database client
- API
- UI

### Stap 3: Test
1. Scrape dezelfde job van LinkedIn
2. Scrape dezelfde job van Indeed
3. Verwacht: 1 job met 2 source badges

## Voordelen

✅ **Geen duplicaten:** Dezelfde job = 1 entry  
✅ **Multi-source tracking:** Zie waar job vandaan komt  
✅ **Betere data:** Combineer info van beide bronnen  
✅ **Flexibel:** Makkelijk nieuwe sources toevoegen  

## Backward Compatibility

✅ `source` kolom blijft bestaan (voor oude queries)  
✅ `linkedin_job_id` en `indeed_job_id` blijven bestaan  
✅ Oude code blijft werken tijdens transitie  

## Next Steps

1. ✅ Migratie 030 created
2. ✅ Deduplicator v2 created
3. ⏳ Update processor
4. ⏳ Update database client
5. ⏳ Update API
6. ⏳ Update UI
7. ⏳ Test end-to-end
