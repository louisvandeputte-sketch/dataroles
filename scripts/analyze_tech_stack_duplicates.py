"""Analyze tech stack duplicates and generate cleanup strategy."""

from collections import defaultdict, Counter
from typing import Dict, List, Tuple
from loguru import logger
import json

from database.client import db


def analyze_duplicates() -> Dict:
    """
    Analyze all tech stack duplicates and inconsistencies.
    
    Returns:
        Dictionary with analysis results
    """
    logger.info("Fetching all tech stack data...")
    
    # Get all data
    languages = db.get_all_programming_languages(active_only=True)
    ecosystems = db.get_all_ecosystems(active_only=True)
    
    logger.info(f"Found {len(languages)} programming languages")
    logger.info(f"Found {len(ecosystems)} ecosystems")
    
    # Analysis results
    results = {
        "cross_table_duplicates": [],
        "naming_variations": defaultdict(list),
        "recommended_merges": [],
        "statistics": {}
    }
    
    # 1. Find cross-table duplicates (exact name match)
    lang_names = {l['name']: l for l in languages}
    eco_names = {e['name']: e for e in ecosystems}
    
    cross_duplicates = set(lang_names.keys()) & set(eco_names.keys())
    
    for name in sorted(cross_duplicates):
        lang = lang_names[name]
        eco = eco_names[name]
        
        results["cross_table_duplicates"].append({
            "name": name,
            "language_id": lang['id'],
            "ecosystem_id": eco['id'],
            "language_display": lang['display_name'],
            "ecosystem_display": eco['display_name'],
            "language_has_logo": bool(lang.get('logo_data') or lang.get('logo_url')),
            "ecosystem_has_logo": bool(eco.get('logo_data') or eco.get('logo_url')),
        })
    
    logger.info(f"Found {len(cross_duplicates)} cross-table duplicates")
    
    # 2. Find naming variations (case-insensitive, normalized)
    def normalize_for_comparison(name: str) -> str:
        """Normalize name for comparison (remove spaces, special chars, lowercase)."""
        import re
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    # Group by normalized name
    all_tech = []
    for lang in languages:
        all_tech.append({
            'name': lang['name'],
            'display_name': lang['display_name'],
            'type': 'language',
            'id': lang['id'],
            'has_logo': bool(lang.get('logo_data') or lang.get('logo_url')),
            'relevance_score': lang.get('relevance_score'),
            'category': lang.get('category')
        })
    
    for eco in ecosystems:
        all_tech.append({
            'name': eco['name'],
            'display_name': eco['display_name'],
            'type': 'ecosystem',
            'id': eco['id'],
            'has_logo': bool(eco.get('logo_data') or eco.get('logo_url')),
            'relevance_score': eco.get('relevance_score'),
            'category': eco.get('category')
        })
    
    # Group by normalized name
    normalized_groups = defaultdict(list)
    for tech in all_tech:
        normalized = normalize_for_comparison(tech['name'])
        normalized_groups[normalized].append(tech)
    
    # Find groups with multiple entries
    for normalized, group in normalized_groups.items():
        if len(group) > 1:
            # Get unique names in this group
            unique_names = list(set(t['name'] for t in group))
            if len(unique_names) > 1:
                results["naming_variations"][normalized] = group
    
    logger.info(f"Found {len(results['naming_variations'])} naming variation groups")
    
    # 3. Generate recommended merges
    for normalized, group in results["naming_variations"].items():
        # Determine canonical entry (priority: has_logo > relevance_score > shortest name)
        canonical = max(group, key=lambda x: (
            x['has_logo'],
            x['relevance_score'] or 0,
            -len(x['name'])  # Negative for shortest
        ))
        
        # Get all other entries
        duplicates = [t for t in group if t['id'] != canonical['id']]
        
        if duplicates:
            results["recommended_merges"].append({
                "canonical": canonical,
                "duplicates": duplicates,
                "total_count": len(group)
            })
    
    logger.info(f"Generated {len(results['recommended_merges'])} merge recommendations")
    
    # 4. Statistics
    results["statistics"] = {
        "total_languages": len(languages),
        "total_ecosystems": len(ecosystems),
        "total_tech_items": len(all_tech),
        "cross_table_duplicates": len(cross_duplicates),
        "naming_variation_groups": len(results["naming_variations"]),
        "recommended_merges": len(results["recommended_merges"]),
        "items_with_logos": sum(1 for t in all_tech if t['has_logo']),
        "items_with_relevance_score": sum(1 for t in all_tech if t['relevance_score'] is not None)
    }
    
    return results


