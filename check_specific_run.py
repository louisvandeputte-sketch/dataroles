"""Check metadata for specific scrape run."""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

run_id = "3830cbff-3699-47d2-88e4-0ed41ce8b048"

print(f"Checking scrape run: {run_id}\n")

# Get run details
result = supabase.table("scrape_runs")\
    .select("*")\
    .eq("id", run_id)\
    .single()\
    .execute()

if result.data:
    run = result.data
    metadata = run.get("metadata", {})
    
    print("=" * 60)
    print("SCRAPE RUN DETAILS")
    print("=" * 60)
    print(f"Query: {run.get('search_query')}")
    print(f"Location: {run.get('location_query')}")
    print(f"Status: {run.get('status')}")
    print(f"Started: {run.get('started_at')}")
    print(f"Completed: {run.get('completed_at')}")
    print()
    print(f"Jobs found: {run.get('jobs_found', 0)}")
    print(f"Jobs new: {run.get('jobs_new', 0)}")
    print(f"Jobs updated: {run.get('jobs_updated', 0)}")
    print(f"Jobs error: {metadata.get('jobs_error', 'N/A (old run)')}")
    print()
    
    if metadata.get('error_details'):
        print("ERROR DETAILS:")
        for i, error in enumerate(metadata['error_details'], 1):
            print(f"  {i}. {error.get('error', 'Unknown error')}")
    else:
        print("⚠️  No error_details in metadata (this is an old run)")
    
    print()
    print("=" * 60)
    print("METADATA")
    print("=" * 60)
    import json
    print(json.dumps(metadata, indent=2))
    print()
    
    # Check job_scrape_history
    history = supabase.table("job_scrape_history")\
        .select("job_posting_id")\
        .eq("scrape_run_id", run_id)\
        .execute()
    
    print("=" * 60)
    print("JOB SCRAPE HISTORY")
    print("=" * 60)
    print(f"Records in job_scrape_history: {len(history.data) if history.data else 0}")
    
    if history.data:
        print("\nJob IDs:")
        for h in history.data:
            print(f"  - {h['job_posting_id']}")
    else:
        print("❌ No jobs in history (jobs failed to process)")
    
else:
    print("❌ Run not found")
