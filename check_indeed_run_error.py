#!/usr/bin/env python3
"""Check Indeed run error details."""

from database.client import db

# Get latest Indeed run
result = db.client.table("scrape_runs")\
    .select("*")\
    .eq("platform", "indeed_brightdata")\
    .order("started_at", desc=True)\
    .limit(1)\
    .execute()

if result.data:
    run = result.data[0]
    run_id = run.get('id')
    
    print(f"Latest Indeed Run: {run_id}")
    print("=" * 80)
    print(f"\nRun Details:")
    print(f"  Query: {run.get('search_query')}")
    print(f"  Location: {run.get('location_query')}")
    print(f"  Platform: {run.get('platform')}")
    print(f"  Status: {run.get('status')}")
    print(f"  Started: {run.get('started_at')}")
    print(f"  Completed: {run.get('completed_at')}")
    print(f"  Jobs found: {run.get('jobs_found')}")
    print(f"  Jobs new: {run.get('jobs_new')}")
    print(f"  Jobs updated: {run.get('jobs_updated')}")
    print(f"  Error message: {run.get('error_message')}")
    print(f"\nMetadata:")
    import json
    print(json.dumps(run.get('metadata'), indent=2))
    
    # Check if there are any scrape_history entries
    print(f"\n" + "=" * 80)
    print("Checking scrape_history...")
    history = db.client.table("scrape_history")\
        .select("*")\
        .eq("scrape_run_id", run_id)\
        .limit(5)\
        .execute()
    
    print(f"Found {len(history.data)} entries in scrape_history")
    if history.data:
        print("\nFirst entry:")
        print(json.dumps(history.data[0], indent=2, default=str))
else:
    print("No Indeed runs found")
