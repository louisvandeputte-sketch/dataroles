#!/usr/bin/env python3
"""Run migration 082 to populate missing posted_date_corrected values."""

from database.client import db
from loguru import logger

logger.info("Running migration 082: Populate missing posted_date_corrected values")

# Read migration file
with open('database/migrations/082_populate_missing_posted_date_corrected.sql', 'r') as f:
    sql = f.read()

# Execute migration
try:
    # Split by semicolon to execute statements separately
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for i, statement in enumerate(statements, 1):
        if statement:
            logger.info(f"Executing statement {i}/{len(statements)}...")
            result = db.client.rpc('exec_sql', {'sql': statement}).execute()
            logger.success(f"Statement {i} executed successfully")
    
    logger.success("✅ Migration 082 completed successfully")
    
    # Verify results
    null_count = db.client.table("job_postings")\
        .select("id", count="exact")\
        .is_("posted_date_corrected", "null")\
        .execute()
    
    total_count = db.client.table("job_postings")\
        .select("id", count="exact")\
        .execute()
    
    logger.info(f"Results:")
    logger.info(f"  Total jobs: {total_count.count}")
    logger.info(f"  Jobs with NULL posted_date_corrected: {null_count.count}")
    logger.info(f"  Jobs with posted_date_corrected: {total_count.count - null_count.count}")
    
except Exception as e:
    logger.error(f"❌ Migration failed: {e}")
    logger.info("Trying direct UPDATE approach...")
    
    # Fallback: Direct UPDATE via Python
    try:
        # Get all jobs with NULL posted_date_corrected
        jobs = db.client.table("job_postings")\
            .select("id, posted_date")\
            .is_("posted_date_corrected", "null")\
            .limit(2000)\
            .execute()
        
        logger.info(f"Found {len(jobs.data)} jobs with NULL posted_date_corrected")
        
        updated = 0
        for job in jobs.data:
            job_id = job['id']
            posted_date = job.get('posted_date')
            
            # Get first_seen_at from job_sources
            sources = db.client.table("job_sources")\
                .select("first_seen_at")\
                .eq("job_posting_id", job_id)\
                .order("first_seen_at")\
                .limit(1)\
                .execute()
            
            first_seen = sources.data[0]['first_seen_at'] if sources.data else None
            
            # Calculate posted_date_corrected
            if first_seen and posted_date:
                # Both exist: use minimum
                corrected = min(first_seen, posted_date)
            elif first_seen:
                # Only first_seen exists
                corrected = first_seen
            elif posted_date:
                # Only posted_date exists
                corrected = posted_date
            else:
                # Neither exists: skip
                continue
            
            # Update job
            db.client.table("job_postings")\
                .update({"posted_date_corrected": corrected})\
                .eq("id", job_id)\
                .execute()
            
            updated += 1
            
            if updated % 100 == 0:
                logger.info(f"Updated {updated}/{len(jobs.data)} jobs...")
        
        logger.success(f"✅ Updated {updated} jobs via Python fallback")
        
    except Exception as e2:
        logger.error(f"❌ Fallback also failed: {e2}")
