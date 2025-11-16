#!/usr/bin/env python3
"""Check status of currently running scrapes."""

from database.client import db
from datetime import datetime, timedelta

# Get all running scrapes
result = db.client.table("scrape_runs")\
    .select("id, search_query, location_query, status, started_at, jobs_found, metadata, platform")\
    .eq("status", "running")\
    .order("started_at", desc=True)\
    .execute()

print(f"\n{'='*80}")
print(f"CURRENTLY RUNNING SCRAPES: {len(result.data)}")
print(f"{'='*80}\n")

for run in result.data:
    started = datetime.fromisoformat(run['started_at'].replace('Z', '+00:00'))
    duration = datetime.utcnow() - started.replace(tzinfo=None)
    
    print(f"Run ID: {run['id']}")
    print(f"Platform: {run.get('platform', 'N/A')}")
    print(f"Query: {run.get('search_query', 'N/A')}")
    print(f"Location: {run.get('location_query', 'N/A')}")
    print(f"Status: {run['status']}")
    print(f"Started: {run['started_at']}")
    print(f"Duration: {duration}")
    print(f"Jobs Found: {run.get('jobs_found', 0)}")
    
    metadata = run.get('metadata', {})
    if metadata:
        print(f"Metadata:")
        if 'snapshot_id' in metadata:
            print(f"  - Snapshot ID: {metadata['snapshot_id']}")
        if 'date_range' in metadata:
            print(f"  - Date Range: {metadata['date_range']}")
        if 'brightdata_jobs_returned' in metadata:
            print(f"  - Bright Data Jobs: {metadata['brightdata_jobs_returned']}")
    
    # Check if stuck (running for more than 30 minutes)
    if duration > timedelta(minutes=30):
        print(f"⚠️  WARNING: Run has been running for {duration.total_seconds()/60:.1f} minutes!")
    
    print(f"{'-'*80}\n")

# Summary
if result.data:
    stuck_runs = [r for r in result.data if (datetime.utcnow() - datetime.fromisoformat(r['started_at'].replace('Z', '+00:00')).replace(tzinfo=None)) > timedelta(minutes=30)]
    if stuck_runs:
        print(f"\n⚠️  {len(stuck_runs)} STUCK RUNS detected (running > 30 minutes)")
        print(f"Consider running cleanup: POST /api/runs/cleanup-stuck or /api/indeed/runs/cleanup-stuck")
else:
    print("✅ No running scrapes found")
