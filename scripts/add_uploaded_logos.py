#!/usr/bin/env python3
"""
Add logos for Hadoop, Python, TensorFlow, R, and Databricks.
Based on the 5 uploaded images.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from database.client import db


# Logo mappings based on uploaded images
LOGO_MAPPINGS = [
    {
        "name": "Hadoop",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/0/0e/Hadoop_logo.svg",
        "description": "Yellow elephant logo"
    },
    {
        "name": "Python",
        "type": "language",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg",
        "description": "Blue and yellow snake logo"
    },
    {
        "name": "TensorFlow",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/2/2d/Tensorflow_logo.svg",
        "description": "Orange T logo"
    },
    {
        "name": "R",
        "type": "language",
        "logo_url": "https://www.r-project.org/logo/Rlogo.svg",
        "description": "Blue R logo"
    },
    {
        "name": "Databricks",
        "type": "ecosystem",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/6/63/Databricks_Logo.png",
        "description": "Orange star logo"
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
    logger.info("ADD LOGOS FROM UPLOADED IMAGES")
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
        if item.get('logo_url') or item.get('logo_data'):
            logger.info(f"  ⏭️  Already has logo, skipping")
            stats["skipped"] += 1
            continue
        
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
    logger.info(f"Skipped (already has logo): {stats['skipped']}")
    logger.info(f"Not found: {stats['not_found']}")
    
    if stats['updated'] > 0:
        logger.success(f"\n✅ Successfully added {stats['updated']} logos!")


if __name__ == "__main__":
    main()
