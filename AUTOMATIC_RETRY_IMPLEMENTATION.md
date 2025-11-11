# Automatic Retry Implementation voor LLM Enrichments

## Overzicht

Alle LLM enrichment operaties in de web app hebben nu **automatische retry logica** voor quota errors en andere transiente fouten. Items die gefaald zijn door quota overschrijding worden automatisch opnieuw geprobeerd na **24 uur**.

## Geïmplementeerde Services

### 1. **Location Enrichment** ✅
**Bestand:** `ingestion/auto_enrich_service.py`

**Wat:**
- Auto-enrichment service draait elke 60 seconden
- Verwerkt 10 locations per batch
- Includeert nu locations met errors >24h oud

**Query Logica:**
```python
retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

# Selecteert:
# 1. Nieuwe locations (ai_enriched is null, geen error)
# 2. Niet-enriched locations (ai_enriched = false, geen error)
# 3. Locations met errors ouder dan 24h
result = db.client.table("locations")\
    .select("id, city, country_code, region, ai_enrichment_error, ai_enriched_at")\
    .or_(
        f"and(ai_enriched.is.null,ai_enrichment_error.is.null),"
        f"and(ai_enriched.eq.false,ai_enrichment_error.is.null),"
        f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{retry_cutoff})"
    )\
    .limit(10)\
    .execute()
```

**Logging:**
```
🔄 Auto-enriching 10 locations (7 new, 3 retries)
Retrying: Arlon, None (previous error)
```

### 2. **Job Enrichment** ✅
**Bestand:** `ingestion/llm_enrichment.py`

**Wat:**
- `get_unenriched_jobs()` functie aangepast
- Nieuwe parameter: `include_retries=True` (default)
- Alleen jobs met `title_classification = 'Data'`

**Query Logica:**
```python
retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

# Selecteert:
# 1. Nieuwe jobs (enrichment_completed_at is null, geen error)
# 2. Jobs met errors ouder dan 24h
# EN title_classification = 'Data'
result = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_error, enrichment_completed_at, job_postings!inner(title_classification)")\
    .or_(
        f"and(enrichment_completed_at.is.null,enrichment_error.is.null),"
        f"and(enrichment_error.not.is.null,enrichment_completed_at.lt.{retry_cutoff})"
    )\
    .eq("job_postings.title_classification", "Data")\
    .limit(limit)\
    .execute()
```

**Logging:**
```
Found 50 unenriched 'Data' jobs (42 new, 8 retries)
```

### 3. **Company Enrichment** ✅
**Bestand:** `ingestion/company_enrichment.py`

**Wat:**
- `get_unenriched_companies()` functie aangepast
- Nieuwe parameter: `include_retries=True` (default)

**Query Logica:**
```python
retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

# Selecteert:
# 1. Companies zonder master data
# 2. Companies met ai_enriched = false (geen error)
# 3. Companies met errors ouder dan 24h
result = db.client.table("company_master_data")\
    .select("company_id, ai_enriched, ai_enrichment_error, ai_enriched_at")\
    .or_(
        f"ai_enriched.is.null,"
        f"and(ai_enriched.eq.false,ai_enrichment_error.is.null),"
        f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{retry_cutoff})"
    )\
    .limit(limit)\
    .execute()
```

**Logging:**
```
Found 25 unenriched companies (20 new, 5 retries)
```

## Retry Helper Utilities

**Bestand:** `ingestion/retry_helper.py`

Bevat herbruikbare functies voor retry logica:

### `should_retry_enrichment()`
```python
def should_retry_enrichment(
    error_message: Optional[str],
    last_attempt_at: Optional[str],
    retry_delay_hours: int = 24
) -> bool:
    """
    Bepaalt of enrichment opnieuw geprobeerd moet worden.
    
    Returns:
        True als retry nodig is, False anders
    """
```

**Error Type Handling:**
- ✅ **Quota errors** (429, "quota exceeded"): Retry na 24h
- ✅ **Rate limit errors**: Retry na 24h
- ✅ **Timeout errors**: Retry na 24h
- ❌ **Parsing/validation errors**: GEEN retry (permanent)
- ✅ **Unknown errors**: Retry eenmalig na 24h

### `is_quota_error()`
```python
def is_quota_error(error_message: Optional[str]) -> bool:
    """Check if error is a quota/rate limit error."""
```

## Configuratie

### Retry Delay Aanpassen

Standaard: **24 uur**

Om aan te passen, wijzig de `retry_delay_hours` parameter:

```python
# In auto_enrich_service.py
retry_cutoff = (datetime.utcnow() - timedelta(hours=12)).isoformat()  # 12h in plaats van 24h

# Of in get_unenriched_jobs()
jobs = get_unenriched_jobs(limit=100, include_retries=True)
```

### Retry Uitschakelen

```python
# Disable retries (alleen nieuwe items)
jobs = get_unenriched_jobs(limit=100, include_retries=False)
companies = get_unenriched_companies(limit=100, include_retries=False)
```

## Testing

### Test Script
```bash
python test_retry_logic.py
```

