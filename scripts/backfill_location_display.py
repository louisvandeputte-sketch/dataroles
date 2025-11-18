#!/usr/bin/env python3
"""
Backfill location_display fields for existing job_postings.

This script:
1. Finds all job_postings with NULL location_display_nl
2. For each job:
   - If location is vague ("Flemish Region"), use company locatie_belgie
   - Otherwise, use location city_name_nl/en/fr
3. Updates job_postings with location_display values

Usage:
    python scripts/backfill_location_display.py [--dry-run] [--batch-size 100]
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.client import SupabaseClient


def backfill_location_display(dry_run: bool = True, batch_size: int = 100):
    """
    Backfill location_display fields for existing jobs.
    
    Args:
        dry_run: If True, only show what would be changed without making changes
        batch_size: Number of jobs to process per batch
    """
    db = SupabaseClient()
    
    logger.info("🔍 Finding jobs with NULL location_display_nl...")
    
    # Get total count
    count_result = db.client.table('job_postings')\
        .select('id', count='exact')\
        .is_('location_display_nl', 'null')\
        .execute()
    
    total_jobs = count_result.count or 0
    
    if total_jobs == 0:
        logger.info("✅ All jobs already have location_display fields populated")
        return
    
    logger.info(f"Found {total_jobs} jobs to backfill")
    
    # Process in batches
    offset = 0
    total_updated = 0
    total_skipped = 0
    errors = 0
    
    while offset < total_jobs:
        logger.info(f"\n📦 Processing batch {offset // batch_size + 1} (jobs {offset + 1}-{min(offset + batch_size, total_jobs)})")
        
        # Get batch of jobs
        jobs = db.client.table('job_postings')\
            .select('id, location_id, company_id')\
            .is_('location_display_nl', 'null')\
            .range(offset, offset + batch_size - 1)\
            .execute()
        
        if not jobs.data:
            break
        
        for job in jobs.data:
            job_id = job['id']
            location_id = job['location_id']
            company_id = job['company_id']
            
            try:
                # Get location details
                location = db.client.table('locations')\
                    .select('full_location_string, city_name_nl, city_name_en, city_name_fr')\
                    .eq('id', location_id)\
                    .single()\
                    .execute()
                
                if not location.data:
                    logger.debug(f"  ⏭️  No location found for job {job_id}")
                    total_skipped += 1
                    continue
                
                location_string = location.data.get('full_location_string', '')
                
                # Determine display location
                location_display_nl = None
                location_display_en = None
                location_display_fr = None
                
                # Check if location is vague
                if location_string.strip().startswith("Flemish Region"):
                    # Try to get company location
                    company_master = db.client.table('company_master_data')\
                        .select('locatie_belgie')\
                        .eq('company_id', company_id)\
                        .execute()
                    
                    if company_master.data and company_master.data[0].get('locatie_belgie'):
                        company_location = company_master.data[0]['locatie_belgie']
                        if company_location and company_location.lower() != 'niet gevonden':
                            # Use company location
                            location_display_nl = company_location
                            location_display_en = company_location
                            location_display_fr = company_location
                            logger.debug(f"  ✓ Using company location: {company_location}")
                
                # If no company location, use location table data
                if not location_display_nl:
                    location_display_nl = location.data.get('city_name_nl')
                    location_display_en = location.data.get('city_name_en')
                    location_display_fr = location.data.get('city_name_fr')
                
                # Update job
                if dry_run:
                    logger.debug(f"  [DRY RUN] Would update job {job_id[:8]}...")
                    logger.debug(f"    NL: {location_display_nl}")
                    logger.debug(f"    EN: {location_display_en}")
                    logger.debug(f"    FR: {location_display_fr}")
                else:
                    db.client.table('job_postings')\
                        .update({
                            'location_display_nl': location_display_nl,
                            'location_display_en': location_display_en,
                            'location_display_fr': location_display_fr
                        })\
                        .eq('id', job_id)\
                        .execute()
                    logger.debug(f"  ✅ Updated job {job_id[:8]}: {location_display_nl}")
                
                total_updated += 1
                
            except Exception as e:
                logger.error(f"  ❌ Error processing job {job_id}: {e}")
                errors += 1
        
        offset += batch_size
        
        # Progress update
        logger.info(f"Progress: {min(offset, total_jobs)}/{total_jobs} jobs processed")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 Summary:")
    logger.info(f"  Total jobs processed: {total_updated + total_skipped}")
    logger.info(f"  Jobs updated: {total_updated}")
    logger.info(f"  Jobs skipped: {total_skipped}")
    logger.info(f"  Errors: {errors}")
    
    if dry_run:
        logger.warning("\n⚠️  DRY RUN MODE - No changes were made")
        logger.info("Run with --execute to apply changes")
    else:
        logger.success("\n✅ Backfill complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill location_display fields for existing jobs"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the backfill (default is dry-run)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of jobs to process per batch (default: 100)'
    )
    
    args = parser.parse_args()
    
    if args.execute:
        logger.warning("⚠️  EXECUTE MODE - Changes will be made to the database")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Aborted")
            return
        backfill_location_display(dry_run=False, batch_size=args.batch_size)
    else:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        backfill_location_display(dry_run=True, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
