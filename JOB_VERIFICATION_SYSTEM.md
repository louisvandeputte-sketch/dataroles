# Job Verification System (LinkedIn & Indeed)

## Overzicht

Het Job Verification System controleert periodiek of actieve LinkedIn en Indeed jobs nog bestaan door hun URLs te verifiëren via de Bright Data API. Dit lost het probleem op dat jobs die niet meer in recente scrapes verschijnen (omdat ze ouder zijn dan de lookback periode) toch nog actief kunnen zijn op de job platforms.

## Probleem

**Oorspronkelijke situatie:**
- Scraper zoekt alleen jobs gepost in laatste 24u (`lookback_days=1`)
- Jobs ouder dan 24u verschijnen niet meer in scrape resultaten
- `last_seen_at` wordt niet meer bijgewerkt
- Na 14 dagen worden ze ten onrechte als "inactief" gemarkeerd

**Nieuwe oplossing:**
- Periodieke verificatie via Bright Data URL-based scraping
- Controleert of job nog bestaat op LinkedIn
- Update `last_seen_at` voor actieve jobs
- Markeert alleen echt verwijderde jobs als inactief

## Architectuur

### Components

1. **`services/job_verification.py`**
   - `JobVerificationService`: Main service class (supports both LinkedIn & Indeed)
   - `verify_active_jobs()`: Verify all active jobs in batches
   - `verify_single_job()`: Verify one specific job
   - `_fetch_jobs_by_url()`: Call Bright Data API with URLs

2. **`clients/brightdata_linkedin.py`**
   - `trigger_collection_by_urls()`: Trigger LinkedIn URL-based scraping
   - `get_snapshot_data()`: Wait for and retrieve results

3. **`clients/brightdata_indeed.py`**
   - `trigger_collection_by_urls()`: Trigger Indeed URL-based scraping
   - `get_snapshot_data()`: Wait for and retrieve results

3. **`scheduler/service.py`**
   - Scheduled task: Daily at 3:00 AM
   - Calls `_verify_active_jobs()`

4. **`web/api/quality.py`**
   - `POST /api/quality/verify-jobs`: Manual trigger endpoint

## Gebruik

### Automatische Verificatie

De verificatie draait automatisch **dagelijks om 3:00 AM** via de scheduler.

### Handmatige Verificatie

Via API endpoint:

```bash
# Verify both LinkedIn and Indeed
curl -X POST "http://localhost:8000/api/quality/verify-jobs?batch_size=100&only_data_jobs=true"

# Verify only LinkedIn
curl -X POST "http://localhost:8000/api/quality/verify-jobs?batch_size=100&only_data_jobs=true&source=linkedin"

# Verify only Indeed
curl -X POST "http://localhost:8000/api/quality/verify-jobs?batch_size=100&only_data_jobs=true&source=indeed"
```

Parameters:
- `batch_size`: Aantal jobs per batch (default: 100)
- `only_data_jobs`: Alleen Data jobs verifiëren (default: true)
- `source`: Filter op bron ('linkedin', 'indeed', of None voor beide)

### Test Script

```bash
python test_job_verification.py
```

Test met kleine batch (10 jobs) om de functionaliteit te verifiëren.

## Logica

### Job Selection

Selecteert jobs die:
- `is_active = true`
- `source = 'linkedin'` OF `source = 'indeed'`
- `linkedin_job_id IS NOT NULL` (voor LinkedIn) OF `indeed_job_id IS NOT NULL` (voor Indeed)
- `title_classification = 'Data'` (optioneel)

### Verificatie Process

1. **Batch ophalen**: Haal actieve jobs op uit database
2. **URLs verzamelen**: Extract LinkedIn URLs
3. **API call**: Trigger Bright Data URL-based scraping
4. **Wacht op resultaten**: Poll snapshot status
5. **Vergelijk**:
   - Job gevonden + heeft title → **Nog actief** → Update `last_seen_at`
   - Job niet gevonden of geen title → **Inactief** → Mark as inactive

### Batch Processing

- Verwerkt jobs in batches (default: 100)
- 60 seconden wachttijd tussen batches (rate limiting)
- Error handling per batch (fouten stoppen niet hele proces)

