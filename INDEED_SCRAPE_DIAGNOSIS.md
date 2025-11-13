# Indeed Scrape Run Diagnosis

## Problem Statement

Indeed scrape runs consistently show:
- ✅ `jobs_found: 1` (Bright Data API returns jobs)
- ❌ `jobs_new: 0` 
- ❌ `jobs_updated: 0`
- ❌ `jobs_error: 1` (all jobs fail processing)
- ❌ No jobs in `job_scrape_history`

**Affected Runs:**
- `3830cbff-3699-47d2-88e4-0ed41ce8b048` - "BI Developer" in Belgium
- `9394dedf-62ef-40cb-ad26-3c5e9f9c05dc` - "BI Developer" in Belgium  
- `5bd808d2-b450-438c-9bd3-40478667f1bd` - "BI Developer" in Belgium

## Root Cause Analysis

### 1. Error Tracking Works ✅

The error tracking system is working correctly:
```json
{
  "jobs_error": "1",
  "error_details": [
    {
      "error": "Field 'X': field required"
    }
  ]
}
```

### 2. Validation Failure ❌

Jobs from Bright Data Indeed API are **failing Pydantic validation** in `models/indeed.py`.

**The Flow:**
```
Bright Data API → Raw JSON
    ↓
IndeedJobPosting(**raw_job)  ← ValidationError here!
    ↓
ProcessingResult(status='error')
    ↓
NO insert_scrape_history() call
    ↓
Result: jobs_found=1, but jobs_error=1, history=0
```

## Investigation Steps

### Step 1: Check Error Details

Run this SQL query in Supabase:

```sql
SELECT 
    metadata->>'jobs_error' as jobs_error,
    metadata->'error_details' as error_details
FROM scrape_runs
WHERE id = '5bd808d2-b450-438c-9bd3-40478667f1bd';
```

**Expected Output:**
```json
{
  "jobs_error": "1",
  "error_details": [
    {
      "error": "Field 'some_field': field required"
    }
  ]
}
```

### Step 2: Identify Missing Field

The error message will tell you which field is missing. Common culprits:

**Required fields in `models/indeed.py`:**
- `jobid`
- `job_title`
- `company_name`
- `location`
- `url`
- `description_text`

**If Bright Data doesn't provide one of these**, validation fails.

### Step 3: Check Bright Data Response

The raw response from Bright Data might be missing fields. Common issues:

1. **Field name mismatch**: Bright Data uses different field names
2. **Missing optional data**: Job doesn't have all fields
3. **API changes**: Bright Data changed their response format

## Solution Options

### Option A: Make Fields Optional (RECOMMENDED)

Make non-critical fields optional in `models/indeed.py`:

```python
# Before (required):
job_title: str

# After (optional):
job_title: Optional[str] = None
```

**Which fields to make optional?**
- Keep `jobid` required (unique identifier)
- Keep `url` required (link to job)
- Make everything else optional with sensible defaults

### Option B: Add Default Values

For fields that should always exist, add defaults:

```python
description_text: str = ""  # Empty string if missing
company_name: str = "Unknown Company"
```

### Option C: Pre-process Raw Data

Add a preprocessing step before validation:

```python
def preprocess_indeed_job(raw_job: Dict) -> Dict:
    """Ensure all required fields exist."""
    defaults = {
        "job_title": "Untitled Position",
        "company_name": "Unknown Company",
        "description_text": "",
        "location": "Unknown"
    }
    return {**defaults, **raw_job}
```

## Recommended Fix

### 1. Update `models/indeed.py`

Make most fields optional except core identifiers:

```python
class IndeedJobPosting(BaseModel):
    """Indeed job posting model."""
    
    # Core required fields (must have)
    jobid: str
    url: str
    
    # Important but optional
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    description_text: Optional[str] = ""
    
    # All other fields already optional
    # ...
```

### 2. Add Validation in Processor

Add a check after validation to skip jobs with missing critical data:

```python
# In ingestion/processor.py
job = IndeedJobPosting(**raw_job)

# Skip if missing critical fields
if not job.job_title or not job.company_name:
    logger.warning(f"Skipping job {job.jobid}: missing critical fields")
    return ProcessingResult(
        status='error', 
        error=f"Missing critical fields: title={bool(job.job_title)}, company={bool(job.company_name)}"
    )
```

### 3. Add Logging for Raw Data

When validation fails, log the raw job data:

```python
except ValidationError as e:
    logger.error(f"ValidationError for {source} job {job_id_field}")
    logger.error(f"Raw job data: {json.dumps(raw_job, indent=2)}")  # ← ADD THIS
    # ...
```

## Testing Plan

### 1. Run Analysis Script

```bash
python3 analyze_indeed_error.py
```

This will show you the exact error from the latest run.

### 2. Test Validation Locally

```bash
python3 test_indeed_job_validation.py
```

This shows which fields are required vs optional.

### 3. Trigger New Test Run

After deploying fixes:
1. Go to Indeed Queries page
2. Trigger "BI Developer" in Belgium
3. Wait for completion
4. Check error details in UI
5. Verify jobs appear in history

## Expected Behavior After Fix

### Scenario 1: Valid Job
```
Jobs found: 1
Jobs new: 1
Jobs updated: 0
Jobs error: 0
Jobs in history: 1 ✅
```

### Scenario 2: Job Missing Optional Field
```
Jobs found: 1
Jobs new: 1  ← Still processes!
Jobs updated: 0
Jobs error: 0
Jobs in history: 1 ✅
```

### Scenario 3: Job Missing Critical Field
```
Jobs found: 1
Jobs new: 0
Jobs updated: 0
Jobs error: 1
Error: "Missing critical fields: title=False"
Jobs in history: 0
```

## Files to Check

1. **`models/indeed.py`** - Validation model
2. **`ingestion/processor.py`** - Processing logic
3. **`clients/brightdata_indeed.py`** - API client
4. **`scraper/orchestrator.py`** - Run orchestration

## Debugging Commands

```bash
# Check specific run
psql $DATABASE_URL -f check_run_5bd808d2.sql

# Analyze error
python3 analyze_indeed_error.py

# Test validation
python3 test_indeed_job_validation.py

# Monitor new run
python3 monitor_new_run.py
```

## Next Actions

1. ✅ Run `analyze_indeed_error.py` to see exact error
2. ⏳ Make fields optional in `models/indeed.py`
3. ⏳ Add raw data logging for debugging
4. ⏳ Deploy fix
5. ⏳ Test with new run
6. ⏳ Verify jobs appear in UI
