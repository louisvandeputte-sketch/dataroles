#!/usr/bin/env python3
"""
Add logos for Alteryx, Power BI, Snowflake, SQL, and Excel.
Batch 2 of uploaded logos.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from database.client import db


# Logo mappings for batch 2
LOGO_MAPPINGS = [
    {
        "name": "Alteryx",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/f/f4/Alteryx_logo.svg",
        "description": "Blue circle with 'a'"
    },
    {
        "name": "Power BI",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/c/cf/New_Power_BI_Logo.svg",
        "description": "Yellow/orange bar chart"
    },
    {
        "name": "Snowflake",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg",
        "description": "Blue snowflake"
    },
    {
        "name": "SQL",
        "type": "language",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/8/87/Sql_data_base_with_logo.png",
        "description": "Blue database cylinder with SQL"
    },
    {
        "name": "Excel",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/3/34/Microsoft_Office_Excel_%282019%E2%80%93present%29.svg",
        "description": "Green Excel logo"
    }
]


def find_tech_item(name: str, tech_type: str):
    """Find tech item by name."""
    if tech_type == "language":
        items = db.get_all_programming_languages(active_only=True) or []
    else:
        items = db.get_all_ecosystems(active_only=True) or []
    
    # Try exact match
    for item in items:
        if item['name'].lower() == name.lower():
            return item
    
    # Try partial match
    for item in items:
        if name.lower() in item['name'].lower():
            return item
    
    return None


def update_logo(item_id: str, tech_type: str, logo_url: str) -> bool:
    """Update tech item with logo URL."""
    try:
        table = "programming_languages" if tech_type == "language" else "ecosystems"
        db.client.table(table)\
            .update({"logo_url": logo_url})\
            .eq("id", item_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update: {e}")
        return False


def main():
    """Main entry point."""
    logger.info("="*80)
    logger.info("ADD LOGOS - BATCH 2")
    logger.info("="*80)
    logger.info(f"Processing {len(LOGO_MAPPINGS)} logos\n")
    
    stats = {"found": 0, "updated": 0, "skipped": 0, "not_found": 0}
    
    for mapping in LOGO_MAPPINGS:
        name = mapping["name"]
        tech_type = mapping["type"]
        logo_url = mapping["logo_url"]
        
        logger.info(f"Processing: {name} ({tech_type})")
        logger.info(f"  Description: {mapping['description']}")
        
        # Find tech item
        item = find_tech_item(name, tech_type)
        
        if not item:
            logger.warning(f"  ❌ Not found in database")
            stats["not_found"] += 1
            continue
        
        stats["found"] += 1
        logger.info(f"  ✅ Found: {item['name']}")
        
        # Check if already has logo
        current_logo = item.get('logo_url') or item.get('logo_data')
        if current_logo:
            logger.info(f"  ⚠️  Already has logo: {str(current_logo)[:50]}...")
            logger.info(f"  🔄 Updating to new logo")
        
        # Update logo
        if update_logo(item['id'], tech_type, logo_url):
            logger.success(f"  ✅ Updated with logo: {logo_url}")
            stats["updated"] += 1
        else:
            logger.error(f"  ❌ Failed to update")
        
        print()
    
    # Summary
    logger.info("="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total: {len(LOGO_MAPPINGS)}")
    logger.info(f"Found in database: {stats['found']}")
    logger.info(f"Updated: {stats['updated']}")
    logger.info(f"Not found: {stats['not_found']}")
    
    if stats['updated'] > 0:
        logger.success(f"\n✅ Successfully added/updated {stats['updated']} logos!")


if __name__ == "__main__":
    main()
