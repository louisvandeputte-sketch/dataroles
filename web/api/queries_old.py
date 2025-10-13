"""API endpoints for search queries management."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger

from database import db
from scraper import execute_scrape_run

router = APIRouter()


class QueryCreate(BaseModel):
    """Schema for creating a new query."""
    search_query: str
    location_query: str
    lookback_days: Optional[int] = 7
    tags: Optional[List[str]] = []
    is_active: bool = True


class QueryUpdate(BaseModel):
    """Schema for updating a query."""
    search_query: Optional[str] = None
    location_query: Optional[str] = None
    lookback_days: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_queries(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all search queries with stats."""
    # Since we don't have a search_queries table yet, 
    # we'll aggregate from scrape_runs to show stats
    
    # Get unique query+location combinations from scrape_runs
    all_runs = db.get_scrape_runs(limit=1000)
    
    # Group by query+location
    queries_dict = {}
    for run in all_runs:
        key = f"{run.get('search_query')}|{run.get('location_query')}"
        if key not in queries_dict:
            queries_dict[key] = {
                "id": key,
                "search_query": run.get("search_query"),
                "location_query": run.get("location_query"),
                "status": "active",  # Assume all are active
                "last_run": run.get("completed_at") or run.get("started_at"),
                "total_jobs": 0,
                "run_count": 0
            }
        
        # Aggregate stats
        queries_dict[key]["total_jobs"] += run.get("jobs_found", 0)
        queries_dict[key]["run_count"] += 1
    
    queries_list = list(queries_dict.values())
    
    # Calculate stats
    total_jobs = sum(q["total_jobs"] for q in queries_list)
    running_now = len([r for r in all_runs if r.get("status") == "running"])
    
    return {
        "queries": queries_list[:limit],
        "total": len(queries_list),
        "stats": {
            "total_queries": len(queries_list),
            "active_queries": len(queries_list),  # All are active for now
            "total_jobs_found": total_jobs,
            "running_now": running_now
        }
    }


@router.post("/")
async def create_query(query: QueryCreate):
    """Create a new search query."""
    # For now, we don't persist queries to a separate table
    # Just return the query data that was submitted
    logger.info(f"Query created: {query.search_query} in {query.location_query}")
    return {
        "id": "temp-id",
        "message": "Query created successfully",
        "query": query.dict()
    }


@router.get("/{query_id}")
async def get_query(query_id: str):
    """Get a specific query by ID."""
    # TODO: Implement
    return {"id": query_id}


@router.put("/{query_id}")
async def update_query(query_id: str, query: QueryUpdate):
    """Update a search query."""
    # TODO: Implement
    return {"id": query_id, "message": "Query updated"}


@router.delete("/{query_id}")
async def delete_query(query_id: str):
    """Delete a search query."""
    # TODO: Implement
    return {"message": "Query deleted"}


@router.post("/{query_id}/run")
async def run_query(query_id: str):
    """Trigger a scrape run for this query."""
    # TODO: Get query from database when we have search_queries table
    raise HTTPException(status_code=404, detail="Query not found")


@router.post("/bulk/run")
async def run_multiple_queries(query_ids: List[str], background_tasks: BackgroundTasks):
    """Run multiple queries."""
    try:
        # Query IDs are in format "search_query|location_query"
        started_count = 0
        
        for query_id in query_ids:
            parts = query_id.split("|")
            if len(parts) != 2:
                logger.warning(f"Invalid query ID format: {query_id}")
                continue
            
            search_query, location_query = parts
            
            # Start scrape in background
            background_tasks.add_task(
                execute_scrape_run,
                query=search_query,
                location=location_query,
                lookback_days=7
            )
            started_count += 1
            logger.info(f"Started scrape for '{search_query}' in '{location_query}'")
        
        return {"message": f"Started {started_count} scrapes"}
    except Exception as e:
        logger.error(f"Failed to run queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run queries: {str(e)}")


@router.post("/bulk/pause")
async def pause_multiple_queries(query_ids: List[str]):
    """Pause multiple queries (not implemented - no search_queries table yet)."""
    # TODO: Implement when we have a proper search_queries table
    # For now, we can't pause queries since they're derived from scrape_runs
    logger.warning(f"Pause not implemented - no search_queries table")
    return {"message": "Pause feature not yet implemented"}


@router.post("/bulk/delete")
async def delete_multiple_queries(query_ids: List[str]):
    """Delete multiple queries (actually deletes all scrape runs for these query combinations)."""
    try:
        # Query IDs are in format "search_query|location_query"
        # We need to delete all scrape_runs matching these combinations
        deleted_count = 0
        
        for query_id in query_ids:
            parts = query_id.split("|")
            if len(parts) != 2:
                logger.warning(f"Invalid query ID format: {query_id}")
                continue
            
            search_query, location_query = parts
            
            # Delete all scrape runs for this query+location combination
            result = db.client.table("scrape_runs")\
                .delete()\
                .eq("search_query", search_query)\
                .eq("location_query", location_query)\
                .execute()
            
            if result.data:
                deleted_count += len(result.data)
                logger.info(f"Deleted {len(result.data)} scrape runs for '{search_query}' in '{location_query}'")
        
        return {"message": f"Deleted {deleted_count} scrape runs"}
    except Exception as e:
        logger.error(f"Failed to delete queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete queries: {str(e)}")


@router.post("/run-now")
async def run_query_now(query: QueryCreate, background_tasks: BackgroundTasks):
    """
    Create and immediately run a scrape for the given query.
    This runs the scrape in the background and returns immediately.
    """
    logger.info(f"Starting immediate scrape: '{query.search_query}' in '{query.location_query}'")
    
    try:
        # Start the scrape in the background
        background_tasks.add_task(
            execute_scrape_run,
            query=query.search_query,  # Note: parameter is 'query' not 'search_query'
            location=query.location_query,  # Note: parameter is 'location' not 'location_query'
            lookback_days=query.lookback_days or 7
        )
        
        return {
            "message": "Scrape started successfully",
            "query": {
                "search_query": query.search_query,
                "location_query": query.location_query,
                "lookback_days": query.lookback_days or 7
            },
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Failed to start scrape: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scrape: {str(e)}")
