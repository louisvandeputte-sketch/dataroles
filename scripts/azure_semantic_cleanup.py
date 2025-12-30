"""
Azure semantic cleanup - merge Microsoft Azure variants.

This script handles semantic duplicates like:
- "Azure Data Factory" vs "Microsoft Azure data factory"
- "Azure Synapse" vs "Microsoft Azure Synapse Analytics"
"""

from database.client import db
from typing import List, Dict, Tuple
from loguru import logger
import re


def normalize_azure_name(name: str) -> str:
    """
    Normalize Azure service names for comparison.
    
    Examples:
    - "Microsoft Azure Data Factory" → "azure data factory"
    - "Azure data lake" → "azure data lake"
    - "MS Azure Synapse Analytics" → "azure synapse analytics"
    """
    # Remove Microsoft/MS prefix
    name = re.sub(r'\b(Microsoft|MS)\s+', '', name, flags=re.IGNORECASE)
    
    # Lowercase and normalize whitespace
    name = re.sub(r'\s+', ' ', name.lower()).strip()
    
    return name


def find_azure_semantic_duplicates() -> Dict[str, List[Dict]]:
    """Find Azure services with semantic duplicates."""
    
    # Get all ecosystems
    ecos = db.get_all_ecosystems(active_only=True)
    
    # Filter Azure items
    azure_items = [e for e in ecos if 'azure' in e['name'].lower()]
    
    logger.info(f"Found {len(azure_items)} Azure items")
    
    # Group by normalized name
    groups = {}
    for item in azure_items:
        normalized = normalize_azure_name(item['name'])
        if normalized not in groups:
            groups[normalized] = []
        groups[normalized].append(item)
    
    # Filter to only groups with duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    
    logger.info(f"Found {len(duplicates)} groups with semantic duplicates")
    
    return duplicates


def choose_canonical_azure_name(items: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """
    Choose the canonical Azure service name.
    
    Preference:
    1. Without "Microsoft" prefix (shorter, cleaner)
    2. Proper capitalization (not lowercase)
    3. Highest relevance score
    4. Has logo
    """
    
    # Sort by preference
    def score_item(item):
        name = item['name']
        has_microsoft = 'microsoft' in name.lower()
        is_lowercase = name[0].islower() if name else False
        has_logo = bool(item.get('logo_data') or item.get('logo_url'))
        relevance = item.get('relevance_score') or 0
        
        # Prefer: no Microsoft, proper case, high score, has logo
        return (
            not has_microsoft,  # Prefer without Microsoft
            not is_lowercase,   # Prefer proper capitalization
            has_logo,           # Prefer with logo
            relevance,          # Prefer higher score
            -len(name)          # Prefer shorter name
        )
    
    sorted_items = sorted(items, key=score_item, reverse=True)
    canonical = sorted_items[0]
    duplicates = sorted_items[1:]
    
    return canonical, duplicates


def merge_azure_duplicate(canonical: Dict, duplicate: Dict, dry_run: bool = True):
    """Merge Azure duplicate into canonical."""
    
    canonical_id = canonical['id']
    duplicate_id = duplicate['id']
    
    logger.info(f"  Merging '{duplicate['name']}' → '{canonical['name']}'")
    
    # Get job assignments
    assignments = db.client.table("job_ecosystems")\
        .select("*")\
        .eq("ecosystem_id", duplicate_id)\
        .execute()
    
    job_assignments = assignments.data if assignments.data else []
    logger.info(f"    → {len(job_assignments)} job assignments")
    
    if dry_run:
        return len(job_assignments)
    
    # Update assignments
    updated = 0
    deleted = 0
    
    for assignment in job_assignments:
        job_id = assignment['job_posting_id']
        
        # Check if canonical already assigned
        existing = db.client.table("job_ecosystems")\
            .select("id")\
            .eq("job_posting_id", job_id)\
            .eq("ecosystem_id", canonical_id)\
            .maybe_single()\
            .execute()
        
        if existing and existing.data:
            # Delete duplicate assignment
            db.client.table("job_ecosystems")\
                .delete()\
                .eq("id", assignment['id'])\
                .execute()
            deleted += 1
        else:
            # Update to canonical
            db.client.table("job_ecosystems")\
                .update({"ecosystem_id": canonical_id})\
                .eq("id", assignment['id'])\
                .execute()
            updated += 1
    
    # Deactivate duplicate
    db.client.table("ecosystems")\
        .update({"is_active": False})\
        .eq("id", duplicate_id)\
        .execute()
    
    # Create alias
    try:
        db.client.table("tech_stack_aliases")\
            .insert({
                "alias": duplicate['name'],
                "canonical_name": canonical['name'],
                "type": "ecosystem",
                "notes": f"Azure semantic duplicate: {duplicate['name']} → {canonical['name']}"
            })\
            .execute()
    except Exception as e:
        if "duplicate" not in str(e).lower():
            logger.warning(f"    Failed to create alias: {e}")
    
    logger.info(f"    ✓ Updated: {updated}, Deleted: {deleted}")
    
    return updated + deleted


def main(dry_run: bool = True):
    """Main cleanup workflow."""
    
    print("="*80)
    print("AZURE SEMANTIC CLEANUP")
    print("="*80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}\n")
    
    # Find duplicates
    duplicates = find_azure_semantic_duplicates()
    
    if not duplicates:
        print("✅ No Azure semantic duplicates found!")
        return
    
    print(f"Found {len(duplicates)} groups with semantic duplicates:\n")
    
    total_assignments = 0
    total_merged = 0
    
    # Process each group
    for i, (normalized, items) in enumerate(sorted(duplicates.items()), 1):
        canonical, dups = choose_canonical_azure_name(items)
        
        print(f"{i}. {normalized}")
        print(f"   ✅ Keep: '{canonical['name']}' (score: {canonical.get('relevance_score')})")
        
        for dup in dups:
            print(f"   ❌ Merge: '{dup['name']}' (score: {dup.get('relevance_score')})")
            assignments = merge_azure_duplicate(canonical, dup, dry_run)
            total_assignments += assignments
            total_merged += 1
        
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Groups processed: {len(duplicates)}")
    print(f"Items to merge: {total_merged}")
    print(f"Job assignments to update: {total_assignments}")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN. No changes were made.")
        print("Run with --execute to apply changes.")
    else:
        print("\n✅ Changes applied successfully!")
    
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Azure semantic cleanup")
    parser.add_argument("--execute", action="store_true", help="Execute changes")
    args = parser.parse_args()
    
    main(dry_run=not args.execute)
