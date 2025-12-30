#!/usr/bin/env python3
"""
Re-enrich remaining AI/ML jobs with NULL type_datarol after fixing constraint.

These jobs failed enrichment yesterday due to OpenAI quota errors.
Now that the constraint is fixed to allow 'AI Engineer', we can re-enrich them.
"""

import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from loguru import logger
from ingestion.llm_enrichment import process_job_enrichment
from database.client import db
import time


def get_jobs_to_fix():
    """Get all Data jobs with NULL type_datarol."""
    result = db.client.table('llm_enrichment')\
        .select('job_posting_id, job_postings!inner(title, title_classification)')\
        .eq('job_postings.title_classification', 'Data')\
        .is_('type_datarol', 'null')\
        .execute()
    
    jobs = []
    for job in result.data:
        job_info = job.get('job_postings', {})
        jobs.append({
            'id': job['job_posting_id'],
            'title': job_info.get('title', 'Unknown')
        })
    
    return jobs


def main():
    """Re-enrich all jobs with NULL type_datarol."""
    
    # Get jobs to fix
    jobs = get_jobs_to_fix()
    
    if not jobs:
        logger.success("✅ No jobs to fix! All jobs have type_datarol set.")
        return
    
    logger.info("="*80)
    logger.info(f"Re-enriching {len(jobs)} jobs with NULL type_datarol")
    logger.info("="*80)
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, job in enumerate(jobs, 1):
        job_id = job['id']
        title = job['title']
        
        logger.info(f"\n[{i}/{len(jobs)}] Processing: {title}")
        logger.info(f"Job ID: {job_id}")
        
        try:
            # Force re-enrichment
            result = process_job_enrichment(job_id, force=True)
            
            if result.get('success'):
                logger.success(f"✅ Successfully enriched: {title}")
                success_count += 1
                
                # Verify type_datarol is now set
                enrichment = db.client.table('llm_enrichment')\
                    .select('type_datarol, enrichment_completed_at, enrichment_error')\
                    .eq('job_posting_id', job_id)\
                    .single()\
                    .execute()
                
                if enrichment.data:
                    type_datarol = enrichment.data.get('type_datarol')
                    completed_at = enrichment.data.get('enrichment_completed_at')
                    error = enrichment.data.get('enrichment_error')
                    
                    logger.info(f"  type_datarol: {type_datarol}")
                    logger.info(f"  completed_at: {completed_at}")
                    if error:
                        logger.warning(f"  error: {error[:100]}")
            else:
                error_msg = result.get('error', 'Unknown error')
                if 'already enriched' in str(error_msg).lower():
                    logger.info(f"⏭️  Already enriched: {title}")
                    skipped_count += 1
                else:
                    logger.error(f"❌ Failed to enrich: {title}")
                    logger.error(f"  Error: {error_msg}")
                    failed_count += 1
        
        except Exception as e:
            logger.error(f"❌ Exception while enriching: {title}")
            logger.error(f"  Error: {e}")
            failed_count += 1
        
        # Delay between jobs to avoid rate limits
        if i < len(jobs):
            time.sleep(2)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total jobs: {len(jobs)}")
    logger.info(f"✅ Successful: {success_count}")
    logger.info(f"⏭️  Skipped: {skipped_count}")
    logger.info(f"❌ Failed: {failed_count}")
    
    if success_count + skipped_count == len(jobs):
        logger.success("\n🎉 All jobs processed successfully!")
        logger.success("No more jobs with NULL type_datarol!")
    elif success_count > 0:
        logger.warning(f"\n⚠️  {failed_count} jobs still need attention")
    else:
        logger.error("\n❌ All jobs failed - check errors above")
    
    # Final verification
    remaining = get_jobs_to_fix()
    logger.info(f"\n📊 Jobs still with NULL type_datarol: {len(remaining)}")


if __name__ == "__main__":
    main()
