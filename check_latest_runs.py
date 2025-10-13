#!/usr/bin/env python3
"""Check latest scrape runs and their data."""

from database import db

# Get latest runs
runs = db.get_scrape_runs(limit=5)
print('Latest scrape runs:')
print('=' * 80)

for run in runs:
    print(f"\n{run['search_query']} in {run['location_query']}")
    print(f"  Status: {run['status']}")
    print(f"  Jobs found: {run['jobs_found']}")
    print(f"  Jobs new: {run['jobs_new']}")
    print(f"  Jobs updated: {run['jobs_updated']}")
    
    metadata = run.get('metadata', {})
    if metadata:
        print(f"  Snapshot ID: {metadata.get('snapshot_id', 'N/A')}")
        print(f"  Batch summary: {metadata.get('batch_summary', 'N/A')}")

# Check if we're using mock or real Bright Data
print('\n' + '=' * 80)
print('\nChecking Bright Data client type:')

import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('BRIGHTDATA_API_KEY')
if api_key and api_key != 'your_api_key_here':
    print(f"✅ Real API key configured: {api_key[:10]}...")
else:
    print("⚠️  Using MOCK Bright Data client (no real API key)")
    print("   This means scrapes return dummy data, not real LinkedIn jobs")

# Check jobs in database
print('\n' + '=' * 80)
print('\nJobs in database:')
result = db.client.table('job_postings').select('id, title, companies(name), locations(city)').limit(10).execute()
print(f"Total: {len(result.data)} jobs")

for job in result.data[:5]:
    company_name = job.get('companies', {}).get('name', 'Unknown') if job.get('companies') else 'Unknown'
    city = job.get('locations', {}).get('city', 'Unknown') if job.get('locations') else 'Unknown'
    print(f"  - {job['title']} at {company_name} in {city}")
