"""API endpoints for job types management."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from database import db

router = APIRouter()


class JobTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"


class JobTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_job_types(active_only: bool = False):
    """List all job types."""
    query = db.client.table("job_types").select("*")
    
    if active_only:
        query = query.eq("is_active", True)
    
    result = query.order("name").execute()
    
    # Get job counts for each type
    types_with_counts = []
    for job_type in result.data:
        # Count jobs with this type
        count_result = db.client.table("job_type_assignments")\
            .select("id", count="exact")\
            .eq("job_type_id", job_type["id"])\
            .execute()
        
        job_type["job_count"] = count_result.count or 0
        types_with_counts.append(job_type)
    
    return {
        "job_types": types_with_counts,
        "total": len(types_with_counts)
    }


@router.get("/{type_id}")
async def get_job_type(type_id: str):
    """Get a specific job type."""
    result = db.client.table("job_types")\
        .select("*")\
        .eq("id", type_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Job type not found")
    
    return result.data


@router.post("/")
async def create_job_type(job_type: JobTypeCreate):
    """Create a new job type."""
    try:
        result = db.client.table("job_types")\
            .insert({
                "name": job_type.name,
                "description": job_type.description,
                "color": job_type.color,
                "is_active": True
            })\
            .execute()
        
        return result.data[0]
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Job type with this name already exists")
        raise HTTPException(status_code=500, detail=f"Failed to create job type: {str(e)}")


@router.put("/{type_id}")
async def update_job_type(type_id: str, job_type: JobTypeUpdate):
    """Update a job type."""
    update_data = {}
    if job_type.name is not None:
        update_data["name"] = job_type.name
    if job_type.description is not None:
        update_data["description"] = job_type.description
    if job_type.color is not None:
        update_data["color"] = job_type.color
    if job_type.is_active is not None:
        update_data["is_active"] = job_type.is_active
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        result = db.client.table("job_types")\
            .update(update_data)\
            .eq("id", type_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Job type not found")
        
        return result.data[0]
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Job type with this name already exists")
        raise HTTPException(status_code=500, detail=f"Failed to update job type: {str(e)}")


@router.delete("/{type_id}")
async def delete_job_type(type_id: str):
    """Delete a job type (soft delete by setting is_active=false)."""
    # Check if type is used in queries
    queries = db.client.table("search_queries")\
        .select("id", count="exact")\
        .eq("job_type_id", type_id)\
        .execute()
    
    if queries.count and queries.count > 0:
        # Soft delete - set to inactive
        result = db.client.table("job_types")\
            .update({"is_active": False})\
            .eq("id", type_id)\
            .execute()
        
        return {
            "message": "Job type deactivated (used in queries)",
            "deactivated": True
        }
    else:
        # Hard delete - not used anywhere
        result = db.client.table("job_types")\
            .delete()\
            .eq("id", type_id)\
            .execute()
        
        return {
            "message": "Job type deleted",
            "deleted": True
        }


@router.get("/{type_id}/jobs")
async def get_jobs_by_type(type_id: str, limit: int = 50, offset: int = 0):
    """Get all jobs with a specific type."""
    # Get job IDs with this type
    assignments = db.client.table("job_type_assignments")\
        .select("job_posting_id")\
        .eq("job_type_id", type_id)\
        .execute()
    
    if not assignments.data:
        return {"jobs": [], "total": 0}
    
    job_ids = [a["job_posting_id"] for a in assignments.data]
    
    # Get jobs
    jobs, total = db.search_jobs(
        job_ids=job_ids,
        limit=limit,
        offset=offset
    )
    
    return {
        "jobs": jobs,
        "total": total
    }
