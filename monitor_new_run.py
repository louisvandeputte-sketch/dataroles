"""Monitor a new scrape run to verify error tracking works."""

import os
import time
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("🔍 Monitoring for new scrape runs...")
print("Start your manual run now!\n")

# Get the most recent run before we start
initial_runs = supabase.table("scrape_runs")\
    .select("id, started_at")\
    .order("started_at", desc=True)\
    .limit(1)\
    .execute()

initial_run_id = initial_runs.data[0]["id"] if initial_runs.data else None
print(f"Latest run before monitoring: {initial_run_id}\n")

# Poll for new runs
print("Waiting for new run to start...")
new_run = None
attempts = 0
max_attempts = 60  # 5 minutes

while not new_run and attempts < max_attempts:
    time.sleep(5)
    attempts += 1
    
    recent_runs = supabase.table("scrape_runs")\
        .select("*")\
        .order("started_at", desc=True)\
        .limit(1)\
        .execute()
    
    if recent_runs.data:
        latest_run = recent_runs.data[0]
        if latest_run["id"] != initial_run_id:
            new_run = latest_run
            print(f"\n✅ New run detected: {new_run['id']}")
            print(f"   Query: {new_run['search_query']}")
            print(f"   Location: {new_run['location_query']}")
            print(f"   Status: {new_run['status']}\n")
            break
    
    if attempts % 6 == 0:  # Every 30 seconds
        print(f"   Still waiting... ({attempts * 5}s)")

if not new_run:
    print("\n❌ No new run detected after 5 minutes")
    exit(1)

# Monitor the run until completion
print("📊 Monitoring run progress...\n")
run_id = new_run["id"]

while True:
    time.sleep(10)
    
    run = supabase.table("scrape_runs")\
        .select("*")\
        .eq("id", run_id)\
        .single()\
        .execute()
    
    if not run.data:
        print("❌ Run not found")
        break
    
    run_data = run.data
    status = run_data["status"]
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status}")
    
    if status in ["completed", "failed"]:
        print("\n" + "=" * 60)
        print("RUN COMPLETED")
        print("=" * 60)
        
        metadata = run_data.get("metadata", {})
        
        print(f"\n📊 RESULTS:")
        print(f"   Status: {status}")
        print(f"   Jobs found: {run_data.get('jobs_found', 0)}")
        print(f"   Jobs new: {run_data.get('jobs_new', 0)}")
        print(f"   Jobs updated: {run_data.get('jobs_updated', 0)}")
        print(f"   Jobs error: {metadata.get('jobs_error', 0)}")
        
        if metadata.get('jobs_error', 0) > 0:
            print(f"\n❌ ERROR DETAILS:")
            error_details = metadata.get('error_details', [])
            if error_details:
                for i, error in enumerate(error_details, 1):
                    print(f"   {i}. {error.get('error', 'Unknown error')}")
            else:
                print("   (No error details available)")
        
        # Check job_scrape_history
        history = supabase.table("job_scrape_history")\
            .select("job_posting_id")\
            .eq("scrape_run_id", run_id)\
            .execute()
        
        jobs_in_history = len(history.data) if history.data else 0
        
        print(f"\n📝 JOB SCRAPE HISTORY:")
        print(f"   Records: {jobs_in_history}")
        
        # Verification
        jobs_found = run_data.get('jobs_found', 0)
        jobs_processed = run_data.get('jobs_new', 0) + run_data.get('jobs_updated', 0)
        jobs_error = metadata.get('jobs_error', 0)
        
        print(f"\n✅ VERIFICATION:")
        print(f"   Jobs found: {jobs_found}")
        print(f"   Jobs processed: {jobs_processed}")
        print(f"   Jobs error: {jobs_error}")
        print(f"   Jobs in history: {jobs_in_history}")
        
        expected_in_history = jobs_processed
        if jobs_in_history == expected_in_history:
            print(f"\n✅ SUCCESS! History count matches processed count ({jobs_in_history})")
        else:
            print(f"\n⚠️  WARNING: History count ({jobs_in_history}) != processed count ({expected_in_history})")
        
        if jobs_found == jobs_processed + jobs_error:
            print(f"✅ SUCCESS! Found = Processed + Error ({jobs_found} = {jobs_processed} + {jobs_error})")
        else:
            print(f"⚠️  WARNING: Found ({jobs_found}) != Processed + Error ({jobs_processed + jobs_error})")
        
        break
    
    elif status == "running":
        # Show progress if available
        if run_data.get('jobs_found'):
            print(f"   Jobs found so far: {run_data.get('jobs_found', 0)}")

print("\n" + "=" * 60)
print(f"Run ID: {run_id}")
print(f"View in UI: https://your-app.railway.app/runs")
print("=" * 60)
