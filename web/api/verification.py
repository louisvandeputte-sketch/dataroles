"""API endpoints for job verification runs."""

from fastapi import APIRouter, Query
from typing import Optional
from database import db

router = APIRouter(prefix="/api/verification", tags=["verification"])


@router.get("/runs")
async def list_verification_runs(
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List job verification runs with statistics.
    
    Args:
        source: Filter by source ('linkedin' or 'indeed')
        status: Filter by status ('running', 'completed', 'failed')
        limit: Maximum number of runs to return
        offset: Offset for pagination
    """
    query = db.client.table("job_verification_runs")\
        .select("*")\
        .order("started_at", desc=True)
    
    if source:
        query = query.eq("source", source)
    
    if status:
        query = query.eq("status", status)
    
    result = query.range(offset, offset + limit - 1).execute()
    
    return {
        "runs": result.data or [],
        "count": len(result.data) if result.data else 0
    }


@router.get("/runs/{run_id}")
async def get_verification_run(run_id: str):
    """
    Get details of a specific verification run including inactive jobs.
    
    Args:
        run_id: UUID of the verification run
    """
    # Get run details
    run_result = db.client.table("job_verification_runs")\
        .select("*")\
        .eq("id", run_id)\
        .single()\
        .execute()
    
    if not run_result.data:
        return {"error": "Run not found"}, 404
    
    # Get inactive jobs for this run
    inactive_jobs_result = db.client.table("job_verification_inactive_jobs")\
        .select("*")\
        .eq("verification_run_id", run_id)\
        .order("marked_at", desc=True)\
        .execute()
    
    return {
        "run": run_result.data,
        "inactive_jobs": inactive_jobs_result.data or []
    }


@router.get("/stats")
async def get_verification_stats(days: int = 7):
    """
    Get verification statistics for the last N days.
    
    Args:
        days: Number of days to look back
    """
    from datetime import datetime, timedelta
    
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Get runs in time period
    runs_result = db.client.table("job_verification_runs")\
        .select("*")\
        .gte("started_at", since)\
        .execute()
    
    runs = runs_result.data or []
    
    # Calculate stats
    stats = {
        "total_runs": len(runs),
        "linkedin_runs": len([r for r in runs if r["source"] == "linkedin"]),
        "indeed_runs": len([r for r in runs if r["source"] == "indeed"]),
        "completed_runs": len([r for r in runs if r["status"] == "completed"]),
        "failed_runs": len([r for r in runs if r["status"] == "failed"]),
        "total_jobs_checked": sum(r.get("jobs_checked", 0) for r in runs),
        "total_jobs_marked_inactive": sum(r.get("jobs_marked_inactive", 0) for r in runs),
        "total_jobs_still_active": sum(r.get("jobs_still_active", 0) for r in runs),
        "total_errors": sum(r.get("jobs_errors", 0) for r in runs)
    }
    
    # Get recent runs
    recent_runs = sorted(runs, key=lambda r: r["started_at"], reverse=True)[:10]
    
    return {
        "stats": stats,
        "recent_runs": recent_runs,
        "period_days": days
    }


@router.get("/inactive-jobs/recent")
async def get_recent_inactive_jobs(limit: int = 100):
    """
    Get recently marked inactive jobs across all runs.
    
    Args:
        limit: Maximum number of jobs to return
    """
    result = db.client.table("job_verification_inactive_jobs")\
        .select("*, job_verification_runs(started_at, source, trigger_type)")\
        .order("marked_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return {
        "inactive_jobs": result.data or [],
        "count": len(result.data) if result.data else 0
    }
