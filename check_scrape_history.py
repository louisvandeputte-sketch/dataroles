#!/usr/bin/env python3
"""Check scrape history for Indeed jobs."""

from database.client import db

print("Checking Scrape History")
print("=" * 80)

# Get Indeed jobs
indeed_jobs = db.client.table("job_postings")\
    .select("id, title, created_at")\
    .eq("source", "indeed")\
    .order("created_at", desc=True)\
    .limit(10)\
    .execute()

print(f"\nFound {len(indeed_jobs.data)} Indeed jobs")

for job in indeed_jobs.data:
    # Check scrape history
    history = db.client.table("job_scrape_history")\
        .select("scrape_run_id")\
        .eq("job_posting_id", job['id'])\
        .execute()
    
    print(f"\n  Job: {job['title'][:50]}")
    print(f"    Created: {job['created_at']}")
    print(f"    History entries: {len(history.data)}")
    
    if history.data:
        for h in history.data:
            print(f"      - Run ID: {h['scrape_run_id']}")

# Check total history count
print(f"\n" + "=" * 80)
total_history = db.client.table("job_scrape_history")\
    .select("*", count="exact")\
    .execute()

print(f"Total scrape history entries: {total_history.count}")

# Check Indeed scrape runs
indeed_runs = db.client.table("scrape_runs")\
    .select("id, search_query, status, jobs_found, jobs_new")\
    .eq("platform", "indeed_brightdata")\
    .order("started_at", desc=True)\
    .execute()

print(f"\nIndeed scrape runs: {len(indeed_runs.data)}")
for run in indeed_runs.data:
    print(f"  {run['search_query']:20} | Status: {run['status']:10} | Found: {run['jobs_found']:3} | New: {run['jobs_new']:3}")
