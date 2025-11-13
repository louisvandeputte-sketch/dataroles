"""API endpoints for Indeed scrape runs."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from loguru import logger

from database import db

router = APIRouter()


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
            .select("job_posting_id, job_postings(id, title, company_id, location_id, source, companies(name), locations(city, country_code))")\
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


@router.post("/{run_id}/cancel")
async def cancel_indeed_run(run_id: str):
    """Cancel/kill a running Indeed scrape run."""
    try:
        from datetime import datetime
        
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
