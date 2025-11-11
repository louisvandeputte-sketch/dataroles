# Job Enrichment Improvements

## Overzicht

Verbeteringen aan het job enrichment systeem om rate limits te beheren en betrouwbaarheid te verbeteren.

## Features

### 1. **Auto-Retry Logica** ✅

**Implementatie:** `ingestion/llm_enrichment.py` - `enrich_job_with_llm()`

**Retry Strategie:**
- **Rate Limit Errors:** 3 retries met exponential backoff (5s, 10s, 20s)
- **API Errors:** 3 retries met exponential backoff (3s, 6s, 12s)
- **JSON Parse Errors:** Geen retry (niet herstelbaar)

**Voorbeeld:**
```python
# Automatic retry on rate limit
enrichment_data, error = enrich_job_with_llm(job_id, description, max_retries=3)

# Logs:
# ⚠️  Rate limit hit for job abc123. Waiting 5s before retry 1/3
# ⚠️  Rate limit hit for job abc123. Waiting 10s before retry 2/3
# ✅ Successfully enriched job abc123
```

### 2. **Batch Size Limiting** ✅

**Implementatie:** `ingestion/llm_enrichment.py` - `batch_enrich_jobs()`

**Configuratie:**
- **Default batch size:** 50 jobs
- **Rate limiting:** 1 seconde tussen jobs
- **Automatic limiting:** Als meer dan 50 jobs worden aangeboden, worden alleen de eerste 50 verwerkt

**Voorbeeld:**
```python
# Process max 50 jobs with 1s delay between each
stats = batch_enrich_jobs(job_ids, batch_size=50, delay_between_jobs=1.0)

# Output:
# {
#   "total": 50,
#   "successful": 48,
#   "failed": 2,
#   "rate_limited": 1
# }
```

### 3. **UI Improvements** ✅

**Implementatie:** `web/templates/jobs.html` - `enrichAllUnenriched()`

**Features:**
- Toont batch size in confirm dialog
- Geeft aan hoeveel jobs nog over zijn
- Schat verwachte tijd (~1 job/seconde)
- Instrueert gebruiker om opnieuw te klikken voor volgende batch

**Voorbeeld Dialog:**
```
Enrich 50 jobs?

(645 total unenriched, processing in batches of 50)

This will run in the background and may take a few minutes.

[OK] [Cancel]
```

**Result Dialog:**
```
Enrichment started in background!
50 jobs will be enriched.

595 jobs remaining. Click "Enrich All" again after this batch completes.

Estimated time: ~1 minute(s)
```

## Retry Logica Details

### Rate Limit Handling

```python
try:
    response = client.responses.create(...)
except RateLimitError as e:
    # Exponential backoff
    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
    time.sleep(wait_time)
    # Retry...
```

**Backoff Schema:**
- Attempt 1: Wait 5 seconds
- Attempt 2: Wait 10 seconds  
- Attempt 3: Wait 20 seconds
- Total max wait: 35 seconds per job

### API Error Handling

```python
except APIError as e:
    # Shorter backoff for API errors
    wait_time = (2 ** attempt) * 3  # 3s, 6s, 12s
    time.sleep(wait_time)
    # Retry...
```

### JSON Parse Error Handling

```python
except json.JSONDecodeError as e:
    # No retry - save error to database
    error_msg = f"Invalid JSON in LLM response: {str(e)}"
    save_enrichment_error_to_db(job_id, error_msg)
    return None, error_msg
```

## Batch Processing Details

### Rate Limiting Between Jobs

```python
for i, job_id in enumerate(job_ids, 1):
    result = process_job_enrichment(job_id)
    
    # Wait between jobs (except last)
    if i < len(job_ids):
        time.sleep(delay_between_jobs)  # Default: 1.0s
```

**Voordelen:**
- ✅ Voorkomt rate limits
- ✅ ~60 jobs per minuut (met 1s delay)
- ✅ Batch van 50 jobs = ~1 minuut

### Batch Size Limiting

```python
if len(job_ids) > batch_size:
    logger.warning(f"Batch size limited from {len(job_ids)} to {batch_size} jobs")
    job_ids = job_ids[:batch_size]
```

**Waarom 50 jobs?**
- ✅ Voorkomt lange-lopende background tasks
- ✅ Geeft gebruiker feedback na elke batch
- ✅ Makkelijker te monitoren
- ✅ Minder kans op timeouts

## Workflow

### Gebruiker Workflow

1. **Klik "Enrich All"**
   - Ziet: "Enrich 50 jobs? (645 total, batches of 50)"
   - Klik OK

2. **Enrichment Start**
   - Ziet: "50 jobs will be enriched. 595 remaining. ~1 minute"
   - Background process start

3. **Wacht ~1 Minuut**
   - Monitor progress in server logs
   - Of gebruik `python monitor_enrichment.py`

