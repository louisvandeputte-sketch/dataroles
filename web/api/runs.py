"""API endpoints for scrape runs monitoring."""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger

from database import db

router = APIRouter()


@router.get("/")
async def list_runs(
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List scrape runs with filtering."""
    # Get runs from database - order by created_at desc to show newest first
    runs = db.get_scrape_runs(status=status, limit=limit, offset=offset)
    
    # Convert to list of dicts with proper formatting
    runs_list = []
    for run in runs:
        # Get job type if available
        job_type = None
        if run.get("job_type_id"):
            type_result = db.client.table("job_types")\
                .select("id, name, color")\
                .eq("id", run.get("job_type_id"))\
                .single()\
                .execute()
            if type_result.data:
                job_type = type_result.data
        
        runs_list.append({
            "id": str(run.get("id")),
            "search_query": run.get("search_query"),
            "location_query": run.get("location_query"),
            "status": run.get("status"),
            "trigger_type": run.get("trigger_type", "manual"),
            "job_type": job_type,
            "created_at": run.get("started_at"),  # Use started_at as created_at for frontend
            "started_at": run.get("started_at"),
            "completed_at": run.get("completed_at"),
            "jobs_found": run.get("jobs_found", 0),
            "jobs_new": run.get("jobs_new", 0),
            "jobs_updated": run.get("jobs_updated", 0),
            "archived": run.get("archived", False),
            "metadata": run.get("metadata", {})
        })
    
    # Count active runs
    active_runs = [r for r in runs_list if r.get("status") == "running"]
    
    # Count completed/failed in last 24h
    from datetime import timezone
    day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    
    completed_24h = 0
    failed_24h = 0
    
    for r in runs_list:
        if not r.get("created_at"):
            continue
        try:
            created_at_str = r["created_at"]
            if isinstance(created_at_str, str):
                # Parse datetime and make it timezone-aware
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                if created_at > day_ago:
                    if r.get("status") == "completed":
                        completed_24h += 1
                    elif r.get("status") == "failed":
                        failed_24h += 1
        except (ValueError, TypeError):
            continue
    
    return {
        "runs": runs_list,
        "total": len(runs_list),
        "stats": {
            "active_runs": len(active_runs),
            "completed_24h": completed_24h,
            "failed_24h": failed_24h,
        }
    }


@router.get("/active")
async def get_active_runs():
    """Get currently running LinkedIn scrapes."""
    # Get LinkedIn runs only (filter by platform)
    runs_result = db.client.table("scrape_runs")\
        .select("*")\
        .eq("status", "running")\
        .or_("platform.eq.linkedin_brightdata,platform.is.null")\
        .order("started_at", desc=True)\
        .limit(10)\
        .execute()
    
    runs = runs_result.data if runs_result.data else []
    
    # Format runs
    runs_list = []
    for run in runs:
        # Get job type if available
        job_type = None
        if run.get("job_type_id"):
            type_result = db.client.table("job_types")\
                .select("id, name, color")\
                .eq("id", run.get("job_type_id"))\
                .single()\
                .execute()
            if type_result.data:
                job_type = type_result.data
        
        runs_list.append({
            "id": str(run.get("id")),
            "search_query": run.get("search_query"),
            "location_query": run.get("location_query"),
            "status": run.get("status"),
            "job_type": job_type,
            "created_at": run.get("started_at"),  # Use started_at as created_at for frontend
            "started_at": run.get("started_at"),
            "jobs_found": run.get("jobs_found", 0),
            "jobs_new": run.get("jobs_new", 0),
            "jobs_updated": run.get("jobs_updated", 0),
            "archived": run.get("archived", False),
            "trigger_type": run.get("trigger_type", "manual"),
            "metadata": run.get("metadata", {})
        })
    
    return {"runs": runs_list}


@router.get("/{run_id}")
async def get_run_detail(run_id: str):
    """Get detailed information about a specific run."""
    # Get run from database
    result = db.client.table("scrape_runs")\
        .select("*")\
        .eq("id", run_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = result.data
    
    metadata = run.get("metadata", {})
    return {
        "id": str(run.get("id")),
        "search_query": run.get("search_query"),
        "location_query": run.get("location_query"),
        "status": run.get("status"),
        "started_at": run.get("started_at"),
        "completed_at": run.get("completed_at"),
        "jobs_found": run.get("jobs_found", 0),
        "jobs_new": run.get("jobs_new", 0),
        "jobs_updated": run.get("jobs_updated", 0),
        "jobs_error": metadata.get("jobs_error", 0),
        "error_details": metadata.get("error_details", []),
        "metadata": metadata,
        "jobs_skipped": 0
    }


@router.get("/{run_id}/jobs")
async def get_run_jobs(run_id: str, limit: int = 50, offset: int = 0):
    """Get jobs found in a specific run."""
    # Query jobs by scrape_run_id via job_scrape_history
    # TODO: Implement
    return {
        "jobs": [],
        "total": 0
    }


@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str):
    """Get execution logs for a run."""
    # TODO: Implement log storage and retrieval
    return {
        "logs": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Scrape started"
            }
        ]
    }


@router.post("/{run_id}/stop")
async def stop_run(run_id: str):
    """
    Hard stop a scrape run immediately.
    
    This will mark the run as failed in the database. The Bright Data 
    collection may continue on their side, but we stop tracking it.
    """
    try:
        # Get current run (don't check status - allow stopping any run)
        current = db.client.table("scrape_runs")\
            .select("*")\
            .eq("id", run_id)\
            .execute()
        
        if not current.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        run = current.data[0]
        
        # Check if already stopped
        if run.get("status") in ["completed", "failed"]:
            return {
                "message": f"Run already {run.get('status')}",
                "run_id": run_id
            }
        
        # Hard stop: update status immediately
        result = db.client.table("scrape_runs")\
            .update({
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": "Manually stopped by user (hard stop)"
            })\
            .eq("id", run_id)\
            .execute()
        
        logger.info(f"Run {run_id} hard stopped by user")
        
        return {
            "message": "Scrape stopped successfully",
            "run_id": run_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scrape: {str(e)}")


from pydantic import BaseModel

class ArchiveRequest(BaseModel):
    archived: bool

@router.post("/{run_id}/archive")
async def archive_run(run_id: str, body: ArchiveRequest):
    """Archive or unarchive a scrape run."""
    try:
        # Update the archived status
        result = db.client.table("scrape_runs")\
            .update({"archived": body.archived})\
            .eq("id", run_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        logger.info(f"Run {run_id} {'archived' if body.archived else 'unarchived'}")
        
        return {
            "message": f"Run {'archived' if body.archived else 'unarchived'} successfully",
            "run_id": run_id,
            "archived": body.archived
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive run: {str(e)}")


@router.delete("/{run_id}")
async def delete_run(run_id: str):
    """Delete a scrape run record."""
    # TODO: Implement
    return {"message": "Run deleted"}


@router.post("/cleanup-stuck")
async def cleanup_stuck_linkedin_runs(hours: int = 2):
    """
    Mark stuck running scrapes as failed.
    A scrape is considered stuck if it's been running for more than X hours.
    """
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Find stuck LinkedIn runs
        stuck_runs = db.client.table("scrape_runs")\
            .select("id, search_query, location_query, started_at")\
            .eq("status", "running")\
            .or_("platform.eq.linkedin_brightdata,platform.is.null")\
            .lt("started_at", cutoff_time.isoformat())\
            .execute()
        
        if not stuck_runs.data:
            return {
                "message": "No stuck runs found",
                "cleaned_count": 0
            }
        
        # Mark each as failed
        cleaned_count = 0
        for run in stuck_runs.data:
            try:
                db.client.table("scrape_runs")\
                    .update({
                        "status": "failed",
                        "completed_at": datetime.utcnow().isoformat(),
                        "error_message": f"Run stuck for more than {hours} hours - automatically marked as failed"
                    })\
                    .eq("id", run["id"])\
                    .execute()
                
                cleaned_count += 1
                logger.warning(
                    f"Marked stuck LinkedIn run as failed: {run['id']}\n"
                    f"  Query: {run.get('search_query')}\n"
                    f"  Started: {run.get('started_at')}"
                )
            except Exception as e:
                logger.error(f"Failed to clean up run {run['id']}: {e}")
        
        return {
            "message": f"Cleaned up {cleaned_count} stuck runs",
            "cleaned_count": cleaned_count,
            "runs_cleaned": [r["id"] for r in stuck_runs.data]
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up stuck LinkedIn runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
