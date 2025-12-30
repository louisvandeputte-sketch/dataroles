"""Enrich all unenriched Data jobs (not just recent ones)."""

from database import db
from ingestion.llm_enrichment import process_job_enrichment
from loguru import logger
import time

# Find all Data jobs without enrichment
logger.info("Finding all unenriched Data jobs...")

# Get all Data jobs
all_data_jobs = db.client.table('job_postings')\
    .select('id, title, posted_date_corrected')\
    .eq('title_classification', 'Data')\
    .eq('is_active', True)\
    .order('posted_date_corrected', desc=True)\
    .execute()

logger.info(f"Found {len(all_data_jobs.data)} total Data jobs")

# Get all enriched job IDs
enriched = db.client.table('llm_enrichment')\
    .select('job_posting_id')\
    .execute()

enriched_ids = {e['job_posting_id'] for e in enriched.data}
logger.info(f"Found {len(enriched_ids)} enriched jobs")

# Find unenriched
unenriched = [job for job in all_data_jobs.data if job['id'] not in enriched_ids]

logger.info(f"\n{'='*80}")
logger.info(f"Found {len(unenriched)} UNENRICHED Data jobs to process")
logger.info(f"{'='*80}\n")

if not unenriched:
    logger.success("✅ All Data jobs are already enriched!")
    exit(0)

# Ask for confirmation
print(f"\nReady to enrich {len(unenriched)} jobs.")
print(f"Estimated time: {len(unenriched) * 2 / 60:.1f} minutes")
response = input("\nProceed? (yes/no): ")

if response.lower() != 'yes':
    logger.info("Cancelled by user")
    exit(0)

# Enrich all unenriched jobs
success_count = 0
failed_count = 0
skipped_count = 0

for i, job in enumerate(unenriched, 1):
    try:
        job_id = job['id']
        title = job['title']
        
        logger.info(f"[{i}/{len(unenriched)}] Enriching: {title}")
        
        result = process_job_enrichment(job_id, force=False)
        
        if result and result.get("success"):
            if result.get("skipped"):
                skipped_count += 1
                logger.debug(f"⏭️  Skipped (already enriched): {title}")
            else:
                success_count += 1
                logger.success(f"✅ [{i}/{len(unenriched)}] Enriched: {title}")
        else:
            failed_count += 1
            error = result.get("error", "Unknown error") if result else "No result"
            logger.error(f"❌ [{i}/{len(unenriched)}] Failed: {title} - {error}")
        
        # Delay to avoid rate limits
        time.sleep(1)
        
    except Exception as e:
        failed_count += 1
        logger.error(f"❌ [{i}/{len(unenriched)}] Exception for {job.get('title')}: {e}")
        continue

logger.info(f"\n{'='*80}")
logger.info(f"ENRICHMENT COMPLETE")
logger.info(f"{'='*80}")
logger.info(f"✅ Success: {success_count}")
logger.info(f"⏭️  Skipped: {skipped_count}")
logger.info(f"❌ Failed: {failed_count}")
logger.info(f"📊 Total: {len(unenriched)}")
logger.info(f"{'='*80}\n")
