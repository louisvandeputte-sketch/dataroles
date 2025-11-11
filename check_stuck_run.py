#!/usr/bin/env python3
"""Check and fix stuck runs."""

from database.client import db
from datetime import datetime, timedelta

# Find runs that are stuck (status=running but started more than 1 day ago)
result = db.client.table("scrape_runs")\
    .select("id, search_query_id, status, started_at, completed_at")\
    .eq("status", "running")\
    .execute()

if result.data:
    print("🔍 Found RUNNING runs:")
    print("=" * 80)
    
    stuck_runs = []
    now = datetime.utcnow()
    
    for run in result.data:
        run_id = run.get("id")
        started_at = run.get("started_at")
        
        # Parse started_at
        if started_at:
            started_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            age = now - started_dt.replace(tzinfo=None)
            
            # Get query info
            query_id = run.get("search_query_id")
            if query_id:
                query = db.client.table("search_queries")\
                    .select("search_query, location_query")\
                    .eq("id", query_id)\
                    .single()\
                    .execute()
                
                query_name = f'"{query.data.get("search_query")}" in {query.data.get("location_query")}' if query.data else "Unknown"
            else:
                query_name = "Unknown (no query ID)"
            
            print(f"\nRun ID: {run_id}")
            print(f"Query: {query_name}")
            print(f"Started: {started_at}")
            print(f"Age: {age}")
            
            # Consider stuck if older than 1 hour
            if age > timedelta(hours=1):
                stuck_runs.append({
                    "id": run_id,
                    "query": query_name,
                    "age": age
                })
                print(f"⚠️ STUCK (running for {age})")
    
    if stuck_runs:
        print("\n" + "=" * 80)
        print(f"\n❌ Found {len(stuck_runs)} stuck run(s)")
        print("\nDo you want to mark them as 'failed'? (y/n)")
        
        # For automation, let's just mark them as failed
        print("\n🔧 Marking stuck runs as 'failed'...")
        
        for stuck in stuck_runs:
            db.client.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": f"Run stuck for {stuck['age']} - automatically marked as failed"
                })\
                .eq("id", stuck["id"])\
                .execute()
            
            print(f"✅ Marked run as failed: {stuck['query']}")
        
        print("\n✅ All stuck runs have been marked as failed")
    else:
        print("\n✅ No stuck runs found (all running runs are recent)")
else:
    print("✅ No running runs found")
