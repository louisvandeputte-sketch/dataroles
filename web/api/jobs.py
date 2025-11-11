"""API endpoints for job database."""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from loguru import logger

from database import db
from ingestion.job_title_classifier import classify_and_save

router = APIRouter()


class ClassifyJobsRequest(BaseModel):
    job_ids: List[str]


@router.get("/")
async def list_jobs(
    search: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    company_ids: Optional[str] = None,  # Comma-separated company IDs
    location_ids: Optional[str] = None,  # Comma-separated location IDs
    type_ids: Optional[str] = None,  # Comma-separated type IDs
    seniority: Optional[List[str]] = None,  # Can be multiple
    employment: Optional[List[str]] = None,  # Can be multiple
    employment_type: Optional[str] = None,
    posted_date: Optional[str] = None,  # today, week, month, all
    ai_enriched: Optional[str] = None,  # true, false, or None for all
    title_classification: Optional[str] = None,  # Data, NIS, or None for all
    source: Optional[str] = None,  # linkedin, indeed, or None for all
    is_active: Optional[bool] = None,
    run_id: Optional[str] = None,  # Filter by scrape run
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_field: str = "posted_date",  # Field to sort by
    sort_direction: str = "desc",  # asc or desc
    limit: int = 50,
    offset: int = 0
):
    """List jobs with filtering and search."""
    
    # If run_id is provided, filter jobs from that specific scrape run
    job_ids_filter = None
    run_info = None
    if run_id:
        # Get jobs from this run via job_scrape_history
        history = db.client.table("job_scrape_history")\
            .select("job_posting_id")\
            .eq("scrape_run_id", run_id)\
            .execute()
        
        if history.data:
            job_ids_filter = [h["job_posting_id"] for h in history.data]
        else:
            # No jobs yet for this run - return empty list instead of all jobs
            job_ids_filter = []
        
        # Get run info for display
        run = db.client.table("scrape_runs")\
            .select("search_query, location_query")\
            .eq("id", run_id)\
            .execute()
        
        if run.data:
            run_info = run.data[0]
    
    # Parse comma-separated IDs
    company_id_list = company_ids.split(',') if company_ids else None
    location_id_list = location_ids.split(',') if location_ids else None
    type_id_list = type_ids.split(',') if type_ids else None
    
    # Parse AI enrichment filter
    ai_enriched_bool = None
    if ai_enriched == 'true':
        ai_enriched_bool = True
    elif ai_enriched == 'false':
        ai_enriched_bool = False
    
    # Build search query
    jobs, total = db.search_jobs(
        search_query=search,
        location=location,
        company_ids=company_id_list,
        location_ids=location_id_list,
        type_ids=type_id_list,
        seniority=seniority,
        employment=employment,
        posted_date=posted_date,
        ai_enriched=ai_enriched_bool,
        title_classification=title_classification,
        source=source,
        active_only=is_active if is_active is not None else True,
        job_ids=job_ids_filter,
        sort_field=sort_field,
        sort_direction=sort_direction,
        limit=limit,
        offset=offset
    )
    
    # Get stats
    stats = db.get_stats()
    
    response = {
        "jobs": jobs,
        "total": total,  # Use actual count from search_jobs
        "stats": {
            "total_jobs": stats.get("total_jobs", 0),
            "active_jobs": stats.get("active_jobs", 0),
            "inactive_jobs": stats.get("total_jobs", 0) - stats.get("active_jobs", 0)
        }
    }
    
    # Include run info if filtering by run_id
    if run_info:
        response["filter_info"] = {
            "run_id": run_id,
            "search_query": run_info.get("search_query"),
            "location_query": run_info.get("location_query")
        }
    
    return response


@router.get("/{job_id}")
async def get_job_detail(job_id: str):
    """Get detailed information about a specific job."""
    # Get job with all related data including LLM enrichment
    job = db.client.table("job_postings")\
        .select("*, companies(*), locations(*), job_descriptions(*), job_posters(*), llm_enrichment(*)")\
        .eq("id", job_id)\
        .single()\
        .execute()
    
    if not job.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.data


@router.get("/{job_id}/history")
async def get_job_history(job_id: str):
    """Get scrape history for a job."""
    # Query job_scrape_history with correct column name
    history = db.client.table("job_scrape_history")\
        .select("*, scrape_runs(id, search_query, location_query, started_at, status)")\
        .eq("job_posting_id", job_id)\
        .order("detected_at", desc=True)\
        .execute()
    
    return {
        "history": history.data if history.data else []
    }


@router.put("/{job_id}")
async def update_job(job_id: str, job_data: dict):
    """Update job information."""
    # Update job posting
    db.update_job_posting(UUID(job_id), job_data)
    return {"message": "Job updated successfully"}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    # TODO: Implement soft delete
    db.client.table("job_postings")\
        .delete()\
        .eq("id", job_id)\
        .execute()
    
    return {"message": "Job deleted"}


@router.post("/{job_id}/archive")
async def archive_job(job_id: str):
    """Archive a job (mark as inactive)."""
    db.mark_jobs_inactive([UUID(job_id)])
    return {"message": "Job archived"}


@router.post("/bulk/archive")
async def archive_multiple_jobs(job_ids: List[str]):
    """Archive multiple jobs."""
    db.mark_jobs_inactive([UUID(jid) for jid in job_ids])
    return {"message": f"Archived {len(job_ids)} jobs"}


