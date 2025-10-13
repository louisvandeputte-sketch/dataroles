# 🔍 New/Updated Count Analysis & Fix

## ❌ Probleem Gevonden

### Reported Counts (INCORRECT)
```
Run: powerbi in Belgium (2025-10-11 16:41)
- jobs_found: 208
- jobs_new: 136
- jobs_updated: 38
- Total accounted: 136 + 38 = 174 ❌ (missing 34!)
```

### Actual Breakdown (CORRECT)
```
- Truly NEW (created during run): 136
- EXISTED BEFORE (re-seen): 72
- Total: 208 ✅
```

### Discrepancy
```
Missing: 208 - 174 = 34 jobs
These 34 jobs were classified as "skipped" instead of "updated"
```

## 🔬 Root Cause Analysis

### Current Logic in `ingestion/processor.py`

```python
if exists:
    if should_update_job(existing_job_data, job_data):
        # Job has changes (e.g., num_applicants increased)
        db.update_job_posting(existing_job_id, {...})
        status = 'updated'  ✅ Counted
    else:
        # Job has NO changes, only update last_seen_at
        db.update_job_posting(existing_job_id, {"last_seen_at": ...})
        status = 'skipped'  ❌ NOT counted!
```

### The Problem

**"Skipped" jobs are NOT counted in `jobs_updated`!**

These jobs:
- ✅ Were found in the scrape
- ✅ Already existed in database
- ✅ Had `last_seen_at` updated
- ❌ But had NO field changes (title, salary, applicants, etc.)

**For the user, these should count as "updated"** because they were re-seen in the run!

## 📊 Detailed Breakdown

### What `should_update_job()` Checks

```python
update_fields = [
    "title",
    "num_applicants",
    "base_salary_min",
    "base_salary_max",
    "employment_type",
    "seniority_level",
    "application_available"
]
```

If ANY of these fields changed → `status = 'updated'`
If NONE changed → `status = 'skipped'` (but still updates `last_seen_at`)

### Example Scenario

**Run 1** (2025-10-10 09:00):
- Scrapes "powerbi in Belgium"
- Finds Job A (new)
- Inserts Job A → `status = 'new'`

**Run 2** (2025-10-11 16:41):
- Scrapes "powerbi in Belgium" again
- Finds Job A again
- Job A exists, check for changes:
  - `num_applicants`: 25 → 30 (changed!)
  - Result: `status = 'updated'` ✅

**Run 3** (2025-10-11 18:00):
- Scrapes "powerbi in Belgium" again
- Finds Job A again
- Job A exists, check for changes:
  - `num_applicants`: 30 → 30 (no change)
  - `title`: same
  - `salary`: same
  - Result: `status = 'skipped'` ❌ (but should be 'updated'!)

## ✅ Solution Implemented

### Changed Logic

```python
if exists:
    if should_update_job(existing_job_data, job_data):
        # Job has changes
        db.update_job_posting(existing_job_id, {...})
        status = 'updated'
        logger.info(f"Updated job: {job.job_title}")
    else:
        # No changes, but still count as 'updated' since we re-saw it
        db.update_job_posting(existing_job_id, {"last_seen_at": ...})
        status = 'updated'  # ✅ Changed from 'skipped'
        logger.debug(f"Re-saw job (no changes): {job.job_title}")
```

### Impact

**Before Fix:**
- jobs_new: 136
- jobs_updated: 38 (only jobs with field changes)
- jobs_skipped: 34 (not counted anywhere!)
- jobs_found: 208

**After Fix:**
- jobs_new: 136
- jobs_updated: 72 (38 with changes + 34 re-seen)
- jobs_found: 208
- ✅ jobs_new + jobs_updated = jobs_found

## 🎯 Why This Makes Sense

### User Perspective

When a user sees "136 new / 38 updated":
- ❌ They think: "Only 174 jobs were processed"
- ✅ They expect: "All 208 jobs were processed"

### Correct Interpretation

- **"New"**: Job was not in database before this run
- **"Updated"**: Job was already in database and was re-seen
  - Includes jobs with field changes (e.g., more applicants)
  - Includes jobs with no changes (still active, still there)

### Why Re-seen Jobs Matter

Even if a job has no changes, knowing it was re-seen is important:
- ✅ Confirms the job is still active
- ✅ Updates `last_seen_at` timestamp
- ✅ Prevents false "inactive" detection
- ✅ Tracks job visibility over time

## 🧪 Testing

### Test Script

Run `test_count_fix.py` to verify:

```bash
./venv/bin/python test_count_fix.py
```

Expected output:
```
✅ SUCCESS! All counts are correct!
   New count correct: ✅ (136 == 136)
   Updated count correct: ✅ (72 == 72)
   Total count correct: ✅ (208 == 208)
```

### Manual Verification

```python
from database import db
from dateutil import parser

# Get latest run
run = db.client.table("scrape_runs")\
    .select("*")\
    .order("started_at", desc=True)\
    .limit(1)\
    .single()\
    .execute()

# Get jobs from run
history = db.client.table("job_scrape_history")\
    .select("job_posting_id")\
    .eq("scrape_run_id", run.data["id"])\
    .execute()

job_ids = [h["job_posting_id"] for h in history.data]

# Check creation dates
jobs = db.client.table("job_postings")\
    .select("id, created_at")\
    .in_("id", job_ids)\
    .execute()

run_start = parser.parse(run.data["started_at"])

new_count = sum(1 for j in jobs.data if parser.parse(j["created_at"]) >= run_start)
updated_count = len(jobs.data) - new_count

print(f"Expected: {new_count} new + {updated_count} updated = {len(jobs.data)} total")
print(f"Reported: {run.data['jobs_new']} new + {run.data['jobs_updated']} updated = {run.data['jobs_found']} total")
```

## 📝 Summary

### Problem
- "Skipped" jobs (no changes, only `last_seen_at` update) were not counted
- This made `jobs_new + jobs_updated < jobs_found`
- Misleading for users

### Solution
- Changed `status = 'skipped'` to `status = 'updated'`
- Now all re-seen jobs count as "updated"
- `jobs_new + jobs_updated = jobs_found` ✅

### Benefits
- ✅ Accurate counts
- ✅ Clear user communication
- ✅ All jobs accounted for
- ✅ Better tracking of job activity

---

**Status**: ✅ Fixed in `ingestion/processor.py` (line 131)
