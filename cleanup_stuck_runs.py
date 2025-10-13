#!/usr/bin/env python3
"""Cleanup stuck runs that are marked as 'running' but are actually completed or failed."""

from database import db
from loguru import logger

# Get all runs with status 'running'
result = db.client.table("scrape_runs")\
    .select("id, search_query, location_query, started_at, completed_at")\
    .eq("status", "running")\
    .execute()

stuck_runs = result.data

logger.info(f"Found {len(stuck_runs)} runs with status 'running'")

for run in stuck_runs:
    run_id = run['id']
    query = run['search_query']
    location = run['location_query']
    
    # If completed_at is set, mark as completed
    if run.get('completed_at'):
        logger.info(f"Marking as completed: {query} in {location}")
        db.client.table("scrape_runs")\
            .update({"status": "completed"})\
            .eq("id", run_id)\
            .execute()
    # If started_at is None, it's a test run - mark as failed
    elif run.get('started_at') is None:
        logger.info(f"Marking test run as failed: {query} in {location}")
        db.client.table("scrape_runs")\
            .update({"status": "failed"})\
            .eq("id", run_id)\
            .execute()
    # If query is "test" or "test dedup", mark as failed (old test data)
    elif query in ["test", "test dedup"]:
        logger.info(f"Marking old test run as failed: {query} in {location}")
        db.client.table("scrape_runs")\
            .update({"status": "failed"})\
            .eq("id", run_id)\
            .execute()
    else:
        logger.warning(f"Run still running: {query} in {location}")

logger.success("Cleanup complete!")
