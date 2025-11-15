# Scrape Runs Investigation - November 15, 2025

## Problem Statement
Scrape runs are not yielding jobs as expected. Investigation reveals multiple issues.

## Investigation Findings

### 1. Recent Scrape Runs Analysis (Last 7 Days)
- **Total runs**: 15
- **Completed**: 10
- **Failed**: 1
- **Running (stuck)**: 4

### 2. Identified Issues

#### Issue #1: Stuck Running Scrapes
**Severity**: HIGH

**Evidence**:
- 4 scrapes currently in "running" status
- PowerBI/Belgium LinkedIn scrapes stuck for 35+ minutes
- Data Engineer/Belgium Indeed scrape stuck since 2025-11-15T21:51:17
- BI Developer/Belgium Indeed scrape stuck since 2025-11-13T22:15:07 (>2 days!)

**Root Cause**:
The scrapes are getting stuck in the `wait_for_completion()` phase and never completing or timing out properly.

**Affected Runs**:
- `ba12a268-66fe-44d2-a777-63ff9fd8726f` - PowerBI/Belgium (LinkedIn) - 35 minutes
- `4cc93a02-ac93-480a-b463-80e84029ae71` - PowerBI/Belgium (LinkedIn) - 35 minutes
- `67f729aa-50b4-4028-ab1f-cb1de54545d5` - Data Engineer/Belgium (Indeed) - 3+ hours
- `7d8dd6fd-f4a9-4584-9d5c-a9a256678949` - BI Developer/Belgium (Indeed) - 2+ days

#### Issue #2: Bright Data Returning 0 Jobs
**Severity**: MEDIUM

**Evidence**:
- Run `4778d695-9b41-4be5-93ed-3345b9c80e4a` (Data Engineer/Belgium on Indeed)
- Status: completed
- Jobs found: 0
- Snapshot ID: `sd_mhzvnpxffzawnlnl8`
- Duration: 455 seconds (normal)
- No error details

**Possible Causes**:
1. No jobs actually match the search criteria on Indeed for "Data Engineer" in "Belgium"
2. Invalid location query format for Indeed
3. Date range too restrictive (past_week)
4. Bright Data API issue or rate limiting

#### Issue #3: Missing Diagnostic Data
**Severity**: LOW

**Evidence**:
The `brightdata_jobs_returned` field is missing from metadata in older runs, making it impossible to diagnose whether:
- Bright Data returned 0 jobs (API issue)
- Bright Data returned jobs but they failed validation (processing issue)

**Code Location**: 
`scraper/orchestrator.py` line 209 shows the field should be saved, but it's not present in actual run metadata.

### 3. Successful Runs for Comparison

**Run**: `84f065d8-54d3-4917-9a9c-a4ebceddfeb2`
- Query: Data Governance
- Location: Belgium
- Platform: indeed_brightdata
- Status: completed
- Jobs Found: 13 (10 new, 3 updated)
- Duration: 360 seconds
- Snapshot ID: `sd_mhyg7v7i81r0955cj`

This proves the system CAN work correctly for Indeed scrapes.

### 4. Pattern Analysis

**Working Queries** (Indeed/Belgium):
- Data Governance: 13 jobs
- Databricks: 14 jobs
- Data Engineer: 15 jobs (different run)
- BI Developer: 1 job (multiple runs)

**Not Working Queries**:
- Data Engineer: 0 jobs (scheduled run at 06:00)
- PowerBI: stuck (LinkedIn)

**Key Observation**: 
- Indeed scrapes work for most queries
- LinkedIn scrapes are getting stuck
- Some queries return 0 jobs even though similar queries work

## Root Causes

### Root Cause #1: Timeout/Polling Issues
The `wait_for_completion()` method in Bright Data clients may not be handling:
1. Network timeouts properly
2. API rate limiting
3. Snapshot status edge cases
4. The 30-minute timeout is not being enforced

**Code Location**: 
- `clients/brightdata_linkedin.py` lines 238-290
- `clients/brightdata_indeed.py` lines 255-306

### Root Cause #2: Location Query Format
The location "Belgium" might not be properly formatted for Indeed's API.

**Evidence**:
- LinkedIn client normalizes Belgium cities (lines 88-114)
- Indeed client detects country but may not format location correctly (lines 88-109)

### Root Cause #3: No Automatic Cleanup
Stuck runs are not automatically cleaned up, causing:
- Resource waste
- Confusion about system status
- Potential database bloat

## Recommended Fixes

### Fix #1: Add Better Error Handling in wait_for_completion()
```python
# Add exponential backoff
# Add better timeout enforcement
# Log snapshot status at each poll
# Handle rate limiting gracefully
```

### Fix #2: Add Stuck Run Cleanup Job
- Automatically mark runs as failed after 30 minutes
- Run every 15 minutes
- Log cleanup actions

### Fix #3: Improve Logging and Diagnostics
- Always save `brightdata_jobs_returned` in metadata
- Log raw Bright Data response
- Add query_params to metadata (already implemented)

### Fix #4: Validate Location Queries
- Test Indeed location queries before running
- Provide better location format guidance
- Log normalized location

### Fix #5: Add Snapshot Status Debugging
- Log each poll attempt with full status
- Save final snapshot status in metadata
- Add retry logic for transient failures

## Immediate Actions

1. **Clean up stuck runs** (URGENT)
   ```bash
   POST /api/runs/cleanup-stuck?hours=0.5
   POST /api/indeed/runs/cleanup-stuck?hours=0.5
   ```

2. **Check Bright Data API status** for the stuck snapshots
   - Manually query snapshot status via API
   - Check if they're actually still processing

3. **Review Bright Data quota/limits**
   - Check if we're hitting rate limits
   - Verify API token is valid

4. **Test location queries**
   - Try "Belgium" vs "BE" vs "Brussels, Belgium"
   - Check Indeed's location format requirements

## Next Steps

1. Implement timeout fixes in Bright Data clients
2. Add automatic stuck run cleanup
3. Improve diagnostic logging
4. Test with various location formats
5. Monitor for 24 hours to verify fixes
