# Scrape Architecture

## Overview

The scraping system is designed to collect LinkedIn job postings via Bright Data's API, process them through an ingestion pipeline, and store them in the database with deduplication and change tracking.

## Components

### 1. Orchestrator (`scraper/orchestrator.py`)

**Main entry point** for executing scrape runs.

**Flow:**
1. Determine date range (incremental scraping)
2. Create `scrape_run` record (status='running')
3. Trigger Bright Data collection
4. Wait for completion (polling)
5. Process jobs through ingestion pipeline
6. Update scrape_run with results
7. Assign job types

**Key Function:**
```python
async def execute_scrape_run(
    query: str,
    location: str,
    lookback_days: Optional[int] = None,
    trigger_type: str = "manual",
    search_query_id: Optional[str] = None,
    job_type_id: Optional[str] = None
) -> ScrapeRunResult
```

### 2. Bright Data Client (`clients/brightdata_linkedin.py`)

**Handles all communication** with Bright Data API.

**Key Methods:**
- `trigger_collection()` - Start a new scrape
- `wait_for_completion()` - Poll until ready
- `download_results()` - Get job data
- `get_snapshot_status()` - Check progress

**Error Handling:**
- Timeout exceptions (30s connect, 5min read)
- Rate limiting (429, 402 errors)
- Race condition validation (building status)

### 3. Ingestion Pipeline (`ingestion/processor.py`)

**Processes raw job data** from Bright Data.

**Flow:**
1. Parse LinkedIn JSON format
2. Extract company info
3. Deduplicate by `job_posting_id`
4. Detect changes (title, description, etc.)
5. Update or insert job posting
6. Track in `job_scrape_history`

**Key Functions:**
- `process_job_posting()` - Single job
- `process_jobs_batch()` - Batch processing

### 4. Date Strategy (`scraper/date_strategy.py`)

**Determines optimal lookback period** for incremental scraping.

**Logic:**
- Check last successful run for query+location
- Default: 7 days (past_week)
- If recent run: 1 day (past_24h)
- Manual override supported

## Data Flow

```
User/Scheduler
    ↓
Orchestrator
    ↓
Bright Data Client → [Bright Data API]
    ↓
Raw Jobs (JSON)
    ↓
Ingestion Pipeline
    ↓
Database (job_postings, job_scrape_history, scrape_runs)
```

## Database Schema

### `scrape_runs`
Tracks each scrape execution:
- `id` - UUID
- `search_query` - Keyword
- `location_query` - Location
- `status` - running/completed/failed
- `jobs_found` - Total jobs
- `jobs_new` - New jobs
- `jobs_updated` - Updated jobs
- `metadata` - JSON (snapshot_id, duration, etc.)

### `job_postings`
Stores job data:
- `id` - UUID
- `job_posting_id` - LinkedIn ID (unique)
- `title`, `description`, `company_name`, etc.
- `first_seen_at`, `last_seen_at`
- `is_active` - Boolean

### `job_scrape_history`
Tracks when jobs were seen:
- `job_posting_id` - FK to job_postings
- `scrape_run_id` - FK to scrape_runs
- `scraped_at` - Timestamp
- `change_detected` - Boolean

## Error Handling

### Timeout Protection
- HTTP client: 30s connect, 5min read
- Snapshot polling: 30min max (configurable)
- Explicit timeout exceptions

### Race Condition Handling
Bright Data sometimes returns `{"status": "building"}` even after status check shows "ready":
```python
if isinstance(data, dict) and data.get("status") == "building":
    raise BrightDataError("Snapshot still building (race condition)")
```

### Error Propagation
All errors are:
1. Logged with full traceback
2. Stored in `scrape_runs.error_message`
3. Include error type and duration
4. Return proper `ScrapeRunResult`

## Configuration

### Environment Variables
```bash
BRIGHTDATA_API_TOKEN=xxx
BRIGHTDATA_DATASET_ID=gd_xxx
USE_MOCK_API=false  # Use mock for testing
```

### Timeouts
- HTTP connect: 30s
- HTTP read: 300s (5min)
- Snapshot polling: 1800s (30min)
- Poll interval: 30s

## Testing

See `tests/README.md` for available test scripts.

**Quick test:**
```bash
python tests/test_scrape_flow.py
```

## Troubleshooting

### Runs hang without results
- Check Bright Data API status
- Verify credentials
- Check timeout logs
- Look for race condition errors

### Jobs not deduplicating
- Verify `job_posting_id` is unique
- Check `job_scrape_history` entries
- Review change detection logic

### Rate limiting
- Bright Data has quota limits
- 429/402 errors indicate limit reached
- Check subscription status

## Future Improvements

1. **Retry logic** - Auto-retry on transient errors
2. **Parallel scraping** - Multiple queries simultaneously
3. **Better progress tracking** - Real-time job counts
4. **Webhook support** - Bright Data can push results
5. **Cost optimization** - Smarter date ranges
