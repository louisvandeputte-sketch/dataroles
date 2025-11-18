"""API endpoints for Indeed scrape runs."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel

from database import db

router = APIRouter()


class ArchiveRequest(BaseModel):
    archived: bool


@router.get("/")
async def list_indeed_runs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all Indeed scrape runs."""
    try:
        # Get runs with Indeed platform
        query_builder = db.client.table("scrape_runs")\
            .select("*, search_queries(search_query, location_query, job_type_id)")\
            .eq("platform", "indeed_brightdata")
        
        if status:
            query_builder = query_builder.eq("status", status)
        
        runs = query_builder.order("started_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Get stats
        stats_query = db.client.table("scrape_runs")\
            .select("status, jobs_found, jobs_new, jobs_updated")\
            .eq("platform", "indeed_brightdata")\
            .execute()
        
        stats = {
            "total_runs": len(stats_query.data),
            "completed": sum(1 for r in stats_query.data if r.get("status") == "completed"),
            "failed": sum(1 for r in stats_query.data if r.get("status") == "failed"),
            "running": sum(1 for r in stats_query.data if r.get("status") == "running"),
            "total_jobs_found": sum(r.get("jobs_found", 0) for r in stats_query.data),
            "total_jobs_new": sum(r.get("jobs_new", 0) for r in stats_query.data),
            "total_jobs_updated": sum(r.get("jobs_updated", 0) for r in stats_query.data),
        }
        
        return {
            "runs": runs.data,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error listing Indeed runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_indeed_runs():
    """Get currently running Indeed scrapes."""
    try:
        runs = db.client.table("scrape_runs")\
            .select("*, search_queries(search_query, location_query, job_type_id)")\
            .eq("platform", "indeed_brightdata")\
            .eq("status", "running")\
            .order("started_at", desc=True)\
            .limit(10)\
            .execute()
        
        return {
            "runs": runs.data,
            "count": len(runs.data)
        }
    except Exception as e:
        logger.error(f"Error getting active Indeed runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}")
async def get_indeed_run(run_id: str):
    """Get details of a specific Indeed run."""
    try:
        result = db.client.table("scrape_runs")\
            .select("*, search_queries(search_query, location_query, job_type_id)")\
            .eq("id", run_id)\
            .eq("platform", "indeed_brightdata")\
            .single()\
            .execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting Indeed run: {e}")
        raise HTTPException(status_code=404, detail="Run not found")


@router.get("/{run_id}/jobs")
async def get_indeed_run_jobs(run_id: str, limit: int = 100, offset: int = 0):
    """Get jobs from a specific Indeed run."""
    try:
        # Get jobs via scrape_history
        result = db.client.table("scrape_history")\
            .select("job_posting_id, job_postings(id, title, company_id, location_id, source, companies(name), locations!job_postings_location_id_fkey(city, country_code))")\
            .eq("scrape_run_id", run_id)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Filter to only Indeed jobs
        jobs = [
            {
                **item["job_postings"],
                "scrape_run_id": run_id
            }
            for item in result.data
            if item.get("job_postings") and item["job_postings"].get("source") == "indeed"
        ]
        
        return {
            "jobs": jobs,
            "total": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting Indeed run jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/archive")
async def archive_indeed_run(run_id: str, body: ArchiveRequest):
    """Archive or unarchive an Indeed scrape run."""
    try:
        # Update the archived status
        result = db.client.table("scrape_runs")\
            .update({"archived": body.archived})\
            .eq("id", run_id)\
            .eq("platform", "indeed_brightdata")\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        logger.info(f"Indeed run {run_id} {'archived' if body.archived else 'unarchived'}")
        
        return {
            "message": f"Run {'archived' if body.archived else 'unarchived'} successfully",
            "run_id": run_id,
            "archived": body.archived
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive Indeed run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive run: {str(e)}")


@router.post("/{run_id}/stop")
async def stop_indeed_run(run_id: str):
    """
    Hard stop an Indeed scrape run immediately.
    
    This will mark the run as failed in the database. The Bright Data 
    collection may continue on their side, but we stop tracking it.
    """
    try:
        # Get current run (don't check status - allow stopping any run)
        current = db.client.table("scrape_runs")\
            .select("*")\
            .eq("id", run_id)\
            .eq("platform", "indeed_brightdata")\
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
        
        logger.info(f"Indeed run {run_id} hard stopped by user")
        
        return {
            "message": "Scrape stopped successfully",
            "run_id": run_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop Indeed run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scrape: {str(e)}")


@router.post("/{run_id}/cancel")
async def cancel_indeed_run(run_id: str):
    """Cancel/kill a running Indeed scrape run."""
    try:
        # Check if run exists and is cancellable
        run = db.client.table("scrape_runs")\
            .select("id, status")\
            .eq("id", run_id)\
            .eq("platform", "indeed_brightdata")\
            .single()\
            .execute()
        
        if not run.data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        current_status = run.data.get("status")
        if current_status not in ["pending", "running"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel run with status '{current_status}'. Only pending or running runs can be cancelled."
            )
        
        # Update run to failed status with cancellation metadata
        result = db.client.table("scrape_runs")\
            .update({
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "metadata": db.client.rpc(
                    "jsonb_set",
                    {
                        "target": db.client.table("scrape_runs").select("metadata").eq("id", run_id).single().execute().data.get("metadata", {}),
                        "path": ["cancelled_manually"],
                        "new_value": True
                    }
                ) if False else {  # Simplified - just overwrite
                    "cancelled_manually": True,
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "previous_status": current_status
                }
            })\
            .eq("id", run_id)\
            .execute()
        
        logger.info(f"Cancelled Indeed run {run_id} (was {current_status})")
        
        return {
            "success": True,
            "message": f"Run cancelled successfully",
            "run_id": run_id,
            "previous_status": current_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling Indeed run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-stuck")
async def cleanup_stuck_indeed_runs(hours: int = 2):
    """
    Mark stuck running scrapes as failed.
    A scrape is considered stuck if it's been running for more than X hours.
    """
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Find stuck runs
        stuck_runs = db.client.table("scrape_runs")\
            .select("id, search_query, location_query, started_at")\
            .eq("platform", "indeed_brightdata")\
            .eq("status", "running")\
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
                    f"Marked stuck Indeed run as failed: {run['id']}\n"
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
        logger.error(f"Error cleaning up stuck Indeed runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
