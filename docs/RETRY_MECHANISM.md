# Automatic Retry Mechanism for Stuck Scrape Runs

## 📋 Overview

The retry mechanism automatically detects and retries stuck scrape runs, preventing permanent failures from temporary issues.

## 🔄 How It Works

### 1. **Detection** (Every Hour)
- Scheduler checks for runs stuck in `running` status for >1 hour
- Marks them as `failed` with retry scheduled

### 2. **Retry Scheduling**
- **Delay**: 4 hours between attempts
- **Max Attempts**: 4 retries total
- **Status**: `pending_retry` until ready

### 3. **Retry Execution** (Every 30 Minutes)
- Finds runs ready for retry (`next_retry_at` <= now)
- Executes the scrape run again
- Increments `retry_count`

### 4. **Final State**
- **Success**: Marked as `completed`
- **4 Failures**: Permanently `failed`

## 📊 Database Schema

### New Columns in `scrape_runs`:

| Column | Type | Description |
|--------|------|-------------|
| `retry_count` | INTEGER | Current retry attempt (0-4) |
| `max_retries` | INTEGER | Maximum retries allowed (default: 4) |
| `next_retry_at` | TIMESTAMPTZ | When to retry (NULL if no retry) |
| `original_run_id` | UUID | ID of original run (for retries) |
| `is_retry` | BOOLEAN | True if this is a retry |

## 🎯 Example Flow

```
Run 1: Data Architect in Belgium
├─ Started: 08:00
├─ Stuck at: 09:00 (>1h)
├─ Status: failed
├─ Error: "Run stuck for 1.2h - retry 1/4 scheduled"
└─ Next retry: 13:00 (4h later)

Run 2: [RETRY 1/4] Data Architect in Belgium
├─ Started: 13:00
├─ Stuck at: 14:00
├─ Status: failed
├─ Error: "Run stuck for 1.1h - retry 2/4 scheduled"
└─ Next retry: 18:00

Run 3: [RETRY 2/4] Data Architect in Belgium
├─ Started: 18:00
├─ Completed: 18:15
└─ Status: completed ✅

Total attempts: 3
Final status: SUCCESS
```

## 🛠️ Manual Usage

### Fix Stuck Runs Now:
```bash
./venv/bin/python scripts/fix_stuck_runs_with_retry.py
```

### Check Pending Retries:
```sql
SELECT 
    search_query,
    location_query,
    retry_count,
    max_retries,
    next_retry_at,
    status
FROM scrape_runs
WHERE status = 'pending_retry'
ORDER BY next_retry_at;
```

### View Retry History:
```sql
SELECT 
    search_query,
    location_query,
    retry_count,
    status,
    error_message,
    started_at,
    completed_at
FROM scrape_runs
WHERE original_run_id = 'YOUR_RUN_ID'
   OR id = 'YOUR_RUN_ID'
ORDER BY retry_count;
```

## ⚙️ Configuration

Edit in `scripts/fix_stuck_runs_with_retry.py`:

```python
fix_stuck_runs_with_retry(
    max_duration_hours=1,    # Consider stuck after 1 hour
    retry_delay_hours=4,     # Wait 4 hours before retry
    max_retries=4            # Maximum 4 attempts
)
```

## 📈 Monitoring

### Scheduler Jobs:
- **Stuck Run Checker**: Every 1 hour
- **Retry Processor**: Every 30 minutes

### Check Scheduler Status:
```python
from scheduler import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_scheduled_jobs()

for job in jobs:
    print(f"{job.id}: next run at {job.next_run_time}")
```

## 🚨 Error Messages

| Message | Meaning |
|---------|---------|
| `Run stuck for X.Xh - retry 1/4 scheduled` | First retry scheduled |
| `Run stuck for X.Xh - retry 2/4 scheduled` | Second retry scheduled |
| `Run stuck for X.Xh - retry 3/4 scheduled` | Third retry scheduled |
| `Run stuck for X.Xh - retry 4/4 scheduled` | Final retry scheduled |
| `Run stuck for X.Xh - permanently failed after 4 attempts` | All retries exhausted |

## 💡 Benefits

1. ✅ **Automatic Recovery**: No manual intervention needed
2. ✅ **Prevents Data Loss**: Temporary failures don't become permanent
3. ✅ **Rate Limiting**: 4-hour delay prevents API throttling
4. ✅ **Transparency**: Clear retry count in error messages
5. ✅ **Configurable**: Easy to adjust timing and max retries

## 🔧 Troubleshooting

### Retry Not Executing?
1. Check scheduler is running
2. Verify `next_retry_at` is in the past
3. Check logs for retry processor errors

### Too Many Retries?
- Reduce `max_retries` in configuration
- Increase `retry_delay_hours` for more spacing

### Stuck Runs Not Detected?
- Check `max_duration_hours` setting
- Verify stuck run checker is scheduled
- Look for errors in scheduler logs
