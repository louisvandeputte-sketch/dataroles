"""
Cleanup tech stack duplicates by merging entries and updating job assignments.

This script:
1. Identifies duplicate tech stack items (cross-table and naming variations)
2. Determines canonical entry to keep (best logo, highest relevance score)
3. Merges duplicates by:
   - Updating job assignments to point to canonical entry
   - Deactivating duplicate entries (soft delete)
4. Generates report of all changes

IMPORTANT: This script makes database changes. Review the dry-run output first!
"""

from typing import Dict, List, Tuple, Optional
from uuid import UUID
from loguru import logger
from collections import defaultdict
import json
import sys

from database.client import db


class TechStackCleanup:
    """Handle tech stack duplicate cleanup operations."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.changes = {
            "deactivated": [],
            "job_assignments_updated": [],
            "aliases_created": []
        }
    
    def analyze_and_cleanup(self):
        """Main cleanup workflow."""
        logger.info("Starting tech stack cleanup...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        
        # 1. Get all data
        languages = db.get_all_programming_languages(active_only=True)
        ecosystems = db.get_all_ecosystems(active_only=True)
        
        logger.info(f"Found {len(languages)} languages, {len(ecosystems)} ecosystems")
        
        # 2. Find cross-table duplicates (exact name match)
        self._cleanup_cross_table_duplicates(languages, ecosystems)
        
        # 3. Find naming variations (normalized match)
        self._cleanup_naming_variations(languages, ecosystems)
        
        # 4. Print summary
        self._print_summary()
        
        return self.changes
    
    def _cleanup_cross_table_duplicates(self, languages: List[Dict], ecosystems: List[Dict]):
        """
        Clean up items that exist in BOTH tables with exact same name.
        
        Strategy: Keep the entry with best data (logo > relevance_score > type preference)
        """
        logger.info("\n=== CLEANING CROSS-TABLE DUPLICATES ===")
        
        # Build name -> entry maps
        lang_map = {l['name']: l for l in languages}
        eco_map = {e['name']: e for e in ecosystems}
        
        # Find duplicates
        duplicate_names = set(lang_map.keys()) & set(eco_map.keys())
        
        logger.info(f"Found {len(duplicate_names)} cross-table duplicates")
        
        for name in sorted(duplicate_names):
            lang = lang_map[name]
            eco = eco_map[name]
            
            # Determine which to keep
            canonical, duplicate = self._choose_canonical(lang, eco, name)
            
            if canonical and duplicate:
                self._merge_entries(canonical, duplicate, f"Cross-table duplicate: {name}")
    
    def _cleanup_naming_variations(self, languages: List[Dict], ecosystems: List[Dict]):
        """
        Clean up naming variations (e.g., "PowerBI" vs "Power BI").
        
        Uses normalized comparison (lowercase, no special chars).
        """
        logger.info("\n=== CLEANING NAMING VARIATIONS ===")
        
        # Combine all tech
        all_tech = []
        for lang in languages:
            all_tech.append({**lang, 'type': 'language'})
        for eco in ecosystems:
            all_tech.append({**eco, 'type': 'ecosystem'})
        
        # Group by normalized name
        def normalize(name: str) -> str:
            import re
            return re.sub(r'[^a-z0-9]', '', name.lower())
        
        groups = defaultdict(list)
        for tech in all_tech:
            normalized = normalize(tech['name'])
            groups[normalized].append(tech)
        
        # Process groups with multiple entries
        variation_count = 0
        for normalized, group in groups.items():
            if len(group) <= 1:
                continue
            
            # Check if they have different actual names
            unique_names = set(t['name'] for t in group)
            if len(unique_names) <= 1:
                continue  # Same name, already handled in cross-table
            
            variation_count += 1
            
            # Sort by priority: has_logo > relevance_score > shortest name
            sorted_group = sorted(group, key=lambda x: (
                bool(x.get('logo_data') or x.get('logo_url')),
                x.get('relevance_score') or 0,
                -len(x['name'])
            ), reverse=True)
            
            canonical = sorted_group[0]
            duplicates = sorted_group[1:]
            
            logger.info(f"\nVariation group: {unique_names}")
            logger.info(f"  → Keep: {canonical['name']} ({canonical['type']})")
            
            for dup in duplicates:
                self._merge_entries(canonical, dup, f"Naming variation: {dup['name']} → {canonical['name']}")
        
        logger.info(f"\nProcessed {variation_count} naming variation groups")
    
    def _choose_canonical(self, lang: Dict, eco: Dict, name: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Choose which entry to keep as canonical.
        
        Priority:
        1. Has logo data
        2. Higher relevance score
        3. Prefer ecosystem over language (most cross-table items are tools/platforms)
        
        Returns: (canonical, duplicate)
        """
        lang_score = (
            bool(lang.get('logo_data') or lang.get('logo_url')),
            lang.get('relevance_score') or 0,
            0  # Language preference score
        )
        
        eco_score = (
            bool(eco.get('logo_data') or eco.get('logo_url')),
            eco.get('relevance_score') or 0,
            1  # Ecosystem preference score (higher)
        )
        
        if eco_score > lang_score:
            canonical = {**eco, 'type': 'ecosystem'}
            duplicate = {**lang, 'type': 'language'}
        else:
            canonical = {**lang, 'type': 'language'}
            duplicate = {**eco, 'type': 'ecosystem'}
        
        logger.info(f"Cross-table: {name}")
        logger.info(f"  → Keep: {canonical['type']} (logo: {bool(canonical.get('logo_data') or canonical.get('logo_url'))}, score: {canonical.get('relevance_score')})")
        logger.info(f"  → Remove: {duplicate['type']} (logo: {bool(duplicate.get('logo_data') or duplicate.get('logo_url'))}, score: {duplicate.get('relevance_score')})")
        
        return canonical, duplicate
    
    def _merge_entries(self, canonical: Dict, duplicate: Dict, reason: str):
        """
        Merge duplicate into canonical by:
        1. Updating all job assignments to point to canonical
        2. Deactivating duplicate entry
        3. Creating alias mapping
        """
        canonical_id = UUID(canonical['id'])
        duplicate_id = UUID(duplicate['id'])
        
        # Get job assignments for duplicate
        if duplicate['type'] == 'language':
            assignments = self._get_language_job_assignments(duplicate_id)
            table = 'job_programming_languages'
            id_column = 'programming_language_id'
        else:
            assignments = self._get_ecosystem_job_assignments(duplicate_id)
            table = 'job_ecosystems'
            id_column = 'ecosystem_id'
        
        logger.info(f"  → {len(assignments)} job assignments to update")
        
        if not self.dry_run:
            # Update job assignments
            for assignment in assignments:
                try:
                    # Check if canonical already assigned to this job
                    existing = self._check_existing_assignment(
                        assignment['job_posting_id'],
                        canonical_id,
                        canonical['type']
                    )
                    
                    if existing:
                        # Delete duplicate assignment (canonical already exists)
                        self._delete_assignment(assignment['id'], table)
                        logger.debug(f"    Deleted duplicate assignment for job {assignment['job_posting_id']}")
                    else:
                        # Update to point to canonical
                        self._update_assignment(assignment['id'], canonical_id, table, id_column)
                        logger.debug(f"    Updated assignment for job {assignment['job_posting_id']}")
                    
                    self.changes["job_assignments_updated"].append({
                        "job_id": assignment['job_posting_id'],
                        "from": str(duplicate_id),
                        "to": str(canonical_id),
                        "type": duplicate['type']
                    })
                except Exception as e:
                    logger.error(f"    Failed to update assignment {assignment['id']}: {e}")
            
            # Deactivate duplicate
            self._deactivate_entry(duplicate_id, duplicate['type'])
            
            # Create alias mapping
            self._create_alias(duplicate['name'], canonical['name'], canonical['type'], reason)
        
        self.changes["deactivated"].append({
            "id": str(duplicate_id),
            "name": duplicate['name'],
            "type": duplicate['type'],
            "reason": reason,
            "job_count": len(assignments)
        })
    
    def _get_language_job_assignments(self, language_id: UUID) -> List[Dict]:
        """Get all job assignments for a programming language."""
        result = db.client.table("job_programming_languages")\
            .select("*")\
            .eq("programming_language_id", str(language_id))\
            .execute()
        return result.data if result.data else []
    
    def _get_ecosystem_job_assignments(self, ecosystem_id: UUID) -> List[Dict]:
        """Get all job assignments for an ecosystem."""
        result = db.client.table("job_ecosystems")\
            .select("*")\
            .eq("ecosystem_id", str(ecosystem_id))\
            .execute()
        return result.data if result.data else []
    
    def _check_existing_assignment(self, job_id: str, tech_id: UUID, tech_type: str) -> bool:
        """Check if canonical is already assigned to this job."""
        if tech_type == 'language':
            result = db.client.table("job_programming_languages")\
                .select("id")\
                .eq("job_posting_id", job_id)\
                .eq("programming_language_id", str(tech_id))\
                .maybe_single()\
                .execute()
        else:
            result = db.client.table("job_ecosystems")\
                .select("id")\
                .eq("job_posting_id", job_id)\
                .eq("ecosystem_id", str(tech_id))\
                .maybe_single()\
                .execute()
        
        return bool(result.data)
    
    def _update_assignment(self, assignment_id: str, new_tech_id: UUID, table: str, id_column: str):
        """Update job assignment to point to canonical entry."""
        db.client.table(table)\
            .update({id_column: str(new_tech_id)})\
            .eq("id", assignment_id)\
            .execute()
    
    def _delete_assignment(self, assignment_id: str, table: str):
        """Delete duplicate job assignment."""
        db.client.table(table)\
            .delete()\
            .eq("id", assignment_id)\
            .execute()
    
    def _deactivate_entry(self, tech_id: UUID, tech_type: str):
        """Deactivate (soft delete) a tech stack entry."""
        table = "programming_languages" if tech_type == "language" else "ecosystems"
        db.client.table(table)\
            .update({"is_active": False})\
            .eq("id", str(tech_id))\
            .execute()
        logger.info(f"  → Deactivated {tech_type}: {tech_id}")
    
    def _create_alias(self, alias: str, canonical: str, tech_type: str, notes: str):
        """Create alias mapping."""
        try:
            db.client.table("tech_stack_aliases")\
                .insert({
                    "alias": alias,
                    "canonical_name": canonical,
                    "type": tech_type,
                    "notes": notes
                })\
                .execute()
            
            self.changes["aliases_created"].append({
                "alias": alias,
                "canonical": canonical,
                "type": tech_type
            })
            logger.info(f"  → Created alias: {alias} → {canonical}")
        except Exception as e:
            # Alias might already exist
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.debug(f"  → Alias already exists: {alias}")
            else:
                logger.error(f"  → Failed to create alias: {e}")
    
    def _print_summary(self):
        """Print cleanup summary."""
        print("\n" + "="*80)
        print("CLEANUP SUMMARY")
        print("="*80)
        print(f"Mode: {'DRY RUN (no changes made)' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"\nDeactivated entries: {len(self.changes['deactivated'])}")
        print(f"Job assignments updated: {len(self.changes['job_assignments_updated'])}")
        print(f"Aliases created: {len(self.changes['aliases_created'])}")
        
        if self.changes['deactivated']:
            print("\n--- Deactivated Entries ---")
            for item in self.changes['deactivated'][:20]:
                print(f"  • {item['name']} ({item['type']}) - {item['job_count']} jobs")
                print(f"    Reason: {item['reason']}")
            
            if len(self.changes['deactivated']) > 20:
                print(f"  ... and {len(self.changes['deactivated']) - 20} more")
        
        print("\n" + "="*80)
        
        if self.dry_run:
            print("\n⚠️  This was a DRY RUN. No changes were made.")
            print("Run with --execute flag to apply changes.")
        else:
            print("\n✅ Changes have been applied to the database.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up tech stack duplicates")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute changes (default is dry-run)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cleanup_report.json",
        help="Output file for changes report"
    )
    
    args = parser.parse_args()
    
    # Run cleanup
    cleanup = TechStackCleanup(dry_run=not args.execute)
    changes = cleanup.analyze_and_cleanup()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(changes, f, indent=2, default=str)
    
    logger.info(f"\nReport saved to: {args.output}")
    
    if not args.execute:
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("1. Review the dry-run output above")
        print("2. Check the report file: " + args.output)
        print("3. If everything looks good, run with --execute flag:")
        print(f"   python {sys.argv[0]} --execute")
        print("="*80)


if __name__ == "__main__":
    main()
