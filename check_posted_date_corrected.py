#!/usr/bin/env python3
"""Check why posted_date_corrected is NULL"""

from database.client import db

problem_job_ids = [
    "7ec45673-ce07-4898-b1c8-fbc3383684f6",
    "bc38bc96-a4d7-4b0e-90c3-4fd065ff0009",
]

print("\n🔍 Checking posted_date_corrected for problem jobs...\n")

for job_id in problem_job_ids:
    # Get job from view
    view_result = db.client.table("job_ranking_view")\
        .select("id, title, posted_date, posted_date_corrected")\
        .eq("id", job_id)\
        .execute()
    
    if view_result.data:
        job = view_result.data[0]
        print(f"Job: {job['title'][:50]}")
        print(f"   posted_date: {job.get('posted_date')}")
        print(f"   posted_date_corrected: {job.get('posted_date_corrected')}")
        
        # Check job_sources for first_seen_at
        sources = db.client.table("job_sources")\
            .select("job_posting_id, first_seen_at, source")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        print(f"   job_sources entries: {len(sources.data)}")
        if sources.data:
            for src in sources.data:
                print(f"      - {src['source']}: first_seen_at = {src.get('first_seen_at')}")
        else:
            print(f"      ❌ NO job_sources entries!")
        
        print()
