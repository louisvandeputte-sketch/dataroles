#!/usr/bin/env python3
"""Debug a successful run with jobs."""

import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Check a successful run with jobs
run_id = "84f065d8-54d3-4917-9a9c-a4ebceddfeb2"  # Data Governance - 13 jobs

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
    print(f'Completed: {run.get("completed_at")}')
    
    print(f'\nJobs Found: {run.get("jobs_found", 0)}')
    print(f'Jobs New: {run.get("jobs_new", 0)}')
    print(f'Jobs Updated: {run.get("jobs_updated", 0)}')
    
    metadata = run.get('metadata', {})
    if metadata:
        print('\n' + '='*80)
        print('METADATA:')
        print('='*80)
        print(json.dumps(metadata, indent=2))
        
        # Key fields to check
        print('\n' + '='*80)
        print('KEY DIAGNOSTICS:')
        print('='*80)
        print(f'Snapshot ID: {metadata.get("snapshot_id", "N/A")}')
        print(f'Bright Data Jobs Returned: {metadata.get("brightdata_jobs_returned", "N/A")}')
        print(f'Date Range: {metadata.get("date_range", "N/A")}')
        print(f'Duration: {metadata.get("duration_seconds", "N/A")} seconds')
        
        if 'query_params' in metadata:
            print('\nQuery Parameters:')
            print(json.dumps(metadata['query_params'], indent=2))
        
        if 'batch_summary' in metadata:
            print(f'\nBatch Summary: {metadata["batch_summary"]}')
    
    # Check job_scrape_history
    history = supabase.table('job_scrape_history')\
        .select('job_posting_id')\
        .eq('scrape_run_id', run_id)\
        .execute()
    
    print('\n' + '='*80)
    print('JOB SCRAPE HISTORY:')
    print('='*80)
    print(f'Jobs in history: {len(history.data) if history.data else 0}')
else:
    print(f'Run {run_id} not found')
