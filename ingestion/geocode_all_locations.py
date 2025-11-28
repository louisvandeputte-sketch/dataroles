#!/usr/bin/env python3
"""
Manual script to geocode all locations without coordinates
Usage: python ingestion/geocode_all_locations.py [--limit N]
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.location_geocoder import enrich_all_locations
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description='Geocode all locations without coordinates')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Maximum number of locations to process (default: all)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Batch size for processing (default: 50)')
    
    args = parser.parse_args()
    
    logger.info("🌍 Starting manual geocoding of all locations...")
    logger.info(f"📊 Settings: limit={args.limit or 'all'}, batch_size={args.batch_size}")
    
    if args.limit:
        # Process in one go with limit
        logger.info(f"🔄 Processing up to {args.limit} locations...")
        enrich_all_locations(limit=args.limit, only_missing=True)
    else:
        # Process all locations in batches
        logger.info(f"🔄 Processing ALL locations in batches of {args.batch_size}...")
        
        total_processed = 0
        batch_num = 1
        
        while True:
            logger.info(f"\n📦 Batch {batch_num} (locations {total_processed + 1} to {total_processed + args.batch_size})...")
            
            # Process batch
            enrich_all_locations(limit=args.batch_size, only_missing=True)
            
            total_processed += args.batch_size
            batch_num += 1
            
            # Check if there are more locations to process
            from database.client import db
            remaining = db.client.table("locations")\
                .select("id", count="exact")\
                .is_("coordinates_enriched", "false")\
                .execute()
            
            remaining_count = remaining.count or 0
            
            if remaining_count == 0:
                logger.success(f"\n✅ All locations geocoded! Total processed: ~{total_processed}")
                break
            else:
                logger.info(f"📍 Remaining locations: {remaining_count}")
                
                # Ask user if they want to continue
                if batch_num > 1:  # After first batch, ask for confirmation
                    response = input(f"\nContinue with next batch? ({remaining_count} remaining) [Y/n]: ")
                    if response.lower() == 'n':
                        logger.info(f"⏸️  Stopped by user. Processed {total_processed} locations.")
                        break
    
    logger.success("🎉 Geocoding complete!")


if __name__ == "__main__":
    main()