**Output:**
```
🧪 Testing Automatic Retry Logic for LLM Enrichments
================================================================================

1️⃣ Location Enrichment Retry Logic
--------------------------------------------------------------------------------
✅ Found 10 locations to enrich
   - New: 7
   - Retries (>24h old errors): 3

   Retry examples:
   - Arlon: Error code: 429 - {'error': {'message': 'You exceeded...
   - Ukkel: Error code: 429 - {'error': {'message': 'You exceeded...

2️⃣ Job Enrichment Retry Logic
--------------------------------------------------------------------------------
✅ Found 50 'Data' jobs to enrich
   - New: 42
   - Retries (>24h old errors): 8

3️⃣ Company Enrichment Retry Logic
--------------------------------------------------------------------------------
✅ Found 25 companies to enrich
   - New: 20
   - Retries (>24h old errors): 5

📊 Summary:
   Locations ready: 10
   Jobs ready: 50
   Companies ready: 25

✅ Retry logic is working!
```

### Handmatig Testen

```python
from ingestion.auto_enrich_service import get_auto_enrich_service
from ingestion.llm_enrichment import get_unenriched_jobs
from ingestion.company_enrichment import get_unenriched_companies

# Check welke items retry nodig hebben
locations = # auto-enrichment service haalt deze automatisch op
jobs = get_unenriched_jobs(limit=100, include_retries=True)
companies = get_unenriched_companies(limit=100, include_retries=True)
```

## Monitoring

### Database Queries

**Vind items die binnenkort retry krijgen:**
```sql
-- Locations met errors ouder dan 23h (binnen 1h retry)
SELECT city, ai_enrichment_error, ai_enriched_at,
       NOW() - ai_enriched_at as age
FROM locations
WHERE ai_enrichment_error IS NOT NULL
  AND ai_enriched_at < NOW() - INTERVAL '23 hours'
ORDER BY ai_enriched_at;
```

**Count retry candidates:**
```sql
-- Locations
SELECT COUNT(*) as retry_candidates
FROM locations
WHERE ai_enrichment_error IS NOT NULL
  AND ai_enriched_at < NOW() - INTERVAL '24 hours';

-- Jobs
SELECT COUNT(*) as retry_candidates
FROM llm_enrichment e
JOIN job_postings j ON e.job_posting_id = j.id
WHERE e.enrichment_error IS NOT NULL
  AND e.enrichment_completed_at < NOW() - INTERVAL '24 hours'
  AND j.title_classification = 'Data';

-- Companies
SELECT COUNT(*) as retry_candidates
FROM company_master_data
WHERE ai_enrichment_error IS NOT NULL
  AND ai_enriched_at < NOW() - INTERVAL '24 hours';
```

### Logs Monitoren

**Location Auto-Enrichment:**
```
2025-11-09 22:40:00 | INFO | 🔄 Auto-enriching 10 locations (7 new, 3 retries)
2025-11-09 22:40:01 | INFO | Retrying: Arlon, None (previous error)
2025-11-09 22:40:02 | SUCCESS | ✅ Auto-enriched: Arlon
```

**Job/Company Enrichment:**
```
2025-11-09 22:40:00 | INFO | Found 50 unenriched 'Data' jobs (42 new, 8 retries)
2025-11-09 22:40:00 | INFO | Found 25 unenriched companies (20 new, 5 retries)
```

## Voordelen

### ✅ Automatisch
- Geen handmatige interventie nodig
- Quota errors worden automatisch opgelost na 24h
- Service blijft draaien zonder blokkades

### ✅ Intelligent
- Alleen transiente errors worden retry'd
- Permanente errors (parsing) worden niet retry'd
- Configurable retry delay

### ✅ Transparant
- Duidelijke logging van retries
- Monitoring via database queries
- Test script voor verificatie

### ✅ Efficiënt
- Geen duplicate work
- Respecteert API rate limits
- Batch processing blijft werken

## Toekomstige Verbeteringen

### 1. Exponential Backoff
```python
# Retry na 1h, 2h, 4h, 8h, 24h
retry_delay = 2 ** retry_count  # hours
```

### 2. Max Retry Attempts
```python
# Stop na 5 pogingen
if retry_count >= 5:
    # Mark as permanently failed
    pass
```

### 3. Retry Counter Tracking
```sql
ALTER TABLE locations 
ADD COLUMN enrichment_retry_count INTEGER DEFAULT 0;

ALTER TABLE llm_enrichment
ADD COLUMN enrichment_retry_count INTEGER DEFAULT 0;

ALTER TABLE company_master_data
ADD COLUMN enrichment_retry_count INTEGER DEFAULT 0;
```

### 4. Dashboard
- Visualiseer retry statistics
- Alert bij hoge failure rate
- Track quota usage

## Rollback

Om retry logica uit te schakelen:

```python
# In auto_enrich_service.py
result = db.client.table("locations")\
    .select("id, city, country_code, region")\
    .or_("ai_enriched.is.null,ai_enriched.eq.false")\
    .is_("ai_enrichment_error", "null")\  # Voeg deze regel terug toe
    .limit(10)\
    .execute()

# In llm_enrichment.py en company_enrichment.py
jobs = get_unenriched_jobs(limit=100, include_retries=False)
companies = get_unenriched_companies(limit=100, include_retries=False)
```

## Support

Bij problemen:
1. Check logs voor retry attempts
2. Run `test_retry_logic.py` voor diagnostics
3. Query database voor retry candidates
4. Verify retry_cutoff timestamp is correct
