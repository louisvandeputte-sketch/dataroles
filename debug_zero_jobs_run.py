#!/usr/bin/env python3
"""Debug a completed run with 0 jobs."""

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

# Check the Data Engineer run that returned 0 jobs
run_id = "4778d695-9b41-4be5-93ed-3345b9c80e4a"

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
        
        if 'error_details' in metadata and metadata['error_details']:
            print('\nError Details:')
            for i, error in enumerate(metadata['error_details'], 1):
                print(f'  {i}. {error}')
    
    if run.get('error_message'):
        print(f'\nError Message: {run["error_message"]}')
    
    # Check job_scrape_history
    history = supabase.table('job_scrape_history')\
        .select('job_posting_id')\
        .eq('scrape_run_id', run_id)\
        .execute()
    
    print('\n' + '='*80)
    print('JOB SCRAPE HISTORY:')
    print('='*80)
    print(f'Jobs in history: {len(history.data) if history.data else 0}')
    
    # DIAGNOSIS
    print('\n' + '='*80)
    print('DIAGNOSIS:')
    print('='*80)
    
    brightdata_returned = metadata.get('brightdata_jobs_returned', 0)
    jobs_found = run.get('jobs_found', 0)
    
    if brightdata_returned == 0:
        print('❌ Bright Data returned 0 jobs')
        print('   Possible causes:')
        print('   - No jobs match the search criteria on Indeed')
        print('   - Invalid location query')
        print('   - Date range too restrictive')
        print('   - Bright Data API issue')
    elif brightdata_returned > 0 and jobs_found == 0:
        print(f'⚠️  Bright Data returned {brightdata_returned} jobs but 0 were saved')
        print('   Possible causes:')
        print('   - All jobs failed validation')
        print('   - Processing/ingestion errors')
        print('   - Check error_details in metadata')
    else:
        print(f'✅ Normal: {brightdata_returned} jobs returned, {jobs_found} saved')
else:
    print(f'Run {run_id} not found')
