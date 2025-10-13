#!/usr/bin/env python3
"""Cleanup all test and dummy data from database."""

from database import db
from loguru import logger

# Delete all runs with test queries
test_queries = ["test", "test dedup", "data engineer", "Data Engineer", "Data Analyst", 
                "Data Scientist", "Machine Learning Engineer"]

logger.info("Cleaning up test data...")

for query in test_queries:
    result = db.client.table("scrape_runs")\
        .delete()\
        .eq("search_query", query)\
        .execute()
    
    if result.data:
        logger.info(f"Deleted {len(result.data)} runs for '{query}'")

# Also delete by location "test"
result = db.client.table("scrape_runs")\
    .delete()\
    .eq("location_query", "test")\
    .execute()

if result.data:
    logger.info(f"Deleted {len(result.data)} runs with location 'test'")

# Delete runs with 0 jobs found (likely mock data)
result = db.client.table("scrape_runs")\
    .select("id, search_query, location_query, jobs_found")\
    .eq("jobs_found", 0)\
    .execute()

logger.info(f"Found {len(result.data)} runs with 0 jobs")
for run in result.data:
    logger.info(f"  - {run['search_query']} in {run['location_query']}")

# Ask for confirmation
if result.data:
    print(f"\nFound {len(result.data)} runs with 0 jobs. Delete them? (y/n): ", end="")
    confirm = input().lower()
    
    if confirm == 'y':
        for run in result.data:
            db.client.table("scrape_runs")\
                .delete()\
                .eq("id", run["id"])\
                .execute()
        logger.success(f"Deleted {len(result.data)} runs with 0 jobs")
    else:
        logger.info("Skipped deletion")

logger.success("Cleanup complete!")
