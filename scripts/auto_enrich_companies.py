#!/usr/bin/env python3
"""
Automatic company enrichment script.
Runs every 10 hours to enrich unenriched companies.

Usage:
    python3 scripts/auto_enrich_companies.py [--batch-size 50] [--max-total 200]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from ingestion.company_enrichment import (
    get_unenriched_companies,
    enrich_companies_batch,
    get_enrichment_stats
)


def main():
    """Main entry point for automatic company enrichment."""
    parser = argparse.ArgumentParser(description="Automatically enrich unenriched companies")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of companies to enrich per batch (default: 50)"
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=200,
        help="Maximum total companies to enrich in this run (default: 200)"
    )
    parser.add_argument(
        "--no-retries",
        action="store_true",
        help="Don't retry companies with old errors (default: retry after 24h)"
    )
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("AUTOMATIC COMPANY ENRICHMENT")
    logger.info("="*80)
    
    # Get current stats
    stats = get_enrichment_stats()
    logger.info(f"Current status: {stats['enriched']}/{stats['total']} companies enriched ({stats['percentage_enriched']}%)")
    logger.info(f"Unenriched: {stats['unenriched']} companies")
    
    # Get unenriched companies
    include_retries = not args.no_retries
    unenriched = get_unenriched_companies(
        limit=args.max_total,
        include_retries=include_retries
    )
    
    if not unenriched:
        logger.info("✅ No companies to enrich. All done!")
        return
    
    logger.info(f"Found {len(unenriched)} companies to enrich")
    logger.info(f"Will process in batches of {args.batch_size}")
    
    # Process in batches
    total_successful = 0
    total_failed = 0
    batch_num = 0
    
    for i in range(0, len(unenriched), args.batch_size):
        batch_num += 1
        batch = unenriched[i:i + args.batch_size]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH {batch_num}: Processing {len(batch)} companies")
        logger.info(f"{'='*80}")
        
        result = enrich_companies_batch(batch, max_companies=args.batch_size)
        
        total_successful += result["successful"]
        total_failed += result["failed"]
        
        logger.info(f"Batch {batch_num} complete: {result['successful']} successful, {result['failed']} failed")
        
        # Show errors if any
        if result["errors"]:
            logger.warning(f"Errors in batch {batch_num}:")
            for error in result["errors"][:5]:  # Show first 5 errors
                logger.warning(f"  - {error.get('company_name', error.get('company_id'))}: {error['error']}")
            if len(result["errors"]) > 5:
                logger.warning(f"  ... and {len(result['errors']) - 5} more errors")
    
    # Final summary
    logger.info(f"\n{'='*80}")
    logger.info("ENRICHMENT COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total processed: {len(unenriched)}")
    logger.info(f"Successful: {total_successful}")
    logger.info(f"Failed: {total_failed}")
    
    # Get updated stats
    final_stats = get_enrichment_stats()
    logger.info(f"\nFinal status: {final_stats['enriched']}/{final_stats['total']} companies enriched ({final_stats['percentage_enriched']}%)")
    logger.info(f"Remaining: {final_stats['unenriched']} companies")
    
    if total_failed > 0:
        logger.warning(f"⚠️  {total_failed} companies failed. They will be retried in 24 hours.")
    
    logger.success("✅ Automatic enrichment run complete!")


if __name__ == "__main__":
    main()
