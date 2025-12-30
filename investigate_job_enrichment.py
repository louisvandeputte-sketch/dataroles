#!/usr/bin/env python3
"""Investigate why specific job has no enrichment despite having title classification."""

from database.client import db
from loguru import logger

# Search for the job
job_title = "Customer Journey Expert - GenAI Chatbot"
company_name = "ING Bank"

logger.info(f"Searching for job: {job_title}")
logger.info(f"Company: {company_name}")

# Find job by title and company
jobs = db.client.table("job_postings")\
    .select("*, companies(*), llm_enrichment(*)")\
    .ilike("title", f"%{job_title}%")\
    .execute()

if not jobs.data:
    logger.error("Job not found!")
    exit(1)

# Filter by company if multiple results
matching_jobs = [j for j in jobs.data if company_name.lower() in j.get('companies', {}).get('name', '').lower()]

if not matching_jobs:
    logger.warning(f"No jobs found for company {company_name}, showing all matches:")
    matching_jobs = jobs.data

for job in matching_jobs:
    logger.info(f"\n{'='*80}")
    logger.info(f"Job ID: {job['id']}")
    logger.info(f"Title: {job['title']}")
    logger.info(f"Company: {job.get('companies', {}).get('name', 'N/A')}")
    logger.info(f"Title Classification: {job.get('title_classification', 'NULL')}")
    logger.info(f"Is Active: {job.get('is_active')}")
    logger.info(f"Posted Date: {job.get('posted_date')}")
    logger.info(f"Posted Date Corrected: {job.get('posted_date_corrected')}")
    
    # Check enrichment
    enrichment = job.get('llm_enrichment')
    if enrichment:
        logger.info(f"\n--- ENRICHMENT RECORD ---")
        logger.info(f"Enrichment ID: {enrichment.get('id')}")
        logger.info(f"Completed At: {enrichment.get('enrichment_completed_at')}")
        logger.info(f"Error: {enrichment.get('enrichment_error')}")
        logger.info(f"Type Datarol: {enrichment.get('type_datarol')}")
        logger.info(f"Skills: {enrichment.get('skills_must_have')}")
        
        if not enrichment.get('enrichment_completed_at'):
            logger.warning("⚠️ ENRICHMENT NOT COMPLETED!")
            
            if enrichment.get('enrichment_error'):
                logger.error(f"Error: {enrichment.get('enrichment_error')}")
            else:
                logger.warning("No error recorded - enrichment may be pending or stuck")
    else:
        logger.error("❌ NO ENRICHMENT RECORD FOUND!")
        logger.info("This job was never processed by the enrichment system")
    
    # Check job sources
    sources = db.client.table("job_sources")\
        .select("*")\
        .eq("job_posting_id", job['id'])\
        .execute()
    
    logger.info(f"\n--- JOB SOURCES ---")
    if sources.data:
        for source in sources.data:
            logger.info(f"Source: {source.get('source')}")
            logger.info(f"Source Job ID: {source.get('source_job_id')}")
            logger.info(f"First Seen: {source.get('first_seen_at')}")
    else:
        logger.warning("No job sources found!")
    
    # Check scrape history
    history = db.client.table("job_scrape_history")\
        .select("*, scrape_runs(*)")\
        .eq("job_posting_id", job['id'])\
        .order("detected_at", desc=True)\
        .limit(3)\
        .execute()
    
    logger.info(f"\n--- SCRAPE HISTORY (last 3) ---")
    if history.data:
        for h in history.data:
            run = h.get('scrape_runs', {})
            logger.info(f"Detected: {h.get('detected_at')}")
            logger.info(f"Run: {run.get('search_query')} @ {run.get('started_at')}")
    else:
        logger.warning("No scrape history found!")

logger.info(f"\n{'='*80}")
logger.info("\n=== DIAGNOSIS ===")
logger.info("Possible reasons for missing enrichment:")
logger.info("1. Job was classified as 'Data' but auto-enrichment hasn't processed it yet")
logger.info("2. Enrichment failed with an error (check enrichment_error)")
logger.info("3. No enrichment record exists (job was never queued for enrichment)")
logger.info("4. Job is too new and hasn't been picked up by auto-enrichment service")
logger.info("5. DISABLE_AUTO_ENRICHMENT env var is set to true")
