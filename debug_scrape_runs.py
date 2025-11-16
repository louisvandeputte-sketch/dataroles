#!/usr/bin/env python3
"""Debug script to check recent scrape runs."""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Get recent scrape runs (last 7 days)
week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
result = supabase.table('scrape_runs')\
    .select('id, search_query, location_query, status, started_at, jobs_found, jobs_new, jobs_updated, metadata, platform')\
    .gte('started_at', week_ago)\
    .order('started_at', desc=True)\
    .limit(15)\
    .execute()

print('\n' + '='*80)
print(f'RECENT SCRAPE RUNS (last 7 days): {len(result.data)}')
print('='*80 + '\n')

for run in result.data:
    print(f'Run ID: {run["id"]}')
    print(f'Platform: {run.get("platform", "N/A")}')
    print(f'Query: {run.get("search_query", "N/A")}')
    print(f'Location: {run.get("location_query", "N/A")}')
    print(f'Status: {run["status"]}')
    print(f'Started: {run["started_at"]}')
    print(f'Jobs Found: {run.get("jobs_found", 0)}')
    print(f'Jobs New: {run.get("jobs_new", 0)}')
    print(f'Jobs Updated: {run.get("jobs_updated", 0)}')
    
    metadata = run.get('metadata', {})
    if metadata:
        if 'brightdata_jobs_returned' in metadata:
            print(f'Bright Data Jobs Returned: {metadata["brightdata_jobs_returned"]}')
        if 'date_range' in metadata:
            print(f'Date Range: {metadata["date_range"]}')
        if 'snapshot_id' in metadata:
            print(f'Snapshot ID: {metadata["snapshot_id"]}')
        if 'error_type' in metadata:
            print(f'Error Type: {metadata["error_type"]}')
    
    if run.get('error_message'):
        print(f'Error Message: {run["error_message"][:200]}...')
    
    print('-'*80 + '\n')

# Summary
completed = [r for r in result.data if r['status'] == 'completed']
failed = [r for r in result.data if r['status'] == 'failed']
running = [r for r in result.data if r['status'] == 'running']

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
print(f'Total runs: {len(result.data)}')
print(f'Completed: {len(completed)}')
print(f'Failed: {len(failed)}')
print(f'Running: {len(running)}')

# Check for runs with 0 jobs
zero_jobs = [r for r in completed if r.get('jobs_found', 0) == 0]
if zero_jobs:
    print(f'\n⚠️  WARNING: {len(zero_jobs)} completed runs with 0 jobs found!')
    for run in zero_jobs:
        print(f'  - {run["search_query"]} in {run["location_query"]} (ID: {run["id"]})')
        metadata = run.get('metadata', {})
        if 'brightdata_jobs_returned' in metadata:
            print(f'    Bright Data returned: {metadata["brightdata_jobs_returned"]} jobs')
