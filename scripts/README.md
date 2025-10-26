# Database Maintenance Scripts

## Delete Old Jobs

Scripts to clean up old job postings from the database.

### 1. Check Old Jobs (Dry Run)

Check how many jobs would be deleted without actually deleting them:

```bash
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/check_old_jobs.py
```

Or with a custom cutoff date:

```bash
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/check_old_jobs.py 2025-10-15
```

**Output:**
- Total jobs in database
- Number of jobs before cutoff date
- Number of jobs that would remain
- Percentage to delete
- Sample of oldest jobs

### 2. Delete Old Jobs

Delete all jobs posted before a specific date (default: 2025-10-18):

```bash
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/delete_old_jobs.py
```

Or with a custom cutoff date:

```bash
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/delete_old_jobs.py 2025-10-15
```

**Features:**
- Shows count of jobs to be deleted
- Asks for confirmation before deletion
- Uses CASCADE delete (automatically removes related data)
- Logs all operations to `logs/delete_old_jobs_{time}.log`
- Shows statistics after deletion

**What gets deleted:**
- Job postings from `job_postings` table
- Related job descriptions (CASCADE)
- Related job posters (CASCADE)
- Related LLM enrichment data (CASCADE)
- Related scrape history (CASCADE)
- Related tech stack assignments (CASCADE)

### Safety Features

1. **Dry run first**: Always run `check_old_jobs.py` first to see what would be deleted
2. **Confirmation required**: The delete script asks for explicit "yes" confirmation
3. **Logging**: All operations are logged with timestamps
4. **Statistics**: Shows before/after counts

### Example Workflow

```bash
# 1. Check what would be deleted
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/check_old_jobs.py

# Output:
# 📊 Statistics:
#    Total jobs in database: 2358
#    Jobs before 2025-10-18: 2001
#    Jobs that would remain: 357
#    Percentage to delete: 84.9%

# 2. If you're happy with the numbers, run the delete
PYTHONPATH=/Users/louisvandeputte/datarole python scripts/delete_old_jobs.py

# 3. Confirm when prompted
# ⚠️  Are you sure you want to delete 2001 jobs? (yes/no): yes

# 4. Check the results
# ✅ Successfully deleted 2001 jobs posted before 2025-10-18
# 📊 Statistics:
#    - Jobs deleted: 2001
#    - Jobs remaining: 357
```

### Notes

- The cutoff date is **exclusive** (jobs posted ON that date are kept)
- All related data is automatically deleted via CASCADE constraints
- Logs are saved in the `logs/` directory
- The script uses the `posted_date` column from `job_postings` table