## API Response Format

### LinkedIn Format

```json
{
  "job_posting_id": "4295969377",
  "job_title": "RN New Graduate Nurse...",
  "company_name": "UNC Health",
  "url": "https://www.linkedin.com/jobs/view/...",
  "job_location": "Raleigh, NC",
  ...
}
```

**Verificatie checks:**
- `job_posting_id` matched met `linkedin_job_id`
- `job_title` is niet null/empty → Job bestaat nog

### Indeed Format

```json
{
  "jobid": "9ee264f79ab0f217",
  "job_title": "Contact Center Agent I",
  "company_name": "Broadspire Services, Inc.",
  "url": "https://www.indeed.com/rc/clk?jk=...",
  "job_location": "Remote in United States",
  ...
}
```

**Verificatie checks:**
- `jobid` matched met `indeed_job_id`
- `job_title` is niet null/empty → Job bestaat nog

## Performance

### Timing
- **Per batch (100 jobs)**: ~2-5 minuten (Bright Data processing)
- **Totaal voor 1000 jobs**: ~30-60 minuten
- **Scheduled run**: Dagelijks om 3:00 AM (lage load periode)

### Kosten
- Bright Data API credits per URL
- Alleen Data jobs (filter reduceert volume)
- Batch processing voorkomt rate limits

## Monitoring

### Logs

```
🔍 Starting LinkedIn job verification...
Found 250 jobs to verify
Processing batch 1 (100 jobs)
Fetching 100 job URLs from Bright Data...
✅ Job still active: Senior Data Engineer
❌ Job inactive (not found): Junior Data Analyst
✅ Verification complete: 250 verified, 230 still active, 20 marked inactive, 0 errors
```

### Stats Response

```json
{
  "verified": 250,
  "still_active": 230,
  "marked_inactive": 20,
  "errors": 0
}
```

## Configuratie

### Settings

In `config/settings.py`:
```python
BRIGHTDATA_API_TOKEN = "..."
BRIGHTDATA_LINKEDIN_DATASET_ID = "gd_..."
```

### Scheduler

In `scheduler/service.py`:
```python
# Runs daily at 3:00 AM
trigger=CronTrigger(hour=3, minute=0)
```

Aanpassen naar andere tijd:
```python
trigger=CronTrigger(hour=2, minute=30)  # 2:30 AM
```

## Error Handling

### API Errors
- Timeout: Continue met volgende batch
- Rate limit: Wacht 60s tussen batches
- Quota exceeded: Log error, stop verificatie

### Database Errors
- Job not found: Skip, log warning
- Update failed: Log error, continue met volgende

### Network Errors
- Retry logic in Bright Data client
- Batch isolation (één fout stopt niet alles)

## Toekomstige Verbeteringen

1. **Incremental Verification**
   - Prioriteer jobs die lang niet geverifieerd zijn
   - Track `last_verified_at` timestamp

2. **Smart Scheduling**
   - Vaker verifiëren voor nieuwe jobs
   - Minder vaak voor oude, stabiele jobs

3. **Multi-Source Support**
   - Ook Indeed jobs verifiëren
   - Verschillende verificatie strategieën per bron

4. **Notification System**
   - Alert bij veel inactieve jobs
   - Weekly summary email

## Troubleshooting

### "No jobs to verify"
- Check: Zijn er actieve LinkedIn jobs in database?
- Check: Filter `only_data_jobs=true` te restrictief?

### "Bright Data API timeout"
- Check: API credentials correct?
- Check: Quota niet overschreden?
- Verlaag `batch_size`

### "Jobs marked inactive but still on LinkedIn"
- Check: Bright Data API response format
- Check: `job_title` parsing logic
- Run manual verification voor specifieke job

## Files

```
services/
  job_verification.py          # Main verification service

clients/
  brightdata_linkedin.py       # Bright Data API client (extended)

scheduler/
  service.py                   # Scheduler with verification task

web/api/
  quality.py                   # API endpoint for manual trigger

test_job_verification.py       # Test script
JOB_VERIFICATION_SYSTEM.md     # This documentation
```
