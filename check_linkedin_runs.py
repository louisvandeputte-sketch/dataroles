#!/usr/bin/env python3
"""Check if LinkedIn scraper runs are executing"""

from database.client import db
from datetime import datetime, timedelta

print("\n🔍 Checking LinkedIn Scraper Runs...\n")

# Check recent runs (last 24 hours)
yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()

print("="*80)
print("📊 Recent Scrape Runs (Last 24 Hours)")
print("="*80)

runs = db.client.table("scrape_runs")\
    .select("*")\
    .gte("started_at", yesterday)\
    .order("started_at", desc=True)\
    .execute()

if not runs.data:
    print("❌ NO RUNS FOUND in last 24 hours!")
else:
    print(f"✅ Found {len(runs.data)} runs\n")
    
    linkedin_runs = [r for r in runs.data if r.get('source') == 'linkedin' or r.get('source') is None]
    indeed_runs = [r for r in runs.data if r.get('source') == 'indeed']
    
    print(f"LinkedIn runs: {len(linkedin_runs)}")
    print(f"Indeed runs: {len(indeed_runs)}\n")
    
    print("Recent runs breakdown:")
    for run in runs.data[:10]:
        source = run.get('source', 'linkedin')  # Default to linkedin for backward compat
        status = run.get('status', 'unknown')
        query = run.get('search_query', 'N/A')
        location = run.get('location_query', 'N/A')
        started = run.get('started_at', 'N/A')
        jobs_found = run.get('jobs_found', 0)
        
        print(f"  {source.upper():8} | {status:10} | {query:20} | {location:15} | Jobs: {jobs_found:3} | {started}")

print("\n" + "="*80)
print("🔍 Checking Scheduled LinkedIn Queries")
print("="*80)

queries = db.client.table("search_queries")\
    .select("*")\
    .eq("is_active", True)\
    .eq("schedule_enabled", True)\
    .execute()

if not queries.data:
    print("❌ NO SCHEDULED QUERIES FOUND!")
else:
    linkedin_queries = [q for q in queries.data if q.get('source') == 'linkedin' or q.get('source') is None]
    indeed_queries = [q for q in queries.data if q.get('source') == 'indeed']
    
    print(f"✅ Found {len(queries.data)} scheduled queries")
    print(f"   LinkedIn: {len(linkedin_queries)}")
    print(f"   Indeed: {len(indeed_queries)}\n")
    
    print("Scheduled LinkedIn queries:")
    for query in linkedin_queries[:10]:
        search_query = query.get('search_query', 'N/A')
        location = query.get('location_query', 'N/A')
        schedule_type = query.get('schedule_type', 'N/A')
        last_run = query.get('last_run_at', 'Never')
        next_run = query.get('next_run_at', 'Not scheduled')
        
        print(f"  {search_query:25} | {location:15} | {schedule_type:10} | Last: {last_run} | Next: {next_run}")

print("\n" + "="*80)
print("🔍 Checking All Search Queries (Active)")
print("="*80)

all_queries = db.client.table("search_queries")\
    .select("*")\
    .eq("is_active", True)\
    .execute()

if all_queries.data:
    linkedin_all = [q for q in all_queries.data if q.get('source') == 'linkedin' or q.get('source') is None]
    indeed_all = [q for q in all_queries.data if q.get('source') == 'indeed']
    
    print(f"Total active queries: {len(all_queries.data)}")
    print(f"  LinkedIn: {len(linkedin_all)}")
    print(f"  Indeed: {len(indeed_all)}")
    print(f"  Scheduled: {len(queries.data)}")
    print(f"  Not scheduled: {len(all_queries.data) - len(queries.data)}")

print("\n" + "="*80)
print("🎯 DIAGNOSIS")
print("="*80)

if len(linkedin_runs) == 0 and len(indeed_runs) > 0:
    print("❌ PROBLEM FOUND: Only Indeed runs are executing!")
    print("   LinkedIn scraper is NOT running.")
    print("\n   Possible causes:")
    print("   1. LinkedIn queries not scheduled (schedule_enabled = false)")
    print("   2. Scheduler not loading LinkedIn queries")
    print("   3. Source filter excluding LinkedIn queries")
    print("   4. LinkedIn scraper disabled in config")
elif len(linkedin_runs) == 0 and len(indeed_runs) == 0:
    print("❌ PROBLEM FOUND: NO scraper runs at all!")
    print("   Neither LinkedIn nor Indeed scrapers are running.")
    print("\n   Possible causes:")
    print("   1. Scheduler not running")
    print("   2. No queries scheduled")
    print("   3. Background services disabled")
elif len(linkedin_runs) > 0:
    print("✅ LinkedIn scraper IS running")
    print(f"   Found {len(linkedin_runs)} LinkedIn runs in last 24 hours")
else:
    print("⚠️ Unclear status - check logs")

print("\n" + "="*80)
