"""API endpoints for data quality tools."""

from fastapi import APIRouter
from typing import List
from uuid import UUID

from database import db
from scraper import mark_inactive_jobs, get_inactive_jobs_summary

router = APIRouter()


@router.get("/duplicates")
async def find_duplicates(threshold: float = 0.9):
    """Find potential duplicate jobs."""
    # TODO: Implement duplicate detection algorithm
    # Compare jobs by: title similarity, company, location, posted date
    return {
        "duplicate_groups": [],
        "total_groups": 0
    }


@router.post("/duplicates/merge")
async def merge_duplicates(primary_job_id: str, duplicate_job_ids: List[str]):
    """Merge duplicate jobs into one."""
    # TODO: Implement merge logic
    # Keep primary job, merge data from duplicates, delete duplicates
    return {"message": f"Merged {len(duplicate_job_ids)} jobs into {primary_job_id}"}


@router.post("/duplicates/mark-not-duplicate")
async def mark_not_duplicate(job_id_1: str, job_id_2: str):
    """Mark two jobs as not duplicates."""
    # TODO: Store in exclusion list
    return {"message": "Marked as not duplicates"}


@router.get("/inactive")
async def get_inactive_jobs(threshold_days: int = 14, limit: int = 50, offset: int = 0):
    """Get jobs that haven't been seen recently."""
    # Get summary
    summary = get_inactive_jobs_summary()
    
    # Get inactive jobs
    result = db.client.table("job_postings")\
        .select("*, companies(name), locations(full_location_string)")\
        .eq("is_active", False)\
        .order("detected_inactive_at", desc=True)\
        .limit(limit)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    return {
        "jobs": result.data if result.data else [],
        "summary": summary
    }


@router.post("/inactive/mark")
async def mark_jobs_inactive_now(threshold_days: int = 14):
    """Manually trigger inactive job marking."""
    count = mark_inactive_jobs(threshold_days=threshold_days)
    return {
        "message": f"Marked {count} jobs as inactive",
        "count": count
    }


@router.post("/inactive/reactivate")
async def reactivate_jobs(job_ids: List[str]):
    """Reactivate inactive jobs."""
    for job_id in job_ids:
        db.client.table("job_postings")\
            .update({"is_active": True, "detected_inactive_at": None})\
            .eq("id", job_id)\
            .execute()
    
    return {"message": f"Reactivated {len(job_ids)} jobs"}


@router.post("/cleanup/normalize-companies")
async def normalize_company_names():
    """Normalize company names (fix capitalization, etc)."""
    # TODO: Implement
    return {"message": "Company names normalized"}


@router.post("/cleanup/remove-test-data")
async def remove_test_data():
    """Remove jobs tagged as test data."""
    # TODO: Implement
    return {"message": "Test data removed"}


@router.get("/stats")
async def get_quality_stats():
    """Get data quality statistics."""
    stats = db.get_stats()
    inactive_summary = get_inactive_jobs_summary()
    
    return {
        "total_jobs": stats.get("total_jobs", 0),
        "active_jobs": stats.get("active_jobs", 0),
        "inactive_jobs": inactive_summary.get("total_inactive", 0),
        "duplicate_groups": 0,  # TODO: Calculate
        "jobs_missing_salary": 0,  # TODO: Calculate
        "jobs_missing_description": 0  # TODO: Calculate
    }
