"""
Intelligent tech stack cleanup using AI-based categorization.

This script uses LLM to determine the correct type (language vs ecosystem)
for each tech stack item, ensuring logical merges.
"""

from typing import Dict, List, Tuple, Optional
from uuid import UUID
from loguru import logger
from collections import defaultdict
import json
import sys
from openai import OpenAI

from database.client import db
from config.settings import settings


# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def categorize_tech_with_ai(tech_names: List[str]) -> Dict[str, str]:
    """
    Use AI to categorize tech stack items as 'language' or 'ecosystem'.
    
    Args:
        tech_names: List of tech stack names to categorize
    
    Returns:
        Dictionary mapping tech name to type ('language' or 'ecosystem')
    """
    prompt = f"""You are a tech stack expert. Categorize each technology as either 'language' or 'ecosystem'.

RULES:
- 'language': Programming languages, query languages, scripting languages (Python, SQL, JavaScript, DAX, etc.)
- 'ecosystem': Tools, frameworks, platforms, databases, cloud services, BI tools (Power BI, Azure, Docker, etc.)

IMPORTANT EXAMPLES:
- Power BI → ecosystem (BI tool, not a language)
- DAX → language (query language used in Power BI)
- Python → language (programming language)
- Databricks → ecosystem (data platform)
- SQL → language (query language)
- PostgreSQL → ecosystem (database)
- React → ecosystem (framework)
- JavaScript → language (programming language)
- Azure → ecosystem (cloud platform)
- Terraform → ecosystem (infrastructure tool)
- Excel → ecosystem (spreadsheet tool)
- VBA → language (scripting language for Excel)

Categorize these technologies:
{json.dumps(tech_names, indent=2)}

Return ONLY a JSON object with this exact format:
{{
  "tech_name": "language",
  "another_tech": "ecosystem",
  ...
}}

No explanations, just the JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a tech stack categorization expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"AI categorized {len(result)} tech items")
        return result
    
    except Exception as e:
        logger.error(f"AI categorization failed: {e}")
        return {}


def get_canonical_type_for_tech(tech_name: str, existing_types: List[str], ai_categorization: Dict[str, str]) -> str:
    """
    Determine the canonical type for a tech stack item.
    
    Priority:
    1. AI categorization (most reliable)
    2. Majority vote from existing types
    3. Default to 'ecosystem' (safer choice)
    
    Args:
        tech_name: Name of the tech
        existing_types: List of types this tech currently has
        ai_categorization: AI-based categorization
    
    Returns:
        Canonical type ('language' or 'ecosystem')
    """
    # Priority 1: AI categorization
    if tech_name in ai_categorization:
        ai_type = ai_categorization[tech_name]
        logger.debug(f"AI categorized '{tech_name}' as '{ai_type}'")
        return ai_type
    
    # Priority 2: Majority vote
    if existing_types:
        type_counts = defaultdict(int)
        for t in existing_types:
            type_counts[t] += 1
        
        majority_type = max(type_counts.items(), key=lambda x: x[1])[0]
        logger.debug(f"Majority vote for '{tech_name}': {majority_type} ({type_counts})")
        return majority_type
    
    # Priority 3: Default to ecosystem
    logger.warning(f"No categorization found for '{tech_name}', defaulting to 'ecosystem'")
    return 'ecosystem'


class IntelligentTechStackCleanup:
    """Handle intelligent tech stack cleanup with AI categorization."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.changes = {
            "deactivated": [],
            "job_assignments_updated": [],
            "aliases_created": [],
            "ai_categorizations": {}
        }
        self.ai_cache = {}
    
    def analyze_and_cleanup(self):
        """Main cleanup workflow with AI categorization."""
        logger.info("Starting intelligent tech stack cleanup with AI...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        
        # 1. Get all data
        languages = db.get_all_programming_languages(active_only=True)
        ecosystems = db.get_all_ecosystems(active_only=True)
        
        logger.info(f"Found {len(languages)} languages, {len(ecosystems)} ecosystems")
        
        # 2. Build tech name → types mapping
        tech_types_map = defaultdict(list)
        all_tech = []
        
        for lang in languages:
            tech_types_map[lang['name']].append('language')
            all_tech.append({**lang, 'type': 'language'})
        
        for eco in ecosystems:
            tech_types_map[eco['name']].append('ecosystem')
            all_tech.append({**eco, 'type': 'ecosystem'})
        
        # 3. Get all unique tech names for AI categorization
        unique_tech_names = list(set(tech_types_map.keys()))
        logger.info(f"Categorizing {len(unique_tech_names)} unique tech items with AI...")
        
        # 4. AI categorization in batches (to avoid token limits)
        batch_size = 50
        ai_categorization = {}
        
        for i in range(0, len(unique_tech_names), batch_size):
            batch = unique_tech_names[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(unique_tech_names)-1)//batch_size + 1}")
            batch_result = categorize_tech_with_ai(batch)
            ai_categorization.update(batch_result)
        
        self.changes["ai_categorizations"] = ai_categorization
        logger.success(f"AI categorized {len(ai_categorization)} tech items")
        
        # 5. Find duplicates and determine canonical entries
        logger.info("\n=== FINDING DUPLICATES WITH AI-BASED CANONICAL TYPES ===")
        
        # Group by normalized name
        def normalize(name: str) -> str:
            import re
            return re.sub(r'[^a-z0-9]', '', name.lower())
        
        normalized_groups = defaultdict(list)
        for tech in all_tech:
            normalized = normalize(tech['name'])
            normalized_groups[normalized].append(tech)
        
        # 6. Process groups with duplicates
        merge_count = 0
        for normalized, group in normalized_groups.items():
            if len(group) <= 1:
                continue
            
            # Check if they have different actual names or types
            unique_names = set(t['name'] for t in group)
            unique_types = set(t['type'] for t in group)
            
            if len(unique_names) == 1 and len(unique_types) == 1:
                continue  # Same name and type, no merge needed
            
            # Determine canonical type using AI
            canonical_type = get_canonical_type_for_tech(
                list(unique_names)[0],  # Use first name for AI lookup
                [t['type'] for t in group],
                ai_categorization
            )
            
            # Find best entry of canonical type
            canonical_candidates = [t for t in group if t['type'] == canonical_type]
            
            if not canonical_candidates:
                # No entry of canonical type exists, pick best from any type
                logger.warning(f"No {canonical_type} entry found for {unique_names}, picking best available")
                canonical_candidates = group
            
            # Sort by priority: has_logo > relevance_score > shortest name
            sorted_candidates = sorted(canonical_candidates, key=lambda x: (
                bool(x.get('logo_data') or x.get('logo_url')),
                x.get('relevance_score') or 0,
                -len(x['name'])
            ), reverse=True)
            
            canonical = sorted_candidates[0]
            duplicates = [t for t in group if t['id'] != canonical['id']]
            
            if duplicates:
                merge_count += 1
                logger.info(f"\n{merge_count}. Merge group: {unique_names}")
                logger.info(f"   AI canonical type: {canonical_type}")
                logger.info(f"   → Keep: {canonical['name']} ({canonical['type']})")
                
                for dup in duplicates:
                    self._merge_entries(canonical, dup, 
                        f"AI-categorized as {canonical_type}: {dup['name']} → {canonical['name']}")
        
        logger.info(f"\nProcessed {merge_count} merge groups")
        
        # 7. Print summary
        self._print_summary()
        
        return self.changes
    
    def _merge_entries(self, canonical: Dict, duplicate: Dict, reason: str):
        """Merge duplicate into canonical (same as before)."""
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
        
        logger.info(f"     → {len(assignments)} job assignments to update")
        
        if not self.dry_run:
            # Update job assignments
            for assignment in assignments:
                try:
                    existing = self._check_existing_assignment(
                        assignment['job_posting_id'],
                        canonical_id,
                        canonical['type']
                    )
                    
                    if existing:
                        self._delete_assignment(assignment['id'], table)
                    else:
                        self._update_assignment(assignment['id'], canonical_id, table, id_column)
                    
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
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.debug(f"  → Alias already exists: {alias}")
            else:
                logger.error(f"  → Failed to create alias: {e}")
    
    def _print_summary(self):
        """Print cleanup summary."""
        print("\n" + "="*80)
        print("INTELLIGENT CLEANUP SUMMARY (AI-CATEGORIZED)")
        print("="*80)
        print(f"Mode: {'DRY RUN (no changes made)' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"\nAI Categorizations: {len(self.changes['ai_categorizations'])}")
        print(f"Deactivated entries: {len(self.changes['deactivated'])}")
        print(f"Job assignments updated: {len(self.changes['job_assignments_updated'])}")
        print(f"Aliases created: {len(self.changes['aliases_created'])}")
        
        # Show some AI categorizations
        if self.changes['ai_categorizations']:
            print("\n--- Sample AI Categorizations ---")
            important_items = ['Power BI', 'DAX', 'Python', 'Databricks', 'SQL', 'PostgreSQL', 
                             'React', 'JavaScript', 'Azure', 'Terraform', 'Excel']
            for item in important_items:
                if item in self.changes['ai_categorizations']:
                    cat_type = self.changes['ai_categorizations'][item]
                    print(f"  • {item}: {cat_type}")
        
        if self.changes['deactivated']:
            print("\n--- Deactivated Entries (first 20) ---")
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
    
    parser = argparse.ArgumentParser(description="Intelligent tech stack cleanup with AI")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute changes (default is dry-run)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="intelligent_cleanup_report.json",
        help="Output file for changes report"
    )
    
    args = parser.parse_args()
    
    # Run cleanup
    cleanup = IntelligentTechStackCleanup(dry_run=not args.execute)
    changes = cleanup.analyze_and_cleanup()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(changes, f, indent=2, default=str)
    
    logger.info(f"\nReport saved to: {args.output}")
    
    if not args.execute:
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("1. Review the AI categorizations above")
        print("2. Check the report file: " + args.output)
        print("3. If everything looks good, run with --execute flag:")
        print(f"   PYTHONPATH=. python {sys.argv[0]} --execute")
        print("="*80)


if __name__ == "__main__":
    main()
