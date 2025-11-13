"""Analyze the actual error from the Indeed run."""

import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

run_id = "5bd808d2-b450-438c-9bd3-40478667f1bd"

print(f"Analyzing Indeed run: {run_id}\n")
print("=" * 70)

# Get run details
result = supabase.table("scrape_runs")\
    .select("*")\
    .eq("id", run_id)\
    .single()\
    .execute()

if not result.data:
    print("❌ Run not found")
    exit(1)

run = result.data
metadata = run.get("metadata", {})

print("\n📊 RUN SUMMARY:")
print(f"   Query: {run.get('search_query')}")
print(f"   Location: {run.get('location_query')}")
print(f"   Source: {metadata.get('source', 'unknown')}")
print(f"   Status: {run.get('status')}")
print(f"   Duration: {metadata.get('duration_seconds', 0):.1f}s")

print("\n📈 RESULTS:")
print(f"   Jobs found: {run.get('jobs_found', 0)}")
print(f"   Jobs new: {run.get('jobs_new', 0)}")
print(f"   Jobs updated: {run.get('jobs_updated', 0)}")
print(f"   Jobs error: {metadata.get('jobs_error', 0)}")

print("\n" + "=" * 70)

if metadata.get('jobs_error', 0) > 0:
    print("\n❌ ERROR DETAILS:")
    error_details = metadata.get('error_details', [])
    
    if error_details:
        for i, error in enumerate(error_details, 1):
            error_msg = error.get('error', 'Unknown error')
            print(f"\n   Error #{i}:")
            print(f"   {error_msg}")
            
            # Parse the error to identify the issue
            if "Field" in error_msg and ":" in error_msg:
                parts = error_msg.split(":", 1)
                field_part = parts[0].replace("Field", "").strip().strip("'")
                issue = parts[1].strip()
                
                print(f"\n   🔍 Analysis:")
                print(f"      Field: {field_part}")
                print(f"      Issue: {issue}")
                
                if "field required" in issue.lower():
                    print(f"\n   💡 Solution:")
                    print(f"      Make '{field_part}' optional in models/indeed.py")
                    print(f"      Change: {field_part}: str")
                    print(f"      To:     {field_part}: Optional[str] = None")
    else:
        print("   (No error details available - this was before the fix)")
else:
    print("\n✅ No errors reported")

print("\n" + "=" * 70)

# Check if any jobs were actually created
history = supabase.table("job_scrape_history")\
    .select("job_posting_id")\
    .eq("scrape_run_id", run_id)\
    .execute()

jobs_in_history = len(history.data) if history.data else 0

print(f"\n📝 JOB SCRAPE HISTORY:")
print(f"   Records: {jobs_in_history}")

if jobs_in_history == 0 and run.get('jobs_found', 0) > 0:
    print(f"\n⚠️  DISCREPANCY CONFIRMED:")
    print(f"   Bright Data found {run.get('jobs_found', 0)} job(s)")
    print(f"   But {jobs_in_history} jobs were successfully processed")
    print(f"   This means ALL jobs failed during validation/processing")

print("\n" + "=" * 70)
print("\n🔧 NEXT STEPS:")
print("   1. Check the error details above")
print("   2. Fix the validation issue in models/indeed.py")
print("   3. Deploy the fix")
print("   4. Trigger a new test run")
