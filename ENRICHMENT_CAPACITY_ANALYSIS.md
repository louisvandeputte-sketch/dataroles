# Auto-Enrichment Capacity Analysis

## Current Configuration

**Service Settings:**
- Check interval: 60 seconds (every minute)
- Batch size: 20 jobs per cycle
- Delay between jobs: 2 seconds
- Query limit: 100 jobs (but only processes first 20 unenriched)

**Processing Time per Cycle:**
- 20 jobs × 2 seconds delay = 40 seconds minimum
- Plus enrichment API time (~3-5 seconds per job) = ~60-100 seconds per job
- **Total per cycle: ~20-33 minutes for 20 jobs**

## Capacity Calculation

### Current Capacity
- **Per hour:** 20 jobs/cycle × 60 minutes / 30 minutes per cycle = ~40 jobs/hour
- **Per night (8 hours):** 40 × 8 = **~320 jobs maximum**

### Problem Identified

**CRITICAL ISSUE:** The service queries only the first 100 Data jobs (line 222):
```python
.limit(100)
```

If there are 2000+ Data jobs and only the first 100 are checked, **new jobs may never be reached** if they're not in the first 100 results.

The query doesn't sort by `posted_date_corrected` or any date field, so it's unpredictable which jobs are returned.

## Bottlenecks

1. **Query Limit (100)** - Only checks first 100 jobs, may miss new ones
2. **No sorting** - Random which jobs are checked
3. **Batch size (20)** - Could be increased
4. **2 second delay** - Necessary for rate limiting but slows processing
5. **Sequential processing** - One job at a time

## Impact on 300 Jobs/Night

**Scenario:** 300 new jobs added overnight

**Current behavior:**
- Service checks first 100 Data jobs (unsorted)
- Filters to 20 unenriched jobs
- Processes 20 jobs per cycle (~30 minutes)
- **Result:** Can handle 320 jobs/night theoretically, BUT...

**PROBLEM:** If the 300 new jobs are NOT in the first 100 queried jobs (because there are 2000+ total Data jobs), they will NEVER be processed.

## Recommended Fixes

### Fix 1: Sort by posted_date_corrected (CRITICAL)
```python
.order("posted_date_corrected", desc=True)  # Newest first
.limit(100)
```
This ensures new jobs are always in the first 100 results.

### Fix 2: Increase query limit
```python
.limit(500)  # Check more jobs
```

### Fix 3: Increase batch size (optional)
```python
if len(jobs) >= 50:  # Process 50 instead of 20
    break
```

### Fix 4: Reduce delay (if API allows)
```python
await asyncio.sleep(1)  # 1 second instead of 2
```

## Recommended Implementation

**Priority 1 (CRITICAL):** Add sorting by posted_date_corrected DESC
- This ensures newest jobs are always processed first
- Zero risk, immediate benefit

**Priority 2:** Increase query limit to 500
- Checks more jobs per cycle
- Minimal performance impact

**Priority 3:** Increase batch size to 30-50
- Processes more jobs per cycle
- May need to monitor API rate limits

## Expected Results After Fix

With sorting + increased limits:
- **New jobs processed within:** 1-2 hours
- **Capacity:** 500+ jobs/night easily
- **Current backlog (116 jobs):** Cleared in ~2-3 hours
