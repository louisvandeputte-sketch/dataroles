#!/usr/bin/env python3
"""Check status of Bright Data snapshots for stuck runs."""

import asyncio
import os
from dotenv import load_dotenv
from clients import get_client

load_dotenv()

async def check_snapshot(snapshot_id: str, source: str = "linkedin"):
    """Check status of a specific snapshot."""
    print(f'\n{"="*80}')
    print(f'Checking {source.upper()} snapshot: {snapshot_id}')
    print(f'{"="*80}')
    
    try:
        client = get_client(source=source)
        status_data = await client.get_snapshot_status(snapshot_id)
        
        print(f'Status: {status_data.get("status")}')
        print(f'Progress: {status_data.get("progress", 0)}%')
        
        if status_data.get("status") == "ready":
            print('\n✅ Snapshot is READY - should have completed!')
            print('This indicates the orchestrator failed to download results.')
            
            # Try to download
            print('\nAttempting to download results...')
            results = await client.download_results(snapshot_id)
            print(f'✅ Downloaded {len(results)} jobs')
            
            if len(results) > 0:
                print('\nFirst job sample:')
                import json
                print(json.dumps(results[0], indent=2)[:500] + '...')
        
        elif status_data.get("status") == "failed":
            print('\n❌ Snapshot FAILED')
            print(f'Error: {status_data.get("error", "Unknown error")}')
        
        elif status_data.get("status") == "building":
            print('\n⏳ Snapshot still BUILDING')
            print('This is unusual for old snapshots - may indicate API issue')
        
        await client.close()
        
    except Exception as e:
        print(f'\n❌ Error checking snapshot: {e}')
        import traceback
        print(traceback.format_exc())

async def main():
    """Check all stuck run snapshots."""
    
    # We don't have snapshot IDs for the stuck runs yet (they're still running)
    # But we can check the 0-job completed run
    
    print('\n' + '='*80)
    print('CHECKING BRIGHT DATA SNAPSHOTS FOR STUCK/FAILED RUNS')
    print('='*80)
    
    # Check the Data Engineer run that returned 0 jobs
    await check_snapshot('sd_mhzvnpxffzawnlnl8', source='indeed')
    
    print('\n\n' + '='*80)
    print('SUMMARY')
    print('='*80)
    print('If snapshots are READY but not downloaded, the issue is in orchestrator.')
    print('If snapshots are still BUILDING, the issue is with Bright Data API.')
    print('If snapshots FAILED, check Bright Data error messages.')

if __name__ == '__main__':
    asyncio.run(main())
