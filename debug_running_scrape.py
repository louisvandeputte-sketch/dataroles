#!/usr/bin/env python3
"""Debug a specific running scrape."""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Check the most recent running scrape
run_id = "ba12a268-66fe-44d2-a777-63ff9fd8726f"  # PowerBI LinkedIn

result = supabase.table('scrape_runs')\
    .select('*')\
    .eq('id', run_id)\
    .single()\
    .execute()

if result.data:
    run = result.data
    print('\n' + '='*80)
    print(f'SCRAPE RUN: {run_id}')
    print('='*80)
    print(f'Query: {run.get("search_query")}')
    print(f'Location: {run.get("location_query")}')
    print(f'Platform: {run.get("platform")}')
    print(f'Status: {run["status"]}')
    print(f'Started: {run["started_at"]}')
    
    started = datetime.fromisoformat(run['started_at'].replace('Z', '+00:00'))
    duration = datetime.utcnow() - started.replace(tzinfo=None)
    print(f'Duration: {duration}')
    print(f'Duration (minutes): {duration.total_seconds() / 60:.1f}')
    
    print(f'\nJobs Found: {run.get("jobs_found", 0)}')
    print(f'Jobs New: {run.get("jobs_new", 0)}')
    print(f'Jobs Updated: {run.get("jobs_updated", 0)}')
    
    metadata = run.get('metadata', {})
    if metadata:
        print('\nMetadata:')
        import json
        print(json.dumps(metadata, indent=2))
    
    if run.get('error_message'):
        print(f'\nError Message: {run["error_message"]}')
    
    # Check if this is a stuck run
    if duration.total_seconds() > 1800:  # 30 minutes
        print(f'\n⚠️  WARNING: This run has been running for {duration.total_seconds()/60:.1f} minutes!')
        print('This is likely a stuck run that should be cleaned up.')
else:
    print(f'Run {run_id} not found')
