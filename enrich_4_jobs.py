"""Enrich the 4 newest unenriched Data jobs."""

from database import db
from ingestion.llm_enrichment import process_job_enrichment
from loguru import logger
import time
from datetime import datetime

# The 4 specific job IDs to enrich
job_ids_to_enrich = [
    'acb96320-2eb5-44b3-895c-8a17a1429ff8',  # Test Data and Automation Engineer
    '27f7e4b3-0aa2-4df8-849a-b29224ec6267',  # Customer Journey Expert - GenAI Chatbot
    'b3f0614b-8a3a-4574-a57b-4fe57f638e9d',  # Customer Journey Expert - Virtual Assistant
    'bc50f12d-6349-400b-ab68-dca6e3177a83',  # AWS Data Architect
]

logger.info(f"Enriching 4 specific jobs...")

# Get job details
jobs = []
for job_id in job_ids_to_enrich:
    result = db.client.table('job_postings')\
        .select('id, title, companies(name)')\
        .eq('id', job_id)\
        .single()\
        .execute()
    
    if result.data:
        jobs.append(result.data)

logger.info(f"\n{'='*80}")
logger.info(f"Jobs to enrich:")
logger.info(f"{'='*80}")
for i, job in enumerate(jobs, 1):
    company_name = job.get('companies', {}).get('name', 'Unknown') if job.get('companies') else 'Unknown'
    logger.info(f"{i}. {job['title']} - {company_name}")
logger.info(f"{'='*80}\n")

# Enrich all 4 jobs
success_count = 0
failed_count = 0

for i, job in enumerate(jobs, 1):
    try:
        job_id = job['id']
        title = job['title']
        company_name = job.get('companies', {}).get('name', 'Unknown') if job.get('companies') else 'Unknown'
        
        logger.info(f"[{i}/4] Enriching: {title} - {company_name}")
        
        result = process_job_enrichment(job_id, force=False)
        
        if result and result.get("success"):
            if result.get("skipped"):
                logger.warning(f"⏭️  [{i}/4] Already enriched: {title}")
            else:
                success_count += 1
                logger.success(f"✅ [{i}/4] Successfully enriched: {title}")
        else:
            failed_count += 1
            error = result.get("error", "Unknown error") if result else "No result"
            logger.error(f"❌ [{i}/4] Failed: {title} - {error}")
        
        # Small delay between enrichments
        if i < len(jobs):
            time.sleep(1)
        
    except Exception as e:
        failed_count += 1
        logger.error(f"❌ [{i}/4] Exception for {job.get('title')}: {e}")
        continue

logger.info(f"\n{'='*80}")
logger.info(f"ENRICHMENT COMPLETE")
logger.info(f"{'='*80}")
logger.info(f"✅ Success: {success_count}")
logger.info(f"❌ Failed: {failed_count}")
logger.info(f"📊 Total: {len(jobs)}")
logger.info(f"{'='*80}\n")
