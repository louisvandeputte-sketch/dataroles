#!/usr/bin/env python3
"""Run migration 024 to add title_classification_error column."""

from pathlib import Path

migration_file = "024_add_title_classification_error.sql"
migration_path = Path(__file__).parent / "database" / "migrations" / migration_file

if not migration_path.exists():
    print(f"❌ Migration file not found: {migration_path}")
    exit(1)

print(f"📄 Migration: {migration_file}")
print("=" * 80)
sql = migration_path.read_text()
print(sql)
print("=" * 80)
print("\n⚠️  Please run this SQL in your Supabase SQL Editor:")
print("   https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new")
print("\n✅ After running the migration, the title_classification_error column will be added")
