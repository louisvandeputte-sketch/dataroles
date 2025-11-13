"""Debug the specific run to understand what happened."""

import requests
import json

# Check if the API is returning the error details
run_id = "9394dedf-62ef-40cb-ad26-3c5e9f9c05dc"

# Try to get run details from API
# Replace with your actual Railway URL
api_url = "https://dataroles-production.up.railway.app"  # Update this!

print(f"Checking run: {run_id}\n")
print("=" * 60)

try:
    response = requests.get(f"{api_url}/api/runs/{run_id}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("API RESPONSE:")
        print(json.dumps(data, indent=2))
        print("\n" + "=" * 60)
        
        print("\nKEY METRICS:")
        print(f"  Jobs found: {data.get('jobs_found', 0)}")
        print(f"  Jobs new: {data.get('jobs_new', 0)}")
        print(f"  Jobs updated: {data.get('jobs_updated', 0)}")
        print(f"  Jobs error: {data.get('jobs_error', 'N/A')}")
        
        if data.get('error_details'):
            print(f"\nERROR DETAILS:")
            for i, error in enumerate(data.get('error_details', []), 1):
                print(f"  {i}. {error}")
        
        metadata = data.get('metadata', {})
        if metadata:
            print(f"\nMETADATA:")
            print(f"  Batch summary: {metadata.get('batch_summary', 'N/A')}")
            print(f"  Jobs error: {metadata.get('jobs_error', 'N/A')}")
            print(f"  Snapshot ID: {metadata.get('snapshot_id', 'N/A')}")
            print(f"  Duration: {metadata.get('duration_seconds', 'N/A')}s")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nNote: Update the api_url in this script with your Railway URL")

print("\n" + "=" * 60)
print("\nTo check in database, run:")
print("  psql <connection-string> -f check_run_9394dedf.sql")
print("\nOr execute the SQL queries in Supabase SQL Editor")
