# ✅ Phase 4.3: Job Lifecycle Manager - COMPLETE

## Summary

The job lifecycle manager has been successfully implemented, providing automated tracking and management of inactive jobs based on last_seen_at timestamps.

## What Was Implemented

### Lifecycle Module (`scraper/lifecycle.py`)

**85 lines** of production-ready lifecycle management:

#### Functions

**1. mark_inactive_jobs(threshold_days=14) → int**

Mark jobs as inactive if they haven't been seen in threshold_days.

**Logic:**
1. Calculate cutoff date (now - threshold_days)
2. Query for active jobs with last_seen_at < cutoff
3. Extract job IDs
4. Call `db.mark_jobs_inactive()` to update
5. Return count of jobs marked

**Default**: 14 days threshold

**Returns**: Count of jobs marked inactive

**Example:**
```python
# Mark jobs not seen in 14+ days
count = mark_inactive_jobs()
# Returns: 25

# Custom threshold
count = mark_inactive_jobs(threshold_days=30)
# Returns: 10
```

**2. get_inactive_jobs_summary() → dict**

Get summary statistics about inactive jobs.

**Returns dictionary with:**
- `total_inactive`: Total count of inactive jobs
- `inactive_last_7_days`: Jobs marked inactive in last 7 days
- `inactive_last_30_days`: Jobs marked inactive in last 30 days

**Example:**
```python
summary = get_inactive_jobs_summary()
# Returns: {
#     "total_inactive": 150,
#     "inactive_last_7_days": 25,
#     "inactive_last_30_days": 80
# }
```

## Test Results

### Pytest: 5/5 Tests Passing ✅

**Test Coverage:**

1. **mark_inactive_jobs** (3 tests)
   - ✅ No jobs to mark (returns 0)
   - ✅ Marks inactive jobs (returns count)
   - ✅ Custom threshold works

2. **get_inactive_jobs_summary** (2 tests)
   - ✅ Summary structure correct
   - ✅ Different counts for each period

### Integration Tests: 4/4 Passing ✅

1. ✅ **Mark Inactive Jobs**
   - Queries database
   - Marks jobs correctly
   - Returns accurate count

2. ✅ **Custom Threshold**
   - Tests 7, 14, 30 day thresholds
   - Each returns appropriate count

3. ✅ **Inactive Summary**
   - Returns all required fields
   - Counts are accurate
   - Structure validated

4. ✅ **Lifecycle Workflow**
   - Complete 4-step workflow
   - Stats before/after
   - Summary generation

## Success Criteria ✅

All criteria met:

### ✅ Can identify jobs not seen in 14+ days
- Queries `job_postings` table
- Filters by `is_active = true`
- Compares `last_seen_at` to cutoff date
- Returns matching job IDs

### ✅ Marks them as inactive with timestamp
- Calls `db.mark_jobs_inactive(job_ids)`
- Sets `is_active = false`
- Sets `detected_inactive_at = now()`
- Updates all matching jobs

### ✅ Returns correct count
- Counts jobs marked
- Returns integer
- Logs success message

### ✅ Summary statistics are accurate
- Total inactive count
- Last 7 days count
- Last 30 days count
- All queries correct

## Usage Examples

### Basic Usage

```python
from scraper import mark_inactive_jobs, get_inactive_jobs_summary

# Mark jobs inactive (default 14 days)
count = mark_inactive_jobs()
print(f"Marked {count} jobs as inactive")

# Get summary
summary = get_inactive_jobs_summary()
print(f"Total inactive: {summary['total_inactive']}")
print(f"Last 7 days: {summary['inactive_last_7_days']}")
```

### Scheduled Task

```python
import schedule
import time
from scraper import mark_inactive_jobs

def cleanup_inactive_jobs():
    """Daily task to mark inactive jobs."""
    count = mark_inactive_jobs(threshold_days=14)
    print(f"Marked {count} jobs as inactive")

# Run daily at 2 AM
schedule.every().day.at("02:00").do(cleanup_inactive_jobs)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Custom Threshold

```python
# More aggressive: 7 days
count = mark_inactive_jobs(threshold_days=7)

# More lenient: 30 days
count = mark_inactive_jobs(threshold_days=30)
```

### Monitoring Dashboard

```python
from scraper import get_inactive_jobs_summary
from database import db

