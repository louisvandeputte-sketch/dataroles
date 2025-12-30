#!/usr/bin/env python3
"""
Bulk add logos to tech stack items based on image filenames.

This script:
1. Scans a directory for logo images
2. Matches filenames to tech stack items (languages/ecosystems)
3. Uploads logos and updates the database

Usage:
    python3 scripts/bulk_add_logos.py --logo-dir /path/to/logos
"""

import sys
from pathlib import Path
import base64
import mimetypes
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from database.client import db
import argparse


# Logo URL mappings (for known public URLs)
LOGO_URL_MAPPINGS = {
    "hadoop": "https://upload.wikimedia.org/wikipedia/commons/0/0e/Hadoop_logo.svg",
    "python": "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg",
    "tensorflow": "https://upload.wikimedia.org/wikipedia/commons/2/2d/Tensorflow_logo.svg",
    "r": "https://www.r-project.org/logo/Rlogo.svg",
    "databricks": "https://upload.wikimedia.org/wikipedia/commons/6/63/Databricks_Logo.png",
}


def normalize_name(name: str) -> str:
    """Normalize name for matching (lowercase, no spaces/special chars)."""
    return name.lower().replace(" ", "").replace("-", "").replace("_", "")


def find_matching_tech_item(filename: str) -> Optional[Tuple[Dict, str]]:
    """
    Find matching tech stack item based on filename.
    
    Returns:
        Tuple of (item_dict, type) where type is 'language' or 'ecosystem'
        None if no match found
    """
    # Remove file extension and normalize
    name_from_file = Path(filename).stem
    normalized_filename = normalize_name(name_from_file)
    
    logger.debug(f"Looking for match: '{name_from_file}' (normalized: '{normalized_filename}')")
    
    # Get all tech items
    languages = db.get_all_programming_languages(active_only=True) or []
    ecosystems = db.get_all_ecosystems(active_only=True) or []
    
    # Try exact match first
    for lang in languages:
        if normalize_name(lang['name']) == normalized_filename:
            logger.info(f"✅ Exact match found: {lang['name']} (language)")
            return (lang, 'language')
    
    for eco in ecosystems:
        if normalize_name(eco['name']) == normalized_filename:
            logger.info(f"✅ Exact match found: {eco['name']} (ecosystem)")
            return (eco, 'ecosystem')
    
    # Try partial match (filename contains tech name or vice versa)
    for lang in languages:
        normalized_lang = normalize_name(lang['name'])
        if normalized_filename in normalized_lang or normalized_lang in normalized_filename:
            logger.info(f"⚠️  Partial match found: {lang['name']} (language)")
            return (lang, 'language')
    
    for eco in ecosystems:
        normalized_eco = normalize_name(eco['name'])
        if normalized_filename in normalized_eco or normalized_eco in normalized_filename:
            logger.info(f"⚠️  Partial match found: {eco['name']} (ecosystem)")
            return (eco, 'ecosystem')
    
    logger.warning(f"❌ No match found for: {name_from_file}")
    return None


def get_logo_url_for_name(name: str) -> Optional[str]:
    """Get public logo URL for known tech items."""
    normalized = normalize_name(name)
    return LOGO_URL_MAPPINGS.get(normalized)


def update_tech_item_logo(item_id: str, item_type: str, logo_url: str) -> bool:
    """Update tech item with logo URL."""
    try:
        table = "programming_languages" if item_type == "language" else "ecosystems"
        db.client.table(table)\
            .update({"logo_url": logo_url})\
            .eq("id", item_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update {item_type} {item_id}: {e}")
        return False


def process_logo_directory(logo_dir: Path, dry_run: bool = True) -> Dict:
    """
    Process all logo files in directory.
    
    Args:
        logo_dir: Path to directory containing logo images
        dry_run: If True, don't actually update database
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        "total_files": 0,
        "matched": 0,
        "unmatched": 0,
        "updated": 0,
        "failed": 0,
        "skipped": 0,
        "matches": []
    }
    
    # Supported image extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp'}
    
    # Get all image files
    image_files = [
        f for f in logo_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    stats["total_files"] = len(image_files)
    
    logger.info(f"Found {len(image_files)} image files in {logo_dir}")
    
    for image_file in image_files:
        logger.info(f"\nProcessing: {image_file.name}")
        
        # Find matching tech item
        match = find_matching_tech_item(image_file.name)
        
        if not match:
            stats["unmatched"] += 1
            continue
        
        item, item_type = match
        stats["matched"] += 1
        
        # Check if already has logo
        if item.get('logo_url') or item.get('logo_data'):
            logger.info(f"  ⏭️  {item['name']} already has a logo, skipping")
            stats["skipped"] += 1
            continue
        
        # Get logo URL (prefer public URL if available)
        logo_url = get_logo_url_for_name(item['name'])
        
        if not logo_url:
            # For now, we'll use public URLs only
            # In production, you'd upload to your CDN/storage
            logger.warning(f"  ⚠️  No public URL found for {item['name']}, skipping")
            stats["skipped"] += 1
            continue
        
        stats["matches"].append({
            "file": image_file.name,
            "tech_name": item['name'],
            "tech_type": item_type,
            "logo_url": logo_url
        })
        
        if dry_run:
            logger.info(f"  🔍 DRY RUN: Would update {item['name']} with {logo_url}")
            stats["updated"] += 1
        else:
            if update_tech_item_logo(item['id'], item_type, logo_url):
                logger.success(f"  ✅ Updated {item['name']} with logo")
                stats["updated"] += 1
            else:
                logger.error(f"  ❌ Failed to update {item['name']}")
                stats["failed"] += 1
    
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bulk add logos to tech stack items")
    parser.add_argument(
        "--logo-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing logo images (default: current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Don't actually update database (default: True)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually update database (overrides --dry-run)"
    )
    
    args = parser.parse_args()
    
    # Override dry_run if --execute is specified
    dry_run = not args.execute
    
    logger.info("="*80)
    logger.info("BULK ADD LOGOS TO TECH STACK")
    logger.info("="*80)
    logger.info(f"Logo directory: {args.logo_dir}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    logger.info("="*80)
    
    if not args.logo_dir.exists():
        logger.error(f"Directory not found: {args.logo_dir}")
        return
    
    # Process logos
    stats = process_logo_directory(args.logo_dir, dry_run=dry_run)
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total files: {stats['total_files']}")
    logger.info(f"Matched: {stats['matched']}")
    logger.info(f"Unmatched: {stats['unmatched']}")
    logger.info(f"Updated: {stats['updated']}")
    logger.info(f"Skipped (already has logo): {stats['skipped']}")
    logger.info(f"Failed: {stats['failed']}")
    
    if stats['matches']:
        logger.info("\n📋 Matches found:")
        for match in stats['matches']:
            logger.info(f"  • {match['file']} → {match['tech_name']} ({match['tech_type']})")
    
    if dry_run and stats['matched'] > 0:
        logger.info("\n⚠️  This was a DRY RUN. No changes were made.")
        logger.info("Run with --execute to apply changes.")
    elif stats['updated'] > 0:
        logger.success(f"\n✅ Successfully updated {stats['updated']} tech items!")


if __name__ == "__main__":
    main()
