#!/usr/bin/env python3
"""
Fix existing jobs with vague 'Flemish Region' locations.

This script:
1. Finds all job_postings with location containing 'Flemish Region'
2. For each job, checks if the company has a locatie_belgie
3. If yes, creates a new location "{locatie_belgie}, Belgium"
4. Updates the job_posting to use the new, more specific location

Usage:
    python scripts/fix_flemish_region_locations.py [--dry-run]
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


def fix_flemish_region_locations(dry_run: bool = True):
    """
    Fix jobs with vague 'Flemish Region' locations by using company locatie_belgie.
    
    Args:
        dry_run: If True, only show what would be changed without making changes
    """
    db = SupabaseClient()
    
    logger.info("🔍 Finding jobs with 'Flemish Region' locations...")
    
    # Step 1: Find all locations with 'Flemish Region'
    flemish_locations = db.client.table('locations')\
        .select('id, full_location_string, city, region')\
        .ilike('full_location_string', '%Flemish Region%')\
        .execute()
    
    if not flemish_locations.data:
        logger.info("✅ No 'Flemish Region' locations found")
        return
    
    logger.info(f"Found {len(flemish_locations.data)} locations with 'Flemish Region'")
    
    # Step 2: For each location, find jobs and check company location
    total_jobs = 0
    updated_jobs = 0
    skipped_jobs = 0
    errors = 0
    
    for location in flemish_locations.data:
        location_id = location['id']
        location_string = location['full_location_string']
        
        # Find jobs with this location
        jobs = db.client.table('job_postings')\
            .select('id, title, company_id')\
            .eq('location_id', location_id)\
            .execute()
        
        if not jobs.data:
            continue
        
        logger.info(f"\n📍 Location: {location_string} ({len(jobs.data)} jobs)")
        
        for job in jobs.data:
            total_jobs += 1
            job_id = job['id']
            job_title = job['title']
            company_id = job['company_id']
            
            try:
                # Get company master data
                company_master = db.client.table('company_master_data')\
                    .select('locatie_belgie')\
                    .eq('company_id', company_id)\
                    .execute()
                
                if not company_master.data:
                    logger.debug(f"  ⏭️  No master data for job: {job_title[:50]}")
                    skipped_jobs += 1
                    continue
                
                locatie_belgie = company_master.data[0].get('locatie_belgie')
                
                if not locatie_belgie or locatie_belgie.lower() == 'niet gevonden':
                    logger.debug(f"  ⏭️  No company location for job: {job_title[:50]}")
                    skipped_jobs += 1
                    continue
                
                # Create new location string
                new_location_string = f"{locatie_belgie}, Belgium"
                
                # Check if this location already exists
                existing_new_location = db.client.table('locations')\
                    .select('id')\
                    .eq('full_location_string', new_location_string)\
                    .execute()
                
                if existing_new_location.data:
                    new_location_id = existing_new_location.data[0]['id']
                    logger.info(f"  ✓ Using existing location: {new_location_string}")
                else:
                    # Create new location
                    if dry_run:
                        logger.info(f"  [DRY RUN] Would create location: {new_location_string}")
                        new_location_id = "dry-run-id"
                    else:
                        location_data = normalize_location(new_location_string)
                        result = db.client.table('locations')\
                            .insert(location_data)\
                            .execute()
                        new_location_id = result.data[0]['id']
                        logger.info(f"  ✓ Created new location: {new_location_string}")
                
                # Update job posting
                if dry_run:
                    logger.info(f"  [DRY RUN] Would update job: {job_title[:50]}")
                    logger.info(f"    Old: {location_string}")
                    logger.info(f"    New: {new_location_string}")
                else:
                    db.client.table('job_postings')\
                        .update({'location_id': new_location_id})\
                        .eq('id', job_id)\
                        .execute()
                    logger.success(f"  ✅ Updated job: {job_title[:50]}")
                    logger.info(f"    {location_string} → {new_location_string}")
                
                updated_jobs += 1
                
            except Exception as e:
                logger.error(f"  ❌ Error processing job {job_id}: {e}")
                errors += 1
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 Summary:")
    logger.info(f"  Total jobs processed: {total_jobs}")
    logger.info(f"  Jobs updated: {updated_jobs}")
    logger.info(f"  Jobs skipped (no company location): {skipped_jobs}")
    logger.info(f"  Errors: {errors}")
    
    if dry_run:
        logger.warning("\n⚠️  DRY RUN MODE - No changes were made")
        logger.info("Run with --execute to apply changes")
    else:
        logger.success("\n✅ Migration complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Fix jobs with vague 'Flemish Region' locations"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the migration (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    if args.execute:
        logger.warning("⚠️  EXECUTE MODE - Changes will be made to the database")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Aborted")
            return
        fix_flemish_region_locations(dry_run=False)
    else:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        fix_flemish_region_locations(dry_run=True)


if __name__ == "__main__":
    main()
