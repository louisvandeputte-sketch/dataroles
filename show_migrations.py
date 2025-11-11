#!/usr/bin/env python3
"""Show SQL for migrations 024 and 025 to copy-paste into Supabase."""

from pathlib import Path

print("=" * 80)
print("MIGRATIES 024 & 025 - KOPIEER NAAR SUPABASE SQL EDITOR")
print("=" * 80)

migrations = [
    "024_add_title_classification_error.sql",
    "025_add_llm_enrichment_error.sql"
]

for migration_file in migrations:
    migration_path = Path(__file__).parent / "database" / "migrations" / migration_file
    
    if migration_path.exists():
        print(f"\n{'=' * 80}")
        print(f"MIGRATIE: {migration_file}")
        print(f"{'=' * 80}\n")
        
        sql = migration_path.read_text()
        print(sql)
        print()
    else:
        print(f"\n❌ Migratie niet gevonden: {migration_file}")

print("=" * 80)
print("\n📋 INSTRUCTIES:")
print("1. Ga naar: https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new")
print("2. Kopieer de SQL hierboven")
print("3. Plak in SQL Editor")
print("4. Klik 'Run'")
print("5. Herhaal voor beide migraties")
print("\n✅ Na uitvoeren: Run 'python test_retry_logic.py' om te verifiëren")
print("=" * 80)
