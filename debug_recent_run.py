#!/usr/bin/env python3
"""Debug the most recent completed run."""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Get most recent completed run
result = supabase.table('scrape_runs')\
    .select('*')\
    .eq('status', 'completed')\
    .order('completed_at', desc=True)\
    .limit(1)\
    .execute()

if result.data:
    run = result.data[0]
    run_id = run['id']
    
    print('\n' + '='*80)
    print(f'MOST RECENT COMPLETED RUN')
    print('='*80)
    print(f'Run ID: {run_id}')
    print(f'Query: {run.get("search_query")}')
    print(f'Location: {run.get("location_query")}')
    print(f'Platform: {run.get("platform", "N/A")}')
    print(f'Completed: {run.get("completed_at")}')
    print(f'Jobs Found: {run.get("jobs_found", 0)}')
    print(f'Jobs New: {run.get("jobs_new", 0)}')
    print(f'Jobs Updated: {run.get("jobs_updated", 0)}')
    
    # Check job_scrape_history
    history = supabase.table('job_scrape_history')\
        .select('job_posting_id, detected_at')\
        .eq('scrape_run_id', run_id)\
        .execute()
    
    print('\n' + '='*80)
    print(f'JOB SCRAPE HISTORY')
    print('='*80)
    print(f'Records in history: {len(history.data) if history.data else 0}')
    
    if history.data:
        # Get first 5 job details
        job_ids = [h['job_posting_id'] for h in history.data[:5]]
        
        print('\nFirst 5 jobs:')
        for job_id in job_ids:
            job = supabase.table('job_postings')\
                .select('id, title, created_at, source')\
                .eq('id', job_id)\
                .single()\
                .execute()
            
            if job.data:
                j = job.data
                print(f'  - {j["title"][:50]} (created: {j["created_at"]}, source: {j.get("source", "N/A")})')
    else:
        print('❌ NO JOBS IN HISTORY!')
        print('\nThis means jobs were found but not saved to job_scrape_history.')
        print('Check the ingestion pipeline logs.')
    
    # Check if jobs exist with this run's timestamp
    print('\n' + '='*80)
    print('JOBS CREATED DURING RUN')
    print('='*80)
    
    started = run.get('started_at')
    completed = run.get('completed_at')
    
    if started and completed:
        jobs = supabase.table('job_postings')\
            .select('id, title, created_at, source')\
            .gte('created_at', started)\
            .lte('created_at', completed)\
            .limit(10)\
            .execute()
        
        print(f'Jobs created during run timeframe: {len(jobs.data) if jobs.data else 0}')
        
        if jobs.data:
            print('\nSample jobs:')
            for j in jobs.data[:5]:
                print(f'  - {j["title"][:50]} (source: {j.get("source", "N/A")})')
else:
    print('No completed runs found')
