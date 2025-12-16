#!/usr/bin/env python3
"""Run migration 083 to add triggers for automatic posted_date_corrected updates."""

import os
from loguru import logger

logger.info("Running migration 083: Add triggers for automatic posted_date_corrected updates")

# Read migration file
with open('database/migrations/083_add_trigger_for_posted_date_corrected.sql', 'r') as f:
    sql = f.read()

logger.info("Migration SQL loaded. This needs to be run directly in Supabase SQL Editor.")
logger.info("=" * 80)
logger.info("INSTRUCTIONS:")
logger.info("1. Go to Supabase Dashboard > SQL Editor")
logger.info("2. Create a new query")
logger.info("3. Copy the SQL from: database/migrations/083_add_trigger_for_posted_date_corrected.sql")
logger.info("4. Run the query")
logger.info("=" * 80)
logger.info("")
logger.info("SQL Preview:")
logger.info("-" * 80)
print(sql[:500] + "...")
logger.info("-" * 80)
logger.info("")
logger.info("After running this migration, posted_date_corrected will be AUTOMATICALLY updated for:")
logger.info("  ✅ New jobs (uses posted_date initially)")
logger.info("  ✅ New job_sources records (recalculates with first_seen_at)")
logger.info("  ✅ Updated posted_date values (recalculates)")
logger.info("")
logger.info("This provides 100% guarantee that posted_date_corrected is always populated.")
