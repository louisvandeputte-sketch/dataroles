"""Test script to verify subdivision_name_nl sync with subdivision_name."""

import sys
sys.path.insert(0, '.')

from database.client import SupabaseClient
from loguru import logger

def test_subdivision_sync():
    """Test that subdivision_name_nl is synced with subdivision_name."""
    
    db = SupabaseClient()
    
    logger.info("Testing subdivision_name_nl sync...")
    
    # Check current state
    result = db.client.table('locations')\
        .select('id, subdivision_name, subdivision_name_nl')\
        .limit(5)\
        .execute()
    
    logger.info("\n📊 Sample locations after migration:")
    logger.info("-" * 80)
    for loc in result.data:
        sub = loc.get('subdivision_name') or 'NULL'
        sub_nl = loc.get('subdivision_name_nl') or 'NULL'
        match = "✅" if sub == sub_nl else "❌"
        logger.info(f"{match} subdivision: {sub:30} | NL: {sub_nl:30}")
    
    # Count mismatches
    total = db.client.table('locations').select('id', count='exact').execute()
    
    # Count where they match
    matching = db.client.table('locations')\
        .select('id', count='exact')\
        .filter('subdivision_name', 'eq', db.client.table('locations').select('subdivision_name_nl'))\
        .execute()
    
    # Count NULL subdivision_name_nl
    null_nl = db.client.table('locations')\
        .select('id', count='exact')\
        .is_('subdivision_name_nl', 'null')\
        .execute()
    
    logger.info(f"\n📈 Statistics:")
    logger.info(f"Total locations: {total.count}")
    logger.info(f"NULL subdivision_name_nl: {null_nl.count}")
    
    if null_nl.count == 0:
        logger.success("✅ All subdivision_name_nl values are populated!")
    else:
        logger.warning(f"⚠️  {null_nl.count} locations still have NULL subdivision_name_nl")
    
    # Test trigger by checking if we can query
    logger.info("\n🔍 Checking unique subdivision values:")
    unique = db.client.table('locations')\
        .select('subdivision_name, subdivision_name_nl')\
        .not_.is_('subdivision_name', 'null')\
        .limit(10)\
        .execute()
    
    for loc in unique.data[:5]:
        logger.info(f"  {loc.get('subdivision_name')} → {loc.get('subdivision_name_nl')}")

if __name__ == "__main__":
    test_subdivision_sync()