@router.post("/bulk/delete")
async def delete_multiple_jobs(job_ids: List[str]):
    """Delete multiple jobs."""
    for job_id in job_ids:
        db.client.table("job_postings")\
            .delete()\
            .eq("id", job_id)\
            .execute()
    
    return {"message": f"Deleted {len(job_ids)} jobs"}


@router.get("/companies/autocomplete")
async def autocomplete_companies(q: str = Query(..., min_length=2)):
    """Autocomplete company names."""
    result = db.client.table("companies")\
        .select("id, name, logo_url")\
        .ilike("name", f"%{q}%")\
        .limit(10)\
        .execute()
    
    return {"companies": result.data if result.data else []}


@router.get("/locations/autocomplete")
async def autocomplete_locations(q: str = Query(..., min_length=2)):
    """Autocomplete locations."""
    result = db.client.table("locations")\
        .select("id, full_location_string, city, region, country")\
        .ilike("full_location_string", f"%{q}%")\
        .limit(10)\
        .execute()
    
    return {"locations": result.data if result.data else []}


@router.get("/types")
async def get_job_types():
    """Get all job types."""
    result = db.client.table("job_types")\
        .select("id, name, description, color")\
        .eq("is_active", True)\
        .order("name")\
        .execute()
    
    return {"types": result.data if result.data else []}


# LLM Enrichment endpoints

def _enrich_job_background(job_id: str, force: bool = False):
    """Background task for enriching a single job."""
    try:
        from ingestion.llm_enrichment import process_job_enrichment
        logger.info(f"🔄 Background enrichment started for job: {job_id}")
        result = process_job_enrichment(job_id, force=force)
        if result["success"]:
            logger.info(f"✅ Background enrichment complete for job: {job_id}")
        else:
            logger.error(f"❌ Background enrichment failed for job: {job_id} - {result.get('error')}")
    except Exception as e:
        logger.error(f"❌ Background enrichment error for job: {job_id} - {e}")


@router.post("/{job_id}/enrich")
async def enrich_single_job(job_id: str, background_tasks: BackgroundTasks, force: bool = False):
    """Enrich a single job with LLM analysis (runs in background). Use force=True to re-enrich."""
    try:
        # Add to background tasks
        background_tasks.add_task(_enrich_job_background, job_id, force)
        
        return {
            "success": True,
            "message": "Job enrichment started in background",
            "job_id": job_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _enrich_jobs_batch_background(job_ids: List[str]):
    """Background task for batch enriching jobs."""
    try:
        from ingestion.llm_enrichment import batch_enrich_jobs
        logger.info(f"🔄 Background batch enrichment started for {len(job_ids)} jobs")
        stats = batch_enrich_jobs(job_ids)
        logger.info(f"✅ Background batch enrichment complete: {stats['successful']} successful, {stats['failed']} failed")
    except Exception as e:
        logger.error(f"❌ Background batch enrichment error: {e}")


@router.post("/enrich/batch")
async def enrich_batch_jobs(job_ids: List[str], background_tasks: BackgroundTasks):
    """Enrich multiple jobs in batch (runs in background)."""
    try:
        if not job_ids:
            raise HTTPException(status_code=400, detail="No job IDs provided")
        
        # Add to background tasks
        background_tasks.add_task(_enrich_jobs_batch_background, job_ids)
        
        return {
            "success": True,
            "message": f"Batch enrichment started in background for {len(job_ids)} jobs",
            "job_count": len(job_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrich/unenriched")
async def get_unenriched_jobs_list(limit: int = 100):
    """Get list of jobs that need enrichment."""
    from ingestion.llm_enrichment import get_unenriched_jobs
    
    try:
        job_ids = get_unenriched_jobs(limit=limit)
        return {
            "count": len(job_ids),
            "job_ids": job_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrich/stats")
async def get_enrichment_stats():
    """Get enrichment statistics (only for 'Data' classified jobs)."""
    try:
        # Total 'Data' jobs
        total_result = db.client.table("llm_enrichment")\
            .select("id, job_postings!inner(title_classification)", count="exact")\
            .eq("job_postings.title_classification", "Data")\
            .execute()
        total = total_result.count or 0
        
        # Enriched 'Data' jobs
        enriched_result = db.client.table("llm_enrichment")\
            .select("id, job_postings!inner(title_classification)", count="exact")\
            .eq("job_postings.title_classification", "Data")\
            .not_.is_("enrichment_completed_at", "null")\
            .execute()
        enriched = enriched_result.count or 0
        
        # Unenriched 'Data' jobs
        unenriched = total - enriched
        
        return {
            "total": total,
            "enriched": enriched,
            "unenriched": unenriched,
            "percentage_enriched": round((enriched / total * 100) if total > 0 else 0, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify_selected_jobs(request: ClassifyJobsRequest, background_tasks: BackgroundTasks):
    """Classify selected jobs using LLM title check."""
    try:
        if not request.job_ids:
            raise HTTPException(status_code=400, detail="No job IDs provided")
        
        # Get job titles for the selected jobs
        jobs = db.client.table("job_postings")\
            .select("id, title")\
            .in_("id", request.job_ids)\
            .execute()
        
        if not jobs.data:
            raise HTTPException(status_code=404, detail="No jobs found")
        
        # Classify each job in background
        for job in jobs.data:
            background_tasks.add_task(classify_and_save, job["id"], job["title"])
        
        return {
            "message": f"Classification started for {len(jobs.data)} jobs",
            "job_count": len(jobs.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
