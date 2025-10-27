#!/usr/bin/env python3
"""
Enrich all existing locations in the database.

This script will:
1. Find all locations that haven't been AI-enriched yet
2. Enrich them using the OpenAI LLM
3. Show statistics about the enrichment process
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.location_enrichment import enrich_locations_batch
from database.client import db
from loguru import logger

# Configure logger
logger.add("logs/enrich_locations_{time}.log", rotation="10 MB")


def get_enrichment_stats():
    """Get statistics about location enrichment status."""
    try:
        # Total locations
        total_result = db.client.table("locations")\
            .select("id", count="exact")\
            .execute()
        total = total_result.count if total_result.count else 0
        
        # Enriched locations
        enriched_result = db.client.table("locations")\
            .select("id", count="exact")\
            .eq("ai_enriched", True)\
            .execute()
        enriched = enriched_result.count if enriched_result.count else 0
        
        # Failed enrichments
        failed_result = db.client.table("locations")\
            .select("id", count="exact")\
            .eq("ai_enriched", False)\
            .not_.is_("ai_enrichment_error", "null")\
            .execute()
        failed = failed_result.count if failed_result.count else 0
        
        # Pending (not enriched yet)
        pending = total - enriched - failed
        
        return {
            "total": total,
            "enriched": enriched,
            "failed": failed,
            "pending": pending
        }
    except Exception as e:
        logger.error(f"Failed to get enrichment stats: {e}")
        return None


def main():
    """Main enrichment function."""
    print("🌍 Location Enrichment Script")
    print("=" * 60)
    
    # Parse arguments early to support --force bypass
    force_reenrich = False
    batch_size = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--force", "-f"):
            force_reenrich = True
            print(f"\n🔄 Force re-enrich mode: Will re-enrich ALL locations")
            if len(sys.argv) > 2:
                try:
                    batch_size = int(sys.argv[2])
                    print(f"📦 Batch size: {batch_size} locations")
                except ValueError:
                    pass
        else:
            try:
                batch_size = int(sys.argv[1])
                print(f"\n📦 Batch size: {batch_size} locations")
            except ValueError:
                print("❌ Invalid batch size argument. Using all pending locations.")

    # Get current stats
    print("\n📊 Current Status:")
    stats = get_enrichment_stats()
    if stats:
        print(f"   Total locations: {stats['total']}")
        print(f"   Already enriched: {stats['enriched']} ({stats['enriched']/stats['total']*100:.1f}%)" if stats['total'] > 0 else "   Already enriched: 0")
        print(f"   Failed enrichments: {stats['failed']}")
        print(f"   Pending enrichment: {stats['pending']}")
    else:
        print("   ❌ Could not retrieve stats")
        return
    
    # Only exit early if not forcing
    if stats['pending'] == 0 and not force_reenrich:
        print("\n✅ All locations are already enriched!")
        return
    
    # Ask for confirmation
    print(f"\n⚠️  This will enrich {('ALL' if force_reenrich else stats['pending'])} locations using OpenAI API.")
    print("   This may take a while and will consume API credits.")
    
    confirm = input(f"\n   Continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Enrichment cancelled")
        return
    
    # Run enrichment
    print(f"\n🚀 Starting enrichment...")
    print("-" * 60)
    
    result = enrich_locations_batch(limit=batch_size, force_reenrich=force_reenrich)
    
    print("\n" + "=" * 60)
    print("📊 Enrichment Results:")
    print(f"   Total processed: {result['total']}")
    print(f"   Successful: {result['successful']} ✅")
    print(f"   Failed: {result['failed']} ❌")
    
    if result['errors']:
        print(f"\n❌ Errors (showing first 10):")
        for i, error in enumerate(result['errors'][:10]):
            city = error.get('city', 'Unknown')
            error_msg = error.get('error', 'Unknown error')
            print(f"   {i+1}. {city}: {error_msg}")
        
        if len(result['errors']) > 10:
            print(f"   ... and {len(result['errors']) - 10} more errors")
    
    # Get updated stats
    print("\n📊 Updated Status:")
    updated_stats = get_enrichment_stats()
    if updated_stats:
        print(f"   Total locations: {updated_stats['total']}")
        print(f"   Enriched: {updated_stats['enriched']} ({updated_stats['enriched']/updated_stats['total']*100:.1f}%)" if updated_stats['total'] > 0 else "   Enriched: 0")
        print(f"   Failed: {updated_stats['failed']}")
        print(f"   Pending: {updated_stats['pending']}")
    
    print("\n✅ Enrichment complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
