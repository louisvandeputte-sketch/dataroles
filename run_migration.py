#!/usr/bin/env python3
"""Run database migration."""

from database import db
from pathlib import Path

def run_migration(migration_file: str):
    """Execute a SQL migration file."""
    migration_path = Path(__file__).parent / "database" / "migrations" / migration_file
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    print(f"📄 Reading migration: {migration_file}")
    sql = migration_path.read_text()
    
    print(f"🔄 Executing migration...")
    try:
        # Execute SQL via Supabase RPC or direct SQL
        # Note: Supabase Python client doesn't support raw SQL execution
        # We need to run this manually in Supabase SQL Editor
        print(f"\n{'='*80}")
        print("⚠️  MANUAL ACTION REQUIRED")
        print(f"{'='*80}")
        print("\nPlease run the following SQL in your Supabase SQL Editor:")
        print(f"\nhttps://supabase.com/dashboard/project/YOUR_PROJECT/sql/new\n")
        print(f"{'='*80}")
        print(sql)
        print(f"{'='*80}\n")
        
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration Tool\n")
    
    success = run_migration("001_add_search_queries_table.sql")
    
    if success:
        print("\n✅ Migration SQL prepared!")
        print("   Please copy the SQL above and run it in Supabase SQL Editor")
    else:
        print("\n❌ Migration preparation failed")
