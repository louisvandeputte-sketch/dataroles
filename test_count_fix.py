#!/usr/bin/env python3
"""Test to verify the new/updated count fix."""

import asyncio
from scraper import execute_scrape_run
from database import db
from dateutil import parser

async def test_counts():
    """Run a small scrape and verify counts."""
    
    print("🧪 Testing New/Updated Count Logic")
    print("=" * 80)
    
    # Run a small scrape
    print("\n1. Running scrape: 'powerbi' in 'Belgium'...")
    result = await execute_scrape_run(
        query="powerbi",
        location="Belgium",
        lookback_days=7
    )
    
    print(f"\n2. Scrape completed!")
    print(f"   Status: {result.status}")
    print(f"   Jobs found: {result.jobs_found}")
    print(f"   Jobs new: {result.jobs_new}")
    print(f"   Jobs updated: {result.jobs_updated}")
    
    # Get the run from database
    runs = db.client.table("scrape_runs")\
        .select("*")\
        .eq("search_query", "powerbi")\
        .eq("location_query", "Belgium")\
        .order("started_at", desc=True)\
        .limit(1)\
        .execute()
    
    if not runs.data:
        print("❌ No run found in database!")
        return
    
    run = runs.data[0]
    run_id = run["id"]
    run_start = run["started_at"]
    
    print(f"\n3. Database verification:")
    print(f"   Run ID: {run_id}")
    print(f"   Started: {run_start}")
    
    # Get all jobs from this run
    history = db.client.table("job_scrape_history")\
        .select("job_posting_id")\
        .eq("scrape_run_id", run_id)\
        .execute()
    
    job_ids = [h["job_posting_id"] for h in history.data]
    
    print(f"\n4. Analyzing {len(job_ids)} jobs...")
    
    # Get creation dates
    jobs_info = db.client.table("job_postings")\
        .select("id, created_at")\
        .in_("id", job_ids)\
        .execute()
    
    run_started = parser.parse(run_start)
    
    truly_new = 0
    existed_before = 0
    
    for job in jobs_info.data:
        created = parser.parse(job["created_at"])
        if created >= run_started:
            truly_new += 1
        else:
            existed_before += 1
    
    print(f"\n5. ✅ Actual Breakdown:")
    print(f"   Truly NEW (created during run): {truly_new}")
    print(f"   EXISTED BEFORE (re-seen): {existed_before}")
    print(f"   Total: {truly_new + existed_before}")
    
    print(f"\n6. 📊 Reported in Database:")
    print(f"   jobs_new: {run['jobs_new']}")
    print(f"   jobs_updated: {run['jobs_updated']}")
    print(f"   jobs_found: {run['jobs_found']}")
    
    print(f"\n7. 🔍 Verification:")
    new_match = run["jobs_new"] == truly_new
    updated_match = run["jobs_updated"] == existed_before
    total_match = run["jobs_found"] == (truly_new + existed_before)
    
    print(f"   New count correct: {'✅' if new_match else '❌'} ({run['jobs_new']} == {truly_new})")
    print(f"   Updated count correct: {'✅' if updated_match else '❌'} ({run['jobs_updated']} == {existed_before})")
    print(f"   Total count correct: {'✅' if total_match else '❌'} ({run['jobs_found']} == {truly_new + existed_before})")
    
    if new_match and updated_match and total_match:
        print(f"\n✅ SUCCESS! All counts are correct!")
    else:
        print(f"\n❌ FAILURE! Counts are still incorrect!")
        print(f"\n   Expected: {truly_new} new + {existed_before} updated = {truly_new + existed_before} total")
        print(f"   Got: {run['jobs_new']} new + {run['jobs_updated']} updated = {run['jobs_found']} total")

if __name__ == "__main__":
    asyncio.run(test_counts())
