#!/usr/bin/env python3
"""Run migration 073"""

from database.client import db

print("\n🚀 Running migration 073: Fix posted_date_corrected NULL handling...\n")

# Read migration file
with open("/Users/louisvandeputte/datarole/database/migrations/073_fix_posted_date_corrected_null.sql", "r") as f:
    sql = f.read()

# Execute migration
try:
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for stmt in statements:
        if stmt:
            print(f"Executing: {stmt[:100]}...")
            db.client.rpc('exec_sql', {'sql': stmt}).execute()
    
    print("\n✅ Migration 073 completed successfully!")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    raise
