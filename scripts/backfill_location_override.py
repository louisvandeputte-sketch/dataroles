#!/usr/bin/env python3
"""
Backfill location_id_override for existing job_postings.

This script:
1. Finds all job_postings with vague location ("Flemish Region")
2. For each job:
   - Gets company locatie_belgie
   - Creates/gets a location record for that city
   - Sets location_id_override to point to the new location
3. Frontend will automatically use override location via COALESCE in view

Usage:
    python scripts/backfill_location_override.py [--dry-run] [--batch-size 100]
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.client import SupabaseClient
from ingestion.normalizer import normalize_location


def backfill_location_override(dry_run: bool = True, batch_size: int = 100):
    """
    Backfill location_id_override for jobs with vague locations.
    
    Args:
        dry_run: If True, only show what would be changed without making changes
        batch_size: Number of jobs to process per batch
    """
    db = SupabaseClient()
    
    logger.info("🔍 Finding jobs with vague 'Flemish Region' location...")
    
    # Find location with city='Flemish Region'
    flemish_location = db.client.table('locations')\
        .select('id')\
        .eq('city', 'Flemish Region')\
        .single()\
        .execute()
    
    if not flemish_location.data:
        logger.info("✅ No vague 'Flemish Region' location found")
        return
    
    flemish_location_id = flemish_location.data['id']
    
    # Get total count of jobs with this location
    count_result = db.client.table('job_postings')\
        .select('id', count='exact')\
        .eq('location_id', flemish_location_id)\
        .execute()
    
    total_jobs = count_result.count or 0
    
    if total_jobs == 0:
        logger.info("✅ No jobs with vague 'Flemish Region' location")
        return
    
    logger.info(f"Found {total_jobs} jobs with vague location to backfill")
    
    # Process in batches
    offset = 0
    total_updated = 0
    total_skipped = 0
    errors = 0
    
    while offset < total_jobs:
        logger.info(f"\n📦 Processing batch {offset // batch_size + 1} (jobs {offset + 1}-{min(offset + batch_size, total_jobs)})")
        
        # Get batch of jobs with Flemish Region location
        jobs = db.client.table('job_postings')\
            .select('id, company_id')\
            .eq('location_id', flemish_location_id)\
            .range(offset, offset + batch_size - 1)\
            .execute()
        
        if not jobs.data:
            break
        
        for job in jobs.data:
            job_id = job['id']
            company_id = job['company_id']
            
            try:
                # Get company location
                company_master = db.client.table('company_master_data')\
                    .select('locatie_belgie')\
                    .eq('company_id', company_id)\
                    .execute()
                
                if not company_master.data or not company_master.data[0].get('locatie_belgie'):
                    logger.debug(f"  ⏭️  No company location for job {job_id[:8]}")
                    total_skipped += 1
                    continue
                
                company_location = company_master.data[0]['locatie_belgie']
                
                if company_location.lower() == 'niet gevonden':
                    logger.debug(f"  ⏭️  Company location is 'niet gevonden' for job {job_id[:8]}")
                    total_skipped += 1
                    continue
                
                # Create location string from company location
                override_location_string = f"{company_location}, Belgium"
                override_location_data = normalize_location(override_location_string)
                
                # Check if this location already exists
                existing_override = db.client.table('locations')\
                    .select('id')\
                    .eq('full_location_string', override_location_data['full_location_string'])\
                    .execute()
                
                if existing_override.data:
                    location_id_override = existing_override.data[0]['id']
                    logger.debug(f"  ✓ Using existing location: {company_location}")
                else:
                    # Create new location
                    if dry_run:
                        logger.debug(f"  [DRY RUN] Would create location: {company_location}")
                        location_id_override = "dry-run-id"
                    else:
                        result = db.client.table('locations')\
                            .insert(override_location_data)\
                            .execute()
                        location_id_override = result.data[0]['id']
                        logger.debug(f"  ✓ Created new location: {company_location}")
                
                # Update job
                if dry_run:
                    logger.debug(f"  [DRY RUN] Would update job {job_id[:8]}")
                    logger.debug(f"    location_id_override: {location_id_override}")
                    logger.debug(f"    Display: {company_location}")
                else:
                    db.client.table('job_postings')\
                        .update({'location_id_override': location_id_override})\
                        .eq('id', job_id)\
                        .execute()
                    logger.debug(f"  ✅ Updated job {job_id[:8]}: {company_location}")
                
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
        description="Backfill location_id_override for jobs with vague locations"
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
        backfill_location_override(dry_run=False, batch_size=args.batch_size)
    else:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        backfill_location_override(dry_run=True, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