4. **Klik Opnieuw "Enrich All"**
   - Ziet: "Enrich 50 jobs? (595 total, batches of 50)"
   - Repeat...

5. **Laatste Batch**
   - Ziet: "Enrich 45 jobs?" (geen batch size warning)
   - Done! ✅

### Background Process Workflow

```
For each job in batch (max 50):
  1. Try to enrich with LLM
  2. If rate limit → Wait 5s, retry
  3. If rate limit again → Wait 10s, retry
  4. If rate limit again → Wait 20s, retry
  5. If still fails → Save error to DB
  6. Wait 1s before next job
```

## Error Handling

### Rate Limit Errors

**Symptom:** `RateLimitError: Rate limit exceeded`

**Handling:**
- ✅ Automatic retry met exponential backoff
- ✅ Max 3 retries (35s total wait)
- ✅ Als nog steeds fails → Error opgeslagen in DB
- ✅ Retry na 24u via auto-enrichment service

**Logs:**
```
⚠️  Rate limit hit for job abc123. Waiting 5s before retry 1/3
⚠️  Rate limit hit for job abc123. Waiting 10s before retry 2/3
✅ Successfully enriched job abc123
```

### JSON Parse Errors

**Symptom:** `Invalid JSON in LLM response`

**Handling:**
- ❌ Geen retry (LLM output is corrupt)
- ✅ Error opgeslagen in DB
- ✅ Retry na 24u (misschien beter LLM output)

**Logs:**
```
❌ Failed to enrich job abc123: Invalid JSON in LLM response: line 26 column 5
```

### API Errors

**Symptom:** `APIError: Service unavailable`

**Handling:**
- ✅ Automatic retry met backoff (3s, 6s, 12s)
- ✅ Max 3 retries
- ✅ Als fails → Error opgeslagen

## Monitoring

### Real-Time Monitoring

```bash
python monitor_enrichment.py
```

**Output:**
```
[20:52:00] Enriched: 140/785 (17.8%) | Errors: 8 | Remaining: 645 (+5 since last check)
```

### Check Stats

```bash
python -c "
from database.client import db

enriched = db.client.table('llm_enrichment')\
    .select('job_posting_id', count='exact')\
    .not_.is_('enrichment_completed_at', 'null')\
    .execute()

print(f'Enriched: {enriched.count}')
"
```

### Server Logs

Watch background enrichment:
```bash
# In terminal waar server draait
🔄 Background batch enrichment started for 50 jobs
✅ Successfully enriched job abc123
⚠️  Rate limit hit for job def456. Waiting 5s...
✅ Background batch enrichment complete: 48 successful, 2 failed
```

## Configuration

### Adjust Batch Size

**In `ingestion/llm_enrichment.py`:**
```python
def batch_enrich_jobs(job_ids, batch_size=50, delay_between_jobs=1.0):
    # Change batch_size to 100 for faster processing (more rate limit risk)
    # Change delay_between_jobs to 0.5 for faster (more rate limit risk)
```

**In `web/templates/jobs.html`:**
```javascript
const batchSize = 50;  // Match backend batch size
```

### Adjust Retry Settings

**In `ingestion/llm_enrichment.py`:**
```python
def enrich_job_with_llm(job_id, description, max_retries=3):
    # Change max_retries to 5 for more resilience
    
    # Adjust backoff times:
    wait_time = (2 ** attempt) * 5  # Change multiplier
```

## Testing

### Test Retry Logic

```python
from ingestion.llm_enrichment import enrich_job_with_llm

# This will retry on rate limits
data, error = enrich_job_with_llm("test-job-id", "test description")
```

### Test Batch Processing

```python
from ingestion.llm_enrichment import batch_enrich_jobs

# Process 10 jobs with 0.5s delay
stats = batch_enrich_jobs(job_ids[:10], batch_size=10, delay_between_jobs=0.5)
print(stats)
```

### Test UI

1. Go to `/jobs`
2. Click "Enrich All"
3. Check dialog shows batch size
4. Check result shows remaining jobs

## Performance

### Expected Throughput

**With default settings:**
- Batch size: 50 jobs
- Delay: 1s between jobs
- Retries: Up to 3 per job

**Best case:** 50 jobs in ~50 seconds (~1 job/sec)
**Worst case:** 50 jobs in ~3 minutes (with retries)
**Average:** 50 jobs in ~1 minute

### Full Enrichment Time

**For 645 unenriched jobs:**
- Batches needed: 13 (645 / 50)
- Time per batch: ~1 minute
- Total time: ~13 minutes
- User clicks needed: 13

## Future Improvements

- [ ] Automatic batch continuation (no user clicks)
- [ ] Progress bar in UI
- [ ] WebSocket updates for real-time progress
- [ ] Configurable batch size in UI
- [ ] Pause/Resume functionality
- [ ] Priority queue for important jobs
