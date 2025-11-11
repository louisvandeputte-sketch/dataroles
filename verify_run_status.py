#!/usr/bin/env python3
"""Verify the run status has been updated."""

from database.client import db

# Check the specific run
run_id = "b1b62c12-71f9-4d14-a75b-54aedb6d1f54"

result = db.client.table("scrape_runs")\
    .select("id, status, started_at, completed_at, error_message")\
    .eq("id", run_id)\
    .single()\
    .execute()

if result.data:
    run = result.data
    print("✅ Run Status Updated:")
    print("=" * 80)
    print(f"Run ID: {run.get('id')}")
    print(f"Status: {run.get('status')}")
    print(f"Started: {run.get('started_at')}")
    print(f"Completed: {run.get('completed_at')}")
    print(f"Error: {run.get('error_message')}")
    print("=" * 80)
    
    if run.get('status') == 'failed':
        print("\n✅ SUCCESS: Run is now marked as 'failed'")
        print("The UI should no longer show it as running.")
    else:
        print(f"\n⚠️ WARNING: Run status is '{run.get('status')}', expected 'failed'")
else:
    print("❌ Run not found")

# Also check if there are any other running runs
print("\n\nChecking for other running runs...")
all_running = db.client.table("scrape_runs")\
    .select("id, search_query_id, status, started_at")\
    .eq("status", "running")\
    .execute()

if all_running.data:
    print(f"⚠️ Found {len(all_running.data)} other running run(s):")
    for run in all_running.data:
        print(f"  - Run ID: {run.get('id')}, Started: {run.get('started_at')}")
else:
    print("✅ No other running runs found")
