#!/usr/bin/env python3
"""
Re-enrich the 10 stuck AI Engineer jobs after fixing the database constraint.

These jobs were stuck in an infinite re-enrichment loop because the database
constraint didn't allow 'AI Engineer' as a valid type_datarol value.

After running migration 081, we can now successfully save these enrichments.
"""

import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from loguru import logger
from ingestion.llm_enrichment import process_job_enrichment
from database.client import db

# The 10 jobs stuck with NULL type_datarol
STUCK_JOBS = [
    {
        'id': 'd68d2252-a20d-4014-9724-52eb53ba47bb',
        'title': 'AI Engineer (NLP / ML / Big Data)'
    },
    {
        'id': 'e1ca29f3-a970-4738-9ad6-0d824c4356b3',
        'title': 'Agentic AI Solutions & Business Translator'
    },
    {
        'id': 'fb13bb8f-52df-4206-b0d4-3dad41eb3ead',
        'title': 'Cloud Data & AI Platform Expert'
    },
    {
        'id': 'd0cfd75f-9762-47cc-a6f0-6c7d26937a9c',
        'title': 'Data & AI Engineer'
    },
    {
        'id': '0cfa13ee-7b01-4b5b-8941-8b99b5a3eaff',
        'title': 'Freelance MLOps & AI Engineers'
    },
    {
        'id': 'dfbbd066-53c0-42ad-8c0d-38e4be207dcc',
        'title': 'GEN AI Engineer (F/H/X)'
    },
    {
        'id': '4b5f1d95-2a02-44e5-afc7-cf3628a56502',
        'title': 'AI Specialist'
    },
    {
        'id': '2ba44502-4203-4e24-b05b-7143b1681a79',
        'title': 'Machine Learning Researcher'
    },
    {
        'id': '92537c34-573f-4a1a-a548-97808ec8ac32',
        'title': 'Software Engineer IA'
    },
    {
        'id': '35e30737-dc6a-4a7c-bdce-b012847d2b2e',
        'title': 'Founding AI/ML Research Engineer'
    },
]


def main():
    """Re-enrich all stuck AI Engineer jobs."""
    
    logger.info("="*80)
    logger.info("Re-enriching 10 stuck AI Engineer jobs")
    logger.info("="*80)
    
    success_count = 0
    failed_count = 0
    
    for i, job in enumerate(STUCK_JOBS, 1):
        job_id = job['id']
        title = job['title']
        
        logger.info(f"\n[{i}/10] Processing: {title}")
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
                        logger.warning(f"  error: {error}")
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ Failed to enrich: {title}")
                logger.error(f"  Error: {error_msg}")
                failed_count += 1
        
        except Exception as e:
            logger.error(f"❌ Exception while enriching: {title}")
            logger.error(f"  Error: {e}")
            failed_count += 1
        
        # Small delay between jobs
        import time
        time.sleep(2)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total jobs: {len(STUCK_JOBS)}")
    logger.info(f"✅ Successful: {success_count}")
    logger.info(f"❌ Failed: {failed_count}")
    
    if success_count == len(STUCK_JOBS):
        logger.success("\n🎉 All jobs successfully re-enriched!")
        logger.success("The infinite re-enrichment loop is now fixed!")
    elif success_count > 0:
        logger.warning(f"\n⚠️  {failed_count} jobs still need attention")
    else:
        logger.error("\n❌ All jobs failed - check errors above")


if __name__ == "__main__":
    main()
