# Indeed Scrape Troubleshooting Checklist

## Current Status
- ✅ Error tracking works
- ✅ Field aliases added (job_id, title, company, etc.)
- ✅ Pydantic v2 ConfigDict syntax
- ✅ Most fields now optional
- ❌ Still getting 0 jobs processed

## Possible Root Causes

### 1. Bright Data Returns Empty Response
**Symptom:** `jobs_found: 1` but validation fails
**Cause:** Bright Data API returns incomplete/malformed data

**Check:**
```sql
SELECT metadata->>'snapshot_id' 
FROM scrape_runs 
WHERE id = 'b7848148-895c-42ce-86de-f1245799ea61';
```

Then manually check Bright Data dashboard for that snapshot.

### 2. Field Names Still Wrong
**Symptom:** `Field 'X': Field required` errors
**Cause:** Bright Data uses different field names than we expect

**Solution:** Add more aliases or make field optional

### 3. Bright Data API Changed
**Symptom:** Consistent failures across all runs
**Cause:** Bright Data changed their Indeed API response format

**Check:** Compare old successful runs (if any) with current failures

### 4. Wrong Dataset ID
**Symptom:** No jobs or wrong data structure
**Cause:** Using wrong Bright Data dataset ID

**Current:** `gd_l4dx9j9sscpvs7no2`
**Check:** Verify this is correct in Bright Data dashboard

### 5. Location/Country Detection Issue
**Symptom:** Jobs found but not for Belgium
**Cause:** Location parsing fails, searches wrong country

**Check:**
```python
# In clients/brightdata_indeed.py
location_lower = "belgium".lower()
if "belgium" in location_lower:
    country = "BE"
    domain = "be.indeed.com"
```

### 6. Raw Data Not Logged
**Symptom:** Can't see what Bright Data actually returns
**Cause:** No logging of raw job data

**Solution:** Add logging in processor.py

## Debugging Steps

### Step 1: Check Error Details
```sql
SELECT 
    metadata->'error_details' as error_details
FROM scrape_runs
WHERE id = 'b7848148-895c-42ce-86de-f1245799ea61';
```

### Step 2: Check Snapshot ID
```sql
SELECT 
    metadata->>'snapshot_id' as snapshot_id,
    metadata->>'duration_seconds' as duration
FROM scrape_runs
WHERE id = 'b7848148-895c-42ce-86de-f1245799ea61';
```

### Step 3: Add Raw Data Logging

Add to `ingestion/processor.py` after line 110:

```python
elif source == "indeed":
    # LOG RAW DATA BEFORE VALIDATION
    logger.info(f"Raw Indeed job data: {json.dumps(raw_job, indent=2)}")
    job = IndeedJobPosting(**raw_job)
```

### Step 4: Check Bright Data Dashboard

1. Go to Bright Data dashboard
2. Find the snapshot ID from Step 2
3. Check if data was actually collected
4. Download the raw JSON response
5. Compare field names with our model

### Step 5: Test Locally

Create a test file with actual Bright Data response:

```python
# test_real_indeed_data.py
from models.indeed import IndeedJobPosting

# Paste actual JSON from Bright Data here
real_data = {
    # ... actual response
}

try:
    job = IndeedJobPosting(**real_data)
    print("✅ Validation passed!")
except Exception as e:
    print(f"❌ Validation failed: {e}")
```

## Quick Fixes to Try

### Fix A: Log Raw Data
Add logging to see what we're actually receiving:

```python
# In ingestion/processor.py, line ~110
logger.info(f"Processing {source} job: {job_id_field}")
logger.debug(f"Raw data keys: {list(raw_job.keys())}")  # ← ADD THIS
```

### Fix B: Make ALL Fields Optional
Nuclear option - make everything optional:

```python
# In models/indeed.py
jobid: Optional[str] = Field(default="unknown", alias='job_id')
url: Optional[str] = Field(default="", alias='job_url')
# ... etc
```

### Fix C: Add Preprocessing
Clean/normalize data before validation:

```python
def preprocess_indeed_job(raw_job: Dict) -> Dict:
    """Normalize field names and add defaults."""
    normalized = {}
    
    # Map common variations
    field_mappings = {
        'job_id': ['job_id', 'jobid', 'id', 'jobkey'],
        'url': ['url', 'job_url', 'link', 'viewJobUrl'],
        'title': ['title', 'job_title', 'position'],
        # ... etc
    }
    
    for target_field, possible_names in field_mappings.items():
        for name in possible_names:
            if name in raw_job:
                normalized[target_field] = raw_job[name]
                break
    
    return {**raw_job, **normalized}
```

## Expected vs Actual

### What We Expect from Bright Data:
```json
{
  "job_id": "abc123",
  "title": "BI Developer",
  "company": "Company Name",
  "location": "Brussels, Belgium",
  "url": "https://be.indeed.com/...",
  "description": "..."
}
```

### What We Might Actually Get:
```json
{
  "jobkey": "abc123",  ← Different name!
  "jobtitle": "BI Developer",  ← Different name!
  "company": "Company Name",
  "formattedLocation": "Brussels",  ← Different name!
  "link": "https://...",  ← Different name!
  "snippet": "..."  ← Different name!
}
```

## Next Actions

1. ✅ Run SQL query to get error details
2. ⏳ Check what field is failing now
3. ⏳ Add raw data logging
4. ⏳ Check Bright Data dashboard
5. ⏳ Compare actual vs expected field names
6. ⏳ Add more aliases or make fields optional
7. ⏳ Test with real data locally
