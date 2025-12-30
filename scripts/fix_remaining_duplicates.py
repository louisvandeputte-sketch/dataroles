"""Fix remaining duplicates after cleanup."""

from database.client import db
from uuid import UUID
from loguru import logger

def fix_power_bi_duplicates():
    """Manually fix Power BI duplicates."""
    
    # Get all Power BI ecosystems
    ecos = db.get_all_ecosystems(active_only=True)
    pb_ecos = [e for e in ecos if 'power' in e['name'].lower() and 'bi' in e['name'].lower()]
    
    print(f"\nFound {len(pb_ecos)} Power BI entries:")
    for e in pb_ecos:
        print(f"  - {e['name']} (id: {e['id']}, score: {e.get('relevance_score')})")
    
    if len(pb_ecos) <= 1:
        print("✅ No duplicates to fix!")
        return
    
    # Choose canonical: highest relevance score
    canonical = max(pb_ecos, key=lambda x: x.get('relevance_score') or 0)
    duplicates = [e for e in pb_ecos if e['id'] != canonical['id']]
    
    print(f"\n✅ Canonical: {canonical['name']} (score: {canonical.get('relevance_score')})")
    print(f"❌ Duplicates to merge:")
    for dup in duplicates:
        print(f"   - {dup['name']} (score: {dup.get('relevance_score')})")
    
    # Merge each duplicate
    for dup in duplicates:
        print(f"\nMerging {dup['name']} → {canonical['name']}...")
        
        # Get job assignments
        assignments = db.client.table("job_ecosystems")\
            .select("*")\
            .eq("ecosystem_id", dup['id'])\
            .execute()
        
        job_assignments = assignments.data if assignments.data else []
        print(f"  Found {len(job_assignments)} job assignments")
        
        # Update or delete each assignment
        for assignment in job_assignments:
            job_id = assignment['job_posting_id']
            
            # Check if canonical already assigned
            existing = db.client.table("job_ecosystems")\
                .select("id")\
                .eq("job_posting_id", job_id)\
                .eq("ecosystem_id", canonical['id'])\
                .maybe_single()\
                .execute()
            
            if existing and existing.data:
                # Delete duplicate assignment
                db.client.table("job_ecosystems")\
                    .delete()\
                    .eq("id", assignment['id'])\
                    .execute()
                print(f"    ✓ Deleted duplicate assignment for job {job_id[:8]}...")
            else:
                # Update to canonical
                db.client.table("job_ecosystems")\
                    .update({"ecosystem_id": canonical['id']})\
                    .eq("id", assignment['id'])\
                    .execute()
                print(f"    ✓ Updated assignment for job {job_id[:8]}...")
        
        # Deactivate duplicate
        db.client.table("ecosystems")\
            .update({"is_active": False})\
            .eq("id", dup['id'])\
            .execute()
        print(f"  ✓ Deactivated {dup['name']}")

def fix_remaining_cross_table_duplicates():
    """Fix remaining cross-table duplicates."""
    
    langs = db.get_all_programming_languages(active_only=True)
    ecos = db.get_all_ecosystems(active_only=True)
    
    lang_names = {l['name']: l for l in langs}
    eco_names = {e['name']: e for e in ecos}
    
    cross_dups = set(lang_names.keys()) & set(eco_names.keys())
    
    print(f"\n\nFound {len(cross_dups)} cross-table duplicates:")
    for name in sorted(cross_dups):
        print(f"  - {name}")
    
    if not cross_dups:
        print("✅ No cross-table duplicates!")
        return
    
    # Fix each duplicate
    for name in cross_dups:
        lang = lang_names[name]
        eco = eco_names[name]
        
        print(f"\nFixing {name}...")
        print(f"  Language: score={lang.get('relevance_score')}, logo={bool(lang.get('logo_data') or lang.get('logo_url'))}")
        print(f"  Ecosystem: score={eco.get('relevance_score')}, logo={bool(eco.get('logo_data') or eco.get('logo_url'))}")
        
        # Determine which to keep (prefer ecosystem for most items)
        # Special cases: VBA, XML are languages
        if name in ['VBA', 'XML']:
            canonical = lang
            duplicate = eco
            canonical_type = 'language'
        else:
            canonical = eco
            duplicate = lang
            canonical_type = 'ecosystem'
        
        print(f"  → Keeping {canonical_type}: {canonical['name']}")
        
        # Get job assignments for duplicate
        if duplicate == lang:
            table = "job_programming_languages"
            id_col = "programming_language_id"
        else:
            table = "job_ecosystems"
            id_col = "ecosystem_id"
        
        assignments = db.client.table(table)\
            .select("*")\
            .eq(id_col, duplicate['id'])\
            .execute()
        
        job_assignments = assignments.data if assignments.data else []
        print(f"  Found {len(job_assignments)} job assignments to update")
        
        # For cross-table, we need to move assignments to the other table
        for assignment in job_assignments:
            job_id = assignment['job_posting_id']
            req_level = assignment.get('requirement_level')
            
            # Check if canonical already assigned
            if canonical_type == 'language':
                check_table = "job_programming_languages"
                check_col = "programming_language_id"
            else:
                check_table = "job_ecosystems"
                check_col = "ecosystem_id"
            
            existing = db.client.table(check_table)\
                .select("id")\
                .eq("job_posting_id", job_id)\
                .eq(check_col, canonical['id'])\
                .maybe_single()\
                .execute()
            
            if existing and existing.data:
                # Just delete old assignment
                db.client.table(table)\
                    .delete()\
                    .eq("id", assignment['id'])\
                    .execute()
                print(f"    ✓ Deleted duplicate assignment for job {job_id[:8]}...")
            else:
                # Create new assignment in correct table
                db.client.table(check_table)\
                    .insert({
                        "job_posting_id": job_id,
                        check_col: canonical['id'],
                        "requirement_level": req_level
                    })\
                    .execute()
                
                # Delete old assignment
                db.client.table(table)\
                    .delete()\
                    .eq("id", assignment['id'])\
                    .execute()
                print(f"    ✓ Moved assignment for job {job_id[:8]}...")
        
        # Deactivate duplicate
        dup_table = "programming_languages" if duplicate == lang else "ecosystems"
        db.client.table(dup_table)\
            .update({"is_active": False})\
            .eq("id", duplicate['id'])\
            .execute()
        print(f"  ✓ Deactivated {duplicate['name']} ({dup_table})")

if __name__ == "__main__":
    print("="*80)
    print("FIXING REMAINING DUPLICATES")
    print("="*80)
    
    # Fix Power BI
    fix_power_bi_duplicates()
    
    # Fix cross-table duplicates
    fix_remaining_cross_table_duplicates()
    
    print("\n" + "="*80)
    print("✅ DONE!")
    print("="*80)