def print_analysis_report(results: Dict):
    """Print human-readable analysis report."""
    print("\n" + "="*80)
    print("TECH STACK DUPLICATE ANALYSIS REPORT")
    print("="*80)
    
    # Statistics
    print("\n📊 STATISTICS")
    print("-" * 80)
    stats = results["statistics"]
    print(f"Total Programming Languages: {stats['total_languages']}")
    print(f"Total Ecosystems: {stats['total_ecosystems']}")
    print(f"Total Tech Items: {stats['total_tech_items']}")
    print(f"Cross-Table Duplicates: {stats['cross_table_duplicates']}")
    print(f"Naming Variation Groups: {stats['naming_variation_groups']}")
    print(f"Recommended Merges: {stats['recommended_merges']}")
    print(f"Items with Logos: {stats['items_with_logos']} ({stats['items_with_logos']/stats['total_tech_items']*100:.1f}%)")
    print(f"Items with Relevance Score: {stats['items_with_relevance_score']} ({stats['items_with_relevance_score']/stats['total_tech_items']*100:.1f}%)")
    
    # Cross-table duplicates
    print("\n🔴 CROSS-TABLE DUPLICATES (Same name in both tables)")
    print("-" * 80)
    if results["cross_table_duplicates"]:
        for dup in results["cross_table_duplicates"][:20]:  # Show first 20
            print(f"  • {dup['name']}")
            print(f"    - Language: {dup['language_display']} (logo: {dup['language_has_logo']})")
            print(f"    - Ecosystem: {dup['ecosystem_display']} (logo: {dup['ecosystem_has_logo']})")
        
        if len(results["cross_table_duplicates"]) > 20:
            print(f"  ... and {len(results['cross_table_duplicates']) - 20} more")
    else:
        print("  ✅ No cross-table duplicates found")
    
    # Naming variations
    print("\n🔶 NAMING VARIATIONS (Similar names)")
    print("-" * 80)
    if results["naming_variations"]:
        # Show top 10 most problematic
        sorted_variations = sorted(
            results["naming_variations"].items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        for normalized, group in sorted_variations:
            names = list(set(t['name'] for t in group))
            print(f"  • Group ({len(group)} items):")
            for name in sorted(names):
                matching = [t for t in group if t['name'] == name]
                types = ', '.join(set(t['type'] for t in matching))
                print(f"    - {name} ({types})")
    else:
        print("  ✅ No naming variations found")
    
    # Recommended merges
    print("\n✅ RECOMMENDED MERGES")
    print("-" * 80)
    if results["recommended_merges"]:
        for i, merge in enumerate(results["recommended_merges"][:15], 1):  # Show first 15
            canonical = merge["canonical"]
            print(f"\n  {i}. Keep: {canonical['name']} ({canonical['type']})")
            print(f"     - Display: {canonical['display_name']}")
            print(f"     - Logo: {canonical['has_logo']}, Score: {canonical['relevance_score']}")
            print(f"     Merge these {len(merge['duplicates'])} duplicates:")
            for dup in merge["duplicates"]:
                print(f"       → {dup['name']} ({dup['type']})")
        
        if len(results["recommended_merges"]) > 15:
            print(f"\n  ... and {len(results['recommended_merges']) - 15} more merge recommendations")
    else:
        print("  ✅ No merges needed")
    
    print("\n" + "="*80)


def save_analysis_to_file(results: Dict, filename: str = "tech_stack_analysis.json"):
    """Save analysis results to JSON file."""
    # Convert defaultdict to regular dict for JSON serialization
    results_copy = dict(results)
    results_copy["naming_variations"] = dict(results_copy["naming_variations"])
    
    with open(filename, 'w') as f:
        json.dump(results_copy, f, indent=2, default=str)
    
    logger.info(f"Analysis saved to {filename}")


if __name__ == "__main__":
    logger.info("Starting tech stack duplicate analysis...")
    
    results = analyze_duplicates()
    print_analysis_report(results)
    save_analysis_to_file(results)
    
    logger.success("Analysis complete!")
