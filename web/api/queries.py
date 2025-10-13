"""API endpoints for search queries management with scheduling support."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime, time
from loguru import logger

from database import db
from scraper import execute_scrape_run
from scheduler import get_scheduler

router = APIRouter()


class QueryCreate(BaseModel):
    """Schema for creating a new query."""
    job_type_id: str
    search_query: str
    location_query: str
    lookback_days: Optional[int] = 7
    is_active: bool = True


class QueryUpdate(BaseModel):
    """Schema for updating a query."""
    search_query: Optional[str] = None
    location_query: Optional[str] = None
    lookback_days: Optional[int] = None
    is_active: Optional[bool] = None


class ScheduleConfig(BaseModel):
    """Schema for schedule configuration."""
    schedule_enabled: bool
    schedule_type: Optional[str] = None  # 'daily', 'interval', 'weekly'
    schedule_time: Optional[str] = None  # HH:MM for daily/weekly
    schedule_interval_hours: Optional[int] = None  # For interval type
    schedule_days_of_week: Optional[List[int]] = None  # For weekly (0=Sun, 6=Sat)


@router.get("/")
async def list_queries(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all search queries with stats."""
    try:
        # Get all queries from search_queries table
        query_builder = db.client.table("search_queries").select("*")
        
        if status == "active":
            query_builder = query_builder.eq("is_active", True)
        elif status == "inactive":
            query_builder = query_builder.eq("is_active", False)
        
        queries = query_builder.order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Get stats for each query
        result = []
        for query in queries.data:
            # Get latest run
            latest_run = db.client.table("scrape_runs")\
                .select("*")\
                .eq("search_query", query["search_query"])\
                .eq("location_query", query["location_query"])\
                .order("started_at", desc=True)\
                .limit(1)\
                .execute()
            
            # Count total jobs found
            all_runs = db.client.table("scrape_runs")\
                .select("jobs_found")\
                .eq("search_query", query["search_query"])\
                .eq("location_query", query["location_query"])\
                .execute()
            
            total_jobs = sum(r.get("jobs_found", 0) for r in all_runs.data)
            
            result.append({
                **query,
                "last_run": latest_run.data[0] if latest_run.data else None,
                "total_jobs": total_jobs,
                "run_count": len(all_runs.data)
            })
        
        # Get overall stats
        stats = {
            "total_queries": len(queries.data),
            "active_queries": sum(1 for q in queries.data if q.get("is_active")),
            "scheduled_queries": sum(1 for q in queries.data if q.get("schedule_enabled")),
        }
        
        return {
            "queries": result,
            "stats": stats,
            "total": len(queries.data)
        }
    except Exception as e:
        logger.error(f"Failed to list queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_query(query: QueryCreate):
    """Create a new search query."""
    try:
        # Verify job type exists
        type_check = db.client.table("job_types")\
            .select("id")\
            .eq("id", query.job_type_id)\
            .eq("is_active", True)\
            .execute()
        
        if not type_check.data:
            raise HTTPException(status_code=400, detail="Invalid or inactive job type")
        
        # Insert into search_queries table
        result = db.client.table("search_queries")\
            .insert({
                "job_type_id": query.job_type_id,
                "search_query": query.search_query,
                "location_query": query.location_query,
                "lookback_days": query.lookback_days,
                "is_active": query.is_active
            })\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create query")
        
        logger.info(f"Created query: '{query.search_query}' in '{query.location_query}' (type: {query.job_type_id})")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create query: {e}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Query with this search term and location already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{query_id}")
async def get_query(query_id: str):
    """Get a specific query by ID."""
    try:
        query = db.client.table("search_queries")\
            .select("*")\
            .eq("id", query_id)\
            .single()\
            .execute()
        
        if not query.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        return query.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{query_id}")
async def update_query(query_id: str, query: QueryUpdate):
    """Update a search query."""
    try:
        # Build update dict
        update_data = {k: v for k, v in query.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = db.client.table("search_queries")\
            .update(update_data)\
            .eq("id", query_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        logger.info(f"Updated query {query_id}")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{query_id}")
async def delete_query(query_id: str):
    """Delete a search query."""
    try:
        # Unschedule if scheduled
        scheduler = get_scheduler()
        scheduler.unschedule_query(query_id)
        
        # Delete query
        result = db.client.table("search_queries")\
            .delete()\
            .eq("id", query_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        logger.info(f"Deleted query {query_id}")
        return {"message": "Query deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{query_id}/run")
async def run_query(query_id: str, background_tasks: BackgroundTasks):
    """Trigger a scrape run for this query."""
    try:
        # Get query from database
        query = db.client.table("search_queries")\
            .select("*")\
            .eq("id", query_id)\
            .single()\
            .execute()
        
        if not query.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        q = query.data
        
        # Start scrape in background
        background_tasks.add_task(
            execute_scrape_run,
            query=q["search_query"],
            location=q["location_query"],
            lookback_days=q.get("lookback_days", 7),
            trigger_type="manual",
            search_query_id=query_id,
            job_type_id=q.get("job_type_id")
        )
        
        logger.info(f"Started manual scrape for query {query_id}")
        return {"message": "Scrape started", "query_id": query_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{query_id}/schedule")
async def update_schedule(query_id: str, schedule: ScheduleConfig):
    """Update schedule configuration for a query."""
    try:
        # Validate schedule config
        if schedule.schedule_enabled:
            if not schedule.schedule_type:
                raise HTTPException(status_code=400, detail="schedule_type required when enabled")
            
            if schedule.schedule_type == "daily" and not schedule.schedule_time:
                raise HTTPException(status_code=400, detail="schedule_time required for daily schedule")
            
            if schedule.schedule_type == "interval" and not schedule.schedule_interval_hours:
                raise HTTPException(status_code=400, detail="schedule_interval_hours required for interval schedule")
            
            if schedule.schedule_type == "weekly":
                if not schedule.schedule_time or not schedule.schedule_days_of_week:
                    raise HTTPException(status_code=400, detail="schedule_time and schedule_days_of_week required for weekly schedule")
        
        # Update database
        update_data = schedule.model_dump()
        result = db.client.table("search_queries")\
            .update(update_data)\
            .eq("id", query_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Update scheduler
        scheduler = get_scheduler()
        if schedule.schedule_enabled:
            scheduler.schedule_query(result.data[0])
            logger.info(f"Scheduled query {query_id}")
        else:
            scheduler.unschedule_query(query_id)
            logger.info(f"Unscheduled query {query_id}")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{query_id}/schedule")
async def get_schedule(query_id: str):
    """Get schedule information for a query."""
    try:
        query = db.client.table("search_queries")\
            .select("schedule_enabled, schedule_type, schedule_time, schedule_interval_hours, schedule_days_of_week, next_run_at, last_run_at")\
            .eq("id", query_id)\
            .single()\
            .execute()
        
        if not query.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Get scheduler info
        scheduler = get_scheduler()
        job_info = scheduler.get_job_info(query_id)
        
        return {
            **query.data,
            "scheduler_info": job_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/run")
async def run_multiple_queries(query_ids: List[str], background_tasks: BackgroundTasks):
    """Run multiple queries."""
    try:
        # Get queries from database
        queries = db.client.table("search_queries")\
            .select("*")\
            .in_("id", query_ids)\
            .execute()
        
        if not queries.data:
            raise HTTPException(status_code=404, detail="No queries found")
        
        # Start scrapes in background
        for query in queries.data:
            background_tasks.add_task(
                execute_scrape_run,
                query=query["search_query"],
                location=query["location_query"],
                lookback_days=query.get("lookback_days", 7),
                trigger_type="manual",
                search_query_id=query["id"]
            )
        
        logger.info(f"Started {len(queries.data)} scrapes")
        return {"message": f"Started {len(queries.data)} scrapes"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/delete")
async def delete_multiple_queries(query_ids: List[str]):
    """Delete multiple queries."""
    try:
        # Unschedule all
        scheduler = get_scheduler()
        for query_id in query_ids:
            scheduler.unschedule_query(query_id)
        
        # Delete queries
        result = db.client.table("search_queries")\
            .delete()\
            .in_("id", query_ids)\
            .execute()
        
        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Deleted {deleted_count} queries")
        
        return {"message": f"Deleted {deleted_count} queries"}
    except Exception as e:
        logger.error(f"Failed to delete queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            query=query.search_query,
            location=query.location_query,
            lookback_days=query.lookback_days,
            trigger_type="manual"
        )
        
        return {
            "message": "Scrape started",
            "query": query.search_query,
            "location": query.location_query
        }
    except Exception as e:
        logger.error(f"Failed to start scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))
