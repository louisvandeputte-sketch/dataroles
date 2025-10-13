#!/usr/bin/env python3
"""Monitor active scrape runs in real-time."""

import asyncio
import sys
from datetime import datetime
from database import db

async def monitor_scrapes():
    """Monitor active scrapes and show progress."""
    
    print("🔍 Monitoring Active Scrapes...")
    print("=" * 80)
    
    last_job_count = {}
    
    while True:
        try:
            # Get active runs
            runs = db.get_scrape_runs(status="running", limit=10)
            
            if not runs:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] No active scrapes", end="", flush=True)
            else:
                # Clear screen
                print("\033[2J\033[H", end="")
                
                print(f"🔍 Active Scrapes - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 80)
                
                for run in runs:
                    run_id = run['id']
                    query = run['search_query']
                    location = run['location_query']
                    jobs_found = run.get('jobs_found', 0)
                    
                    # Calculate jobs/sec
                    if run_id in last_job_count:
                        jobs_per_sec = (jobs_found - last_job_count[run_id]) / 2
                    else:
                        jobs_per_sec = 0
                    
                    last_job_count[run_id] = jobs_found
                    
                    # Get jobs in history
                    history = db.client.table("job_scrape_history")\
                        .select("id", count="exact")\
                        .eq("scrape_run_id", run_id)\
                        .execute()
                    
                    jobs_saved = history.count or 0
                    
                    print(f"\n📊 {query} in {location}")
                    print(f"   Run ID: {run_id[:8]}...")
                    print(f"   Jobs Found: {jobs_found}")
                    print(f"   Jobs Saved: {jobs_saved}")
                    print(f"   Speed: {jobs_per_sec:.1f} jobs/sec")
                    
                    # Progress bar
                    if jobs_found > 0:
                        progress = min(100, int((jobs_saved / jobs_found) * 100))
                        bar_length = 40
                        filled = int(bar_length * progress / 100)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        print(f"   Progress: [{bar}] {progress}%")
                
                print("\n" + "=" * 80)
                print("Press Ctrl+C to stop monitoring")
            
            # Wait 2 seconds
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(monitor_scrapes())