def get_job_health_metrics():
    """Get comprehensive job health metrics."""
    stats = db.get_stats()
    inactive = get_inactive_jobs_summary()
    
    return {
        "total_jobs": stats["total_jobs"],
        "active_jobs": stats["active_jobs"],
        "inactive_jobs": inactive["total_inactive"],
        "recently_inactive": inactive["inactive_last_7_days"],
        "health_score": stats["active_jobs"] / stats["total_jobs"] * 100
    }

metrics = get_job_health_metrics()
print(f"Health Score: {metrics['health_score']:.1f}%")
```

## Lifecycle Workflow

```
Scheduled Task (Daily)
         ↓
┌─────────────────────────────────────┐
│ mark_inactive_jobs(threshold=14)    │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Calculate Cutoff Date               │
│ cutoff = now() - 14 days            │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Query Active Jobs                   │
│ WHERE is_active = true              │
│   AND last_seen_at < cutoff         │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Mark Jobs Inactive                  │
│ UPDATE job_postings                 │
│ SET is_active = false               │
│     detected_inactive_at = now()    │
│ WHERE id IN (job_ids)               │
└─────────────┬───────────────────────┘
              ↓
         Return Count
```

## Integration with Scraping

The lifecycle manager works in tandem with the scraping system:

**During Scraping:**
```python
# In processor.py
if exists:
    # Update last_seen_at for existing jobs
    db.update_job_posting(job_id, {
        "last_seen_at": datetime.utcnow().isoformat()
    })
```

**Periodic Cleanup:**
```python
# Daily scheduled task
mark_inactive_jobs(threshold_days=14)
```

**Result:**
- Jobs seen in scrapes → `last_seen_at` updated → stay active
- Jobs not seen in 14+ days → marked inactive
- Automatic lifecycle management

## Files Created/Modified

1. **scraper/lifecycle.py** (85 lines)
   - 2 core functions
   - Inactive job tracking
   - Summary statistics

2. **scraper/__init__.py** (26 lines)
   - Exports lifecycle functions

3. **tests/test_lifecycle.py** (180 lines)
   - 5 pytest tests
   - 100% passing
   - Mocked database calls

4. **test_lifecycle.py** (140 lines)
   - 4 integration tests
   - All passing
   - Real database queries

## Key Features

### Automated Tracking
- Identifies inactive jobs
- No manual intervention
- Scheduled execution

### Configurable Threshold
- Default: 14 days
- Customizable per use case
- Flexible for different job types

### Summary Statistics
- Total inactive count
- Time-based breakdowns
- Monitoring support

### Database Integration
- Queries job_postings table
- Updates is_active flag
- Sets detected_inactive_at timestamp

## Monitoring & Alerting

### Daily Report

```python
def daily_lifecycle_report():
    """Generate daily lifecycle report."""
    # Mark inactive jobs
    marked = mark_inactive_jobs()
    
    # Get summary
    summary = get_inactive_jobs_summary()
    
    # Get stats
    stats = db.get_stats()
    
    print(f"""
    Daily Lifecycle Report
    =====================
    Jobs marked inactive today: {marked}
    Total active jobs: {stats['active_jobs']}
    Total inactive jobs: {summary['total_inactive']}
    Inactive last 7 days: {summary['inactive_last_7_days']}
    """)
```

### Health Check

```python
def check_job_health():
    """Check if too many jobs are going inactive."""
    summary = get_inactive_jobs_summary()
    
    # Alert if >50 jobs went inactive in last 7 days
    if summary['inactive_last_7_days'] > 50:
        print("⚠️ WARNING: High inactive rate!")
        return False
    
    return True
```

## Best Practices

### Scheduling
- Run `mark_inactive_jobs()` daily
- Off-peak hours (e.g., 2 AM)
- After scraping runs complete

### Threshold Selection
- **7 days**: Aggressive, for high-frequency scraping
- **14 days**: Balanced, recommended default
- **30 days**: Conservative, for less frequent scraping

### Monitoring
- Track `inactive_last_7_days` trend
- Alert on sudden spikes
- Review inactive jobs periodically

## Next Steps

Phase 4.3 is complete. The complete orchestration system is now functional!

**Phase 4 (Orchestration) Complete:**
- ✅ 4.1: Date Range Strategy
- ✅ 4.2: Scrape Orchestrator
- ✅ 4.3: Job Lifecycle Manager

**Ready for Phase 5: Web Interface** or other features.

---

**Status**: Phase 4.3 Complete ✅  
**Lines of Code**: 85 lines  
**Test Coverage**: 5 pytest + 4 integration tests, all passing  
**Functions**: 2 lifecycle functions  
**Ready for**: Phase 5 or additional features
