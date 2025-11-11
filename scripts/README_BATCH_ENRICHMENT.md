# Batch Enrichment Script

## Overview

Script to **RE-ENRICH ALL** active Data jobs in batches of 50 using the LLM enrichment pipeline.

⚠️ **WARNING**: This script will **OVERWRITE** all existing enrichment data for Data jobs!

## Features

- ✅ Processes ALL active Data jobs (`title_classification = 'Data'`)
- ✅ Forces re-enrichment (overwrites existing data)
- ✅ Batches of 50 jobs to avoid overwhelming the API
- ✅ Automatic rate limiting (1s between jobs, 5s between batches)
- ✅ Detailed progress logging
- ✅ Error handling and recovery
- ✅ Summary statistics

## Usage

### Run the Script

```bash
cd /Users/louisvandeputte/datarole
python scripts/batch_enrich_data_jobs.py
```

**What it does:**
- Finds ALL active Data jobs
- Re-enriches EVERY job (overwrites existing enrichment)
- Processes in batches of 50
- Uses latest prompt version (v18)

### 3. Run in Background (Recommended for Large Batches)

```bash
nohup python scripts/batch_enrich_data_jobs.py > enrichment.log 2>&1 &
```

Monitor progress:
```bash
tail -f enrichment.log
```

## Configuration

Edit these constants in the script if needed:

```python
BATCH_SIZE = 50                # Jobs per batch
DELAY_BETWEEN_BATCHES = 5      # Seconds between batches
DELAY_BETWEEN_JOBS = 1         # Seconds between individual jobs
```

## Output

### Console Output

```
============================================================
BATCH ENRICHMENT SCRIPT FOR DATA JOBS
============================================================
Batch size: 50
Mode: FORCE RE-ENRICH (overwrites existing data)
Delay between batches: 5s
Delay between jobs: 1s
============================================================

Found 243 active Data jobs to enrich

Total jobs to process: 243
Total batches: 5

⚠️  WARNING: This will OVERWRITE all existing enrichment data for these jobs!

Start enrichment of 243 jobs in 5 batches? (y/n): y

============================================================
Processing batch 1/3 (50 jobs)
============================================================

[1/50] Processing: Data Engineer - Azure & Databricks...
✅ Enriched: Data Engineer - Azure & Databricks
[2/50] Processing: Senior Data Analyst - Power BI...
✅ Enriched: Senior Data Analyst - Power BI
...

Batch 1 complete: 48 successful, 2 failed

Waiting 5s before next batch...

============================================================
ENRICHMENT COMPLETE
============================================================
Total jobs processed: 243
Successful: 237
Failed: 6
Time elapsed: 1623.4s (27.1 minutes)
Average time per job: 6.7s
============================================================
```

## Error Handling

- **Rate Limits**: Script automatically waits between jobs and batches
- **API Errors**: Logged but don't stop the batch
- **Keyboard Interrupt**: Graceful shutdown (Ctrl+C)
- **Failed Jobs**: Logged with error details for manual review

## Monitoring

Check enrichment progress in database:

```sql
-- Count enriched vs total Data jobs
SELECT 
    COUNT(*) as total_data_jobs,
    COUNT(e.enrichment_completed_at) as enriched,
    COUNT(*) - COUNT(e.enrichment_completed_at) as remaining
FROM job_postings j
LEFT JOIN llm_enrichment e ON j.id = e.job_posting_id
WHERE j.title_classification = 'Data' 
  AND j.is_active = true;
```

## Troubleshooting

### Script Hangs

- Check OpenAI API status
- Verify database connection
- Check logs for specific errors

### High Failure Rate

- Check OpenAI API key and credits
- Verify job descriptions exist
- Review error messages in logs

### Want to Stop

- Press Ctrl+C to stop gracefully
- Note: If you re-run the script, it will re-enrich ALL jobs again (including already completed ones)

## Cost Estimation

Assuming ~$0.01 per job enrichment:
- 100 jobs ≈ $1.00
- 500 jobs ≈ $5.00
- 1000 jobs ≈ $10.00

Check actual costs in OpenAI dashboard.

## After Enrichment

1. **Verify Results**
   ```sql
   SELECT enrichment_model_version, COUNT(*) 
   FROM llm_enrichment 
   GROUP BY enrichment_model_version;
   ```

2. **Check for Errors**
   ```sql
   SELECT job_posting_id, enrichment_error 
   FROM llm_enrichment 
   WHERE enrichment_error IS NOT NULL;
   ```

3. **Review Tech Stack Processing**
   ```sql
   SELECT COUNT(DISTINCT job_id) 
   FROM job_programming_languages;
   ```

## Notes

- Script uses the same enrichment pipeline as the web UI
- All enrichment data is saved to `llm_enrichment` table
- Tech stack is automatically extracted and linked
- Prompt version is tracked in `enrichment_model_version`
