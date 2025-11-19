"""
Stuck Run Cleaner
=================

Detects and marks stuck scrape runs as failed.
A run is considered stuck if it's been running for more than 1 hour.
"""

from datetime import datetime, timedelta
from loguru import logger
from database.client import db


def clean_stuck_runs() -> int:
    """
    Find and mark stuck runs as failed.
    
    Returns:
        Number of runs marked as failed
    """
    logger.info("🔍 Checking for stuck scrape runs...")
    
    # Find runs that are stuck (status=running but started more than 1 hour ago)
    result = db.client.table("scrape_runs")\
        .select("id, search_query_id, status, started_at, completed_at")\
        .eq("status", "running")\
        .execute()
    
    if not result.data:
        logger.info("✅ No running runs found")
        return 0
    
    stuck_runs = []
    now = datetime.utcnow()
    
    for run in result.data:
        run_id = run.get("id")
        started_at = run.get("started_at")
        
        if not started_at:
            continue
        
        # Parse started_at
        started_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        age = now - started_dt.replace(tzinfo=None)
        
        # Consider stuck if older than 1 hour
        if age > timedelta(hours=1):
            # Get query info for logging
            query_name = "Unknown"
            query_id = run.get("search_query_id")
            if query_id:
                try:
                    query = db.client.table("search_queries")\
                        .select("search_query, location_query")\
                        .eq("id", query_id)\
                        .single()\
                        .execute()
                    
                    if query.data:
                        query_name = f'"{query.data.get("search_query")}" in {query.data.get("location_query")}'
                except Exception as e:
                    logger.warning(f"Could not fetch query info: {e}")
            
            stuck_runs.append({
                "id": run_id,
                "query": query_name,
                "age": age
            })
            logger.warning(f"⚠️ Found stuck run: {query_name} (running for {age})")
    
    if not stuck_runs:
        logger.info(f"✅ All {len(result.data)} running run(s) are recent (< 1 hour)")
        return 0
    
    # Mark stuck runs as failed
    logger.info(f"🔧 Marking {len(stuck_runs)} stuck run(s) as failed...")
    
    for stuck in stuck_runs:
        try:
            db.client.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": f"Run stuck for {stuck['age']} - automatically marked as failed"
                })\
                .eq("id", stuck["id"])\
                .execute()
            
            logger.info(f"✅ Marked as failed: {stuck['query']}")
        except Exception as e:
            logger.error(f"❌ Failed to mark run {stuck['id']} as failed: {e}")
    
    logger.info(f"✅ Cleaned up {len(stuck_runs)} stuck run(s)")
    return len(stuck_runs)


if __name__ == "__main__":
    # For manual testing
    count = clean_stuck_runs()
    print(f"\n{'='*80}")
    print(f"Cleaned up {count} stuck run(s)")
    print(f"{'='*80}")
