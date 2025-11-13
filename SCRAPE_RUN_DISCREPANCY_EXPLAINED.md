# Scrape Run Discrepancy: "1 job found" but "No jobs in history"

## Problem Description

You encountered a scrape run that shows:
- **Jobs found**: 1
- **Jobs in history**: 0 (no jobs visible in UI)

Run ID: `3830cbff-3699-47d2-88e4-0ed41ce8b048`

## Root Cause

The discrepancy occurs because:

1. **`jobs_found`** = Number of jobs returned by Bright Data API
2. **Jobs in `job_scrape_history`** = Number of jobs **successfully processed** into database

### Why the difference?

In `ingestion/processor.py`, the function `process_job_posting()`:

```python
def process_job_posting(raw_job, scrape_run_id, source):
    try:
        # Step 1: Parse and validate with Pydantic
        try:
            if source == "indeed":
                job = IndeedJobPosting(**raw_job)  # ← Can fail with ValidationError
        except ValidationError as e:
            return ProcessingResult(status='error', error=str(e))  # ← Returns early!
        
        # ... process company, location, etc ...
        
        # Step 7: Record in scrape history
        db.insert_scrape_history(job_id, scrape_run_id)  # ← NEVER REACHED if error above!
        
    except Exception as e:
        return ProcessingResult(status='error', error=str(e))
```

**The issue**: `insert_scrape_history()` is only called **after successful processing**. If there's a ValidationError or any other exception, this line is never reached.

## Common Causes of Processing Failures

1. **ValidationError**: Required field missing in API response
   - Example: Indeed API returns job without `job_title`
   - Pydantic validation fails immediately

2. **Database errors**: 
   - Company/location insert fails
   - Duplicate key violations (rare)

3. **Data quality issues**:
   - Malformed location strings
   - Invalid date formats
   - Missing company information

## Solution Implemented

### ✅ Track Error Count in Metadata

Modified `scraper/orchestrator.py` to save error details:

```python
db.update_scrape_run(run_id, {
    "status": "completed",
    "jobs_found": len(jobs_data),
    "jobs_new": batch_result.new_count,
    "jobs_updated": batch_result.updated_count,
    "metadata": {
        "jobs_error": batch_result.error_count,  # ← NEW
        "error_details": batch_result.error_details  # ← NEW
    }
})
```

### ✅ Expose Errors in API

Modified `web/api/runs.py` to include error information:

```python
return {
    "jobs_found": run.get("jobs_found", 0),
    "jobs_new": run.get("jobs_new", 0),
    "jobs_updated": run.get("jobs_updated", 0),
    "jobs_error": metadata.get("jobs_error", 0),  # ← NEW
    "error_details": metadata.get("error_details", [])  # ← NEW
}
```

## How to Debug This Issue

### 1. Check the scrape run metadata

```sql
SELECT 
    id,
    search_query,
    location_query,
    jobs_found,
    jobs_new,
    jobs_updated,
    metadata->'jobs_error' as jobs_error,
    metadata->'error_details' as error_details
FROM scrape_runs
WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048';
```

### 2. Check if any jobs were created around that time

```sql
SELECT 
    jp.id,
    jp.title,
    jp.created_at,
    c.name as company_name
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
WHERE jp.created_at BETWEEN 
    (SELECT started_at FROM scrape_runs WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048') 
    AND 
    (SELECT completed_at FROM scrape_runs WHERE id = '3830cbff-3699-47d2-88e4-0ed41ce8b048');
```

### 3. Check job_scrape_history

```sql
SELECT COUNT(*) 
FROM job_scrape_history 
WHERE scrape_run_id = '3830cbff-3699-47d2-88e4-0ed41ce8b048';
```

## Expected Behavior Going Forward

After this fix, you'll see:

```
Run: "BI Developer" in Belgium
✅ Jobs found: 1
✅ Jobs new: 0
✅ Jobs updated: 0
❌ Jobs error: 1
📋 Error details: ["ValidationError: field required (job_title)"]
```

This makes it clear that:
- Bright Data found 1 job
- But we couldn't process it due to validation error
- The specific error is shown in `error_details`

## UI Improvements Needed

The frontend should display:
1. **Jobs found** (from Bright Data)
2. **Jobs processed** (new + updated)
3. **Jobs failed** (with expandable error details)

Example:
```
📊 Run Results:
   • Found: 1 job
   • Processed: 0 jobs
   • Failed: 1 job (click to see errors)
```

## Prevention

To reduce processing failures:

1. **Make more fields optional** in Pydantic models
2. **Add better error handling** for malformed data
3. **Log raw job data** when validation fails
4. **Add retry logic** for transient database errors

## Related Files

- `ingestion/processor.py` - Job processing logic
- `scraper/orchestrator.py` - Scrape run orchestration
- `models/indeed.py` - Indeed job validation model
- `web/api/runs.py` - API endpoints for run details
