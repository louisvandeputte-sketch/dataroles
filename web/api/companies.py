"""API endpoints for company master data management."""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from database import db

router = APIRouter()


# Pydantic models for request/response
class CompanyMasterDataCreate(BaseModel):
    company_number: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    revenue_eur: Optional[int] = None
    revenue_range: Optional[str] = None
    profitability: Optional[str] = None
    growth_rate: Optional[float] = None
    growth_trend: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    office_locations: Optional[List[str]] = None
    company_culture: Optional[str] = None
    benefits: Optional[str] = None
    remote_policy: Optional[str] = None
    custom_fields: Optional[dict] = None
    data_source: Optional[str] = "Manual"
    verified: Optional[bool] = False
    notes: Optional[str] = None


class CompanyMasterDataUpdate(BaseModel):
    company_number: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    revenue_eur: Optional[int] = None
    revenue_range: Optional[str] = None
    profitability: Optional[str] = None
    growth_rate: Optional[float] = None
    growth_trend: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    office_locations: Optional[List[str]] = None
    company_culture: Optional[str] = None
    benefits: Optional[str] = None
    remote_policy: Optional[str] = None
    custom_fields: Optional[dict] = None
    data_source: Optional[str] = None
    verified: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/")
async def list_companies(
    search: Optional[str] = None,
    industry: Optional[str] = None,
    employee_min: Optional[int] = None,
    employee_max: Optional[int] = None,
    has_master_data: Optional[bool] = None,
    verified: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """List companies with optional filters."""
    
    try:
        # Build base query with LEFT JOIN to master data
        query = db.client.table("companies").select(
            "id, name, logo_url, company_master_data(*)",
            count="exact"
        )
        
        # Apply search filter
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # Order by name
        query = query.order("name")
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        if not result.data:
            return {"companies": [], "total": 0}
        
        # Process results - just normalize master_data format
        companies = []
        for company in result.data:
            # Convert master_data from list to dict if needed
            master_data = company.get("company_master_data")
            if isinstance(master_data, list):
                company["company_master_data"] = master_data[0] if master_data else None
            
            companies.append(company)
        
        return {
            "companies": companies,
            "total": result.count or 0
        }
    
    except Exception as e:
        print(f"Error in list_companies: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load companies: {str(e)}")


@router.get("/{company_id}")
async def get_company(company_id: str):
    """Get company details with master data."""
    
    # Get company with master data
    company = db.client.table("companies")\
        .select("*, company_master_data(*)")\
        .eq("id", company_id)\
        .single()\
        .execute()
    
    if not company.data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_data = company.data
    
    # Get job count and recent jobs
    jobs = db.client.table("job_postings")\
        .select("id, title, posted_date, is_active")\
        .eq("company_id", company_id)\
        .order("posted_date", desc=True)\
        .limit(10)\
        .execute()
    
    company_data["jobs"] = jobs.data
    company_data["job_count"] = len(jobs.data)
    
    # Handle master_data format (list to dict)
    if company_data.get("company_master_data"):
        if isinstance(company_data["company_master_data"], list):
            company_data["company_master_data"] = company_data["company_master_data"][0] if company_data["company_master_data"] else None
    
    return company_data


@router.post("/{company_id}/master-data")
async def create_master_data(company_id: str, data: CompanyMasterDataCreate):
    """Create master data for a company."""
    
    # Check if company exists
    company = db.client.table("companies")\
        .select("id")\
        .eq("id", company_id)\
        .execute()
    
    if not company.data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if master data already exists
    existing = db.client.table("company_master_data")\
        .select("id")\
        .eq("company_id", company_id)\
        .execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="Master data already exists. Use PUT to update.")
    
    # Create master data
    master_data = data.dict(exclude_none=True)
    master_data["company_id"] = company_id
    
    result = db.client.table("company_master_data")\
        .insert(master_data)\
        .execute()
    
    return result.data[0]


@router.put("/{company_id}/master-data")
async def update_master_data(company_id: str, data: CompanyMasterDataUpdate):
    """Update master data for a company."""
    
    # Check if master data exists
    existing = db.client.table("company_master_data")\
        .select("id")\
        .eq("company_id", company_id)\
        .execute()
    
    if not existing.data:
        raise HTTPException(status_code=404, detail="Master data not found. Use POST to create.")
    
    # Update master data
    update_data = data.dict(exclude_none=True)
    
    # If verified is set to True, update last_verified_at
    if update_data.get("verified") is True:
        from datetime import datetime
        update_data["last_verified_at"] = datetime.utcnow().isoformat()
    
    result = db.client.table("company_master_data")\
        .update(update_data)\
        .eq("company_id", company_id)\
        .execute()
    
    return result.data[0]


@router.delete("/{company_id}/master-data")
async def delete_master_data(company_id: str):
    """Delete master data for a company."""
    
    result = db.client.table("company_master_data")\
        .delete()\
        .eq("company_id", company_id)\
        .execute()
    
    return {"message": "Master data deleted successfully"}


@router.get("/industries/list")
async def list_industries():
    """Get list of unique industries."""
    
    result = db.client.table("company_master_data")\
        .select("industry")\
        .execute()
    
    # Extract unique industries
    industries = list(set(
        item["industry"] 
        for item in result.data 
        if item.get("industry")
    ))
    industries.sort()
    
    return {"industries": industries}
