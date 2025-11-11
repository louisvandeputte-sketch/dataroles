# Job Enrichment Error Tracking - Implementatie

## Probleem

Wanneer een job enrichment faalt (bijv. door OpenAI API quota, parsing errors, etc.), wordt er **geen error opgeslagen** in de database. Het record blijft gewoon leeg, waardoor:
- Het lijkt alsof de job nooit geprobeerd werd te enrichen
- Je niet kunt zien waarom het gefaald is
- Je niet weet welke jobs opnieuw geprobeerd moeten worden

**Voorbeeld:**
```
Job: "Artificial Intelligence Engineer"
Company: Randstad Digital Belgium
Status: Lijkt "unenriched" maar is eigenlijk gefaald
Reden: Onbekend (niet opgeslagen)
```

## Oplossing

### 1. Database Migratie

**Bestand:** `database/migrations/025_add_llm_enrichment_error.sql`

Voegt `enrichment_error` kolom toe aan `llm_enrichment` tabel:
- Slaat error message op wanneer enrichment faalt
- Indexes voor filtering en retry logic
- Timestamp blijft behouden voor tracking

**Uitvoeren:**
```sql
-- Kopieer de SQL uit 025_add_llm_enrichment_error.sql
-- Run in Supabase SQL Editor
```

### 2. Code Aanpassingen

**Bestand:** `ingestion/llm_enrichment.py`

#### Nieuwe functie: `save_enrichment_error_to_db()`
```python
def save_enrichment_error_to_db(job_id: str, error_message: str) -> bool:
    """Save enrichment error to database."""
    # Updates llm_enrichment with error message
    # Sets enrichment_completed_at to track attempt time
```

#### Aangepaste functie: `enrich_job_with_llm()`
```python
# Voorheen: return Optional[Dict[str, Any]]
# Nu: return tuple[Optional[Dict[str, Any]], Optional[str]]

# Returns: (enrichment_data, error_message)
```

#### Aangepaste functie: `process_job_enrichment()`
```python
# Nu roept het save_enrichment_error_to_db() aan bij falen
enrichment_data, error_message = enrich_job_with_llm(job_id, description)

if not enrichment_data:
    save_enrichment_error_to_db(job_id, error_message)
    return {"success": False, "error": error_message}
```

#### Aangepaste functie: `save_enrichment_to_db()`
```python
# Cleared enrichment_error bij succesvolle enrichment
"enrichment_error": None  # Clear any previous error
```

## Voordelen

### ✅ Zichtbaarheid
- Alle gefaalde enrichments zijn nu zichtbaar in database
- Error messages tonen exacte reden van falen
- Timestamps tonen wanneer het geprobeerd werd

### ✅ Debugging
```python
# Vind alle gefaalde enrichments
SELECT job_posting_id, enrichment_error, enrichment_completed_at
FROM llm_enrichment
WHERE enrichment_error IS NOT NULL
ORDER BY enrichment_completed_at DESC;
```

### ✅ Retry Logic
```python
# Vind jobs die retry nodig hebben
SELECT job_posting_id, enrichment_error
FROM llm_enrichment
WHERE enrichment_error IS NOT NULL
  AND enrichment_completed_at IS NULL;
```

### ✅ Monitoring
- Track error types (quota exceeded, parsing errors, etc.)
- Identify patterns in failures
- Monitor API health

## Gebruik

### 1. Vind gefaalde enrichments
```bash
python find_failed_job_enrichments.py
```

Output:
```
❌ Jobs with Enrichment Errors:
1. Artificial Intelligence Engineer
   Company: Randstad Digital Belgium
   Failed at: 2025-11-07T13:15:00
   Error: Error code: 429 - You exceeded your current quota...

2. Senior Data Scientist
   Company: Acme Corp
   Failed at: 2025-11-07T12:30:00
   Error: Could not extract structured output from API response
```

### 2. Re-enrich gefaalde jobs

**Via API:**
```bash
# Single job
curl -X POST "http://localhost:8000/api/jobs/{job_id}/enrich?force=true"

# Batch
curl -X POST "http://localhost:8000/api/jobs/enrich/batch" \
  -H "Content-Type: application/json" \
  -d '{"job_ids": ["job-id-1", "job-id-2"]}'
```

**Via Python:**
```python
from ingestion.llm_enrichment import process_job_enrichment

# Re-enrich with force=True
result = process_job_enrichment(job_id, force=True)
```

### 3. Monitor error types

```sql
-- Count errors by type
SELECT 
  CASE 
    WHEN enrichment_error LIKE '%quota%' THEN 'Quota Exceeded'
    WHEN enrichment_error LIKE '%extract%' THEN 'Parsing Error'
    WHEN enrichment_error LIKE '%timeout%' THEN 'Timeout'
    ELSE 'Other'
  END as error_type,
  COUNT(*) as count
FROM llm_enrichment
WHERE enrichment_error IS NOT NULL
GROUP BY error_type;
```

## Error Types

### 1. **OpenAI API Quota Exceeded**
```
Error code: 429 - You exceeded your current quota, please check your plan and billing details
```
**Oplossing:** Wacht tot quota reset of upgrade plan

### 2. **Parsing Error**
```
Could not extract structured output from API response
```
**Oplossing:** Check prompt versie en output format

### 3. **Timeout**
```
Request timeout after 300 seconds
```
**Oplossing:** Check API status, retry later

### 4. **Invalid JSON**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```
**Oplossing:** Check LLM output format, mogelijk prompt issue

## Migratie Checklist

- [ ] Run database migratie `025_add_llm_enrichment_error.sql`
- [ ] Code is al geüpdatet in `ingestion/llm_enrichment.py`
- [ ] Test met een job die faalt (bijv. tijdens quota exceeded)
- [ ] Verify error wordt opgeslagen in database
- [ ] Test re-enrichment met `force=True`
- [ ] Verify error wordt gecleared bij succesvolle enrichment

## Toekomstige Verbeteringen

1. **Automatic Retry Logic**
   - Retry gefaalde jobs automatisch na X tijd
   - Exponential backoff voor rate limiting
   - Max retry attempts tracking

2. **Error Notifications**
   - Alert bij hoge error rate
   - Daily summary van gefaalde enrichments
   - Slack/email notifications

3. **Analytics Dashboard**
   - Visualiseer error trends
   - Success rate over tijd
   - Error type breakdown

4. **Batch Retry Command**
   ```bash
   python retry_failed_enrichments.py --error-type="quota" --max-retries=3
   ```
