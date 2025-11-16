#!/usr/bin/env python3
"""Clean up stuck scrape runs."""

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

# Find stuck runs (running for more than 30 minutes)
cutoff_time = (datetime.utcnow() - timedelta(minutes=30)).isoformat()

result = supabase.table('scrape_runs')\
    .select('id, search_query, location_query, platform, started_at')\
    .eq('status', 'running')\
    .lt('started_at', cutoff_time)\
    .execute()

print('\n' + '='*80)
print(f'STUCK RUNS FOUND: {len(result.data)}')
print('='*80 + '\n')

if not result.data:
    print('✅ No stuck runs found')
    exit(0)

for run in result.data:
    print(f'Run ID: {run["id"]}')
    print(f'Platform: {run.get("platform", "N/A")}')
    print(f'Query: {run.get("search_query", "N/A")}')
    print(f'Location: {run.get("location_query", "N/A")}')
    print(f'Started: {run["started_at"]}')
    
    started = datetime.fromisoformat(run['started_at'].replace('Z', '+00:00'))
    duration = datetime.utcnow() - started.replace(tzinfo=None)
    print(f'Duration: {duration} ({duration.total_seconds()/60:.1f} minutes)')
    print('-'*80)

print('\n' + '='*80)
print('CLEANING UP STUCK RUNS')
print('='*80 + '\n')

cleaned_count = 0
for run in result.data:
    try:
        supabase.table('scrape_runs')\
            .update({
                'status': 'failed',
                'completed_at': datetime.utcnow().isoformat(),
                'error_message': 'Run stuck for more than 30 minutes - automatically marked as failed'
            })\
            .eq('id', run['id'])\
            .execute()
        
        cleaned_count += 1
        print(f'✅ Cleaned up run: {run["id"]} ({run.get("search_query")} in {run.get("location_query")})')
    except Exception as e:
        print(f'❌ Failed to clean up run {run["id"]}: {e}')

print('\n' + '='*80)
print(f'SUMMARY: Cleaned up {cleaned_count}/{len(result.data)} stuck runs')
print('='*80)
