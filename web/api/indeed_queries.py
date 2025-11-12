"""API endpoints for Indeed search queries management."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from loguru import logger

from database import db
from scraper import execute_scrape_run
from scheduler.query_scheduler import get_scheduler

router = APIRouter()


class IndeedQueryCreate(BaseModel):
    """Schema for creating a new Indeed query."""
    job_type_id: str
    search_query: str
    location_query: str
    lookback_days: Optional[int] = 7
    is_active: bool = True


class IndeedQueryUpdate(BaseModel):
    """Schema for updating an Indeed query."""
    job_type_id: Optional[str] = None
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
async def list_indeed_queries(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all Indeed search queries with stats."""
    try:
        # Get all Indeed queries from search_queries table
        query_builder = db.client.table("search_queries").select("*").eq("source", "indeed")
        
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
                .eq("search_query_id", query["id"])\
                .order("started_at", desc=True)\
                .limit(1)\
                .execute()
            
            # Count total jobs found
            all_runs = db.client.table("scrape_runs")\
                .select("jobs_found")\
                .eq("search_query_id", query["id"])\
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
        }
        
        return {
            "queries": result,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error listing Indeed queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_indeed_query(query: IndeedQueryCreate):
    """Create a new Indeed search query."""
    try:
        data = {
            **query.dict(),
            "source": "indeed"
        }
        result = db.client.table("search_queries").insert(data).execute()
        return result.data[0]
    except Exception as e:
        logger.error(f"Error creating Indeed query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{query_id}")
async def get_indeed_query(query_id: str):
    """Get a specific Indeed query."""
    try:
        result = db.client.table("search_queries")\
            .select("*")\
            .eq("id", query_id)\
            .eq("source", "indeed")\
            .single()\
            .execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting Indeed query: {e}")
        raise HTTPException(status_code=404, detail="Query not found")


@router.patch("/{query_id}")
async def update_indeed_query(query_id: str, query: IndeedQueryUpdate):
    """Update an Indeed query."""
    try:
        data = query.dict(exclude_none=True)
        result = db.client.table("search_queries")\
            .update(data)\
            .eq("id", query_id)\
            .eq("source", "indeed")\
            .execute()
        return result.data[0]
    except Exception as e:
        logger.error(f"Error updating Indeed query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{query_id}")
async def delete_indeed_query(query_id: str):
    """Delete an Indeed query."""
    try:
        db.client.table("search_queries")\
            .delete()\
            .eq("id", query_id)\
            .eq("source", "indeed")\
            .execute()
        return {"message": "Query deleted"}
    except Exception as e:
        logger.error(f"Error deleting Indeed query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{query_id}/run")
async def run_indeed_query(query_id: str, background_tasks: BackgroundTasks):
    """Trigger a scrape run for an Indeed query."""
    try:
        # Get query details
        query = db.client.table("search_queries")\
            .select("*")\
            .eq("id", query_id)\
            .eq("source", "indeed")\
            .single()\
            .execute()
        
        query_data = query.data
        
        # Run scrape in background
        async def run_scrape():
            await execute_scrape_run(
                query=query_data["search_query"],
                location=query_data["location_query"],
                lookback_days=query_data.get("lookback_days"),
                trigger_type="manual",
                search_query_id=query_id,
                job_type_id=query_data.get("job_type_id"),
                source="indeed"
            )
        
        background_tasks.add_task(run_scrape)
        
        return {"message": "Scrape started", "query_id": query_id}
    except Exception as e:
        logger.error(f"Error running Indeed query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{query_id}/schedule")
async def update_schedule(query_id: str, schedule: ScheduleConfig):
    """Update schedule configuration for an Indeed query."""
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
            .eq("source", "indeed")\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Update scheduler
        scheduler = get_scheduler()
        if schedule.schedule_enabled:
            scheduler.schedule_query(result.data[0])
            logger.info(f"Scheduled Indeed query {query_id}")
        else:
            scheduler.unschedule_query(query_id)
            logger.info(f"Unscheduled Indeed query {query_id}")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update Indeed schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{query_id}/schedule")
async def get_schedule(query_id: str):
    """Get schedule information for an Indeed query."""
    try:
        result = db.client.table("search_queries")\
            .select("schedule_enabled, schedule_type, schedule_time, schedule_interval_hours, schedule_days_of_week")\
            .eq("id", query_id)\
            .eq("source", "indeed")\
            .single()\
            .execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Failed to get Indeed schedule: {e}")
        raise HTTPException(status_code=404, detail="Query not found")
