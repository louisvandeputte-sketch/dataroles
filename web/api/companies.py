"""API endpoints for company master data management."""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from typing import Optional, List
from pydantic import BaseModel
import csv
import io
from loguru import logger

from database import db

router = APIRouter()

# Allowed image types for logo upload
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# Pydantic models for request/response
class CompanyMasterDataCreate(BaseModel):
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    jobs_page_url: Optional[str] = None
    contact_email: Optional[str] = None
    # AI enrichment fields
    bedrijfswebsite: Optional[str] = None
    jobspagina: Optional[str] = None
    email_hr: Optional[str] = None
    email_hr_bron: Optional[str] = None
    email_algemeen: Optional[str] = None
    bedrijfsomschrijving: Optional[str] = None


class CompanyMasterDataUpdate(BaseModel):
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    jobs_page_url: Optional[str] = None
    contact_email: Optional[str] = None
    # AI enrichment fields
    bedrijfswebsite: Optional[str] = None
    jobspagina: Optional[str] = None
    email_hr: Optional[str] = None
    email_hr_bron: Optional[str] = None
    email_algemeen: Optional[str] = None
    bedrijfsomschrijving: Optional[str] = None


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
        # Only select essential fields to reduce response size
        query = db.client.table("companies").select(
            "id, name, logo_url, industry, company_master_data(hiring_model, is_consulting)",
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
    
    print(f"[DEBUG] PUT request for company_id: {company_id}")
    print(f"[DEBUG] Received data type: {type(data)}")
    print(f"[DEBUG] Data dict: {data.dict()}")
    print(f"[DEBUG] Data dict (exclude_none): {data.dict(exclude_none=True)}")
    
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
    
    print(f"[DEBUG] Sending to database: {update_data}")
    
    result = db.client.table("company_master_data")\
        .update(update_data)\
        .eq("company_id", company_id)\
        .execute()
    
    print(f"[DEBUG] Update successful")
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


@router.get("/export/csv")
async def export_companies_csv(
    search: Optional[str] = None,
    industry: Optional[str] = None,
    verified: Optional[bool] = None
):
    """Export companies with master data to CSV."""
    
    try:
        # Build query to get all companies (no pagination for export)
        query = db.client.table("companies").select(
            "id, linkedin_company_id, name, logo_url, company_master_data(*)"
        )
        
        # Apply search filter
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # Order by name
        query = query.order("name")
        
        result = query.execute()
        
        if not result.data:
            # Return empty CSV with headers
            companies = []
        else:
            companies = result.data
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'LinkedIn Company ID',
            'Company Name',
            'Industry',
            'Founded Year',
            'Website',
            'Jobs Page URL',
            'Contact Email',
            'Bedrijfswebsite (AI)',
            'Jobspagina (AI)',
            'Email HR (AI)',
            'Email HR Bron (AI)',
            'Email Algemeen (AI)',
            'Bedrijfsomschrijving (AI)',
            'AI Enriched'
        ])
        
        # Write data rows
        for company in companies:
            master_data = company.get("company_master_data")
            
            # Handle master_data format (could be list or dict)
            if isinstance(master_data, list):
                master_data = master_data[0] if master_data else None
            
            # Extract fields
            linkedin_company_id = company.get("linkedin_company_id", "")
            company_name = company.get("name", "")
            industry = master_data.get("industry", "") if master_data else ""
            founded_year = master_data.get("founded_year", "") if master_data else ""
            website = master_data.get("website", "") if master_data else ""
            jobs_page_url = master_data.get("jobs_page_url", "") if master_data else ""
            contact_email = master_data.get("contact_email", "") if master_data else ""
            bedrijfswebsite = master_data.get("bedrijfswebsite", "") if master_data else ""
            jobspagina = master_data.get("jobspagina", "") if master_data else ""
            email_hr = master_data.get("email_hr", "") if master_data else ""
            email_hr_bron = master_data.get("email_hr_bron", "") if master_data else ""
            email_algemeen = master_data.get("email_algemeen", "") if master_data else ""
            bedrijfsomschrijving = master_data.get("bedrijfsomschrijving", "") if master_data else ""
            ai_enriched = "Yes" if (master_data and master_data.get("ai_enriched")) else "No"
            
            writer.writerow([
                linkedin_company_id,
                company_name,
                industry,
                founded_year,
                website,
                jobs_page_url,
                contact_email,
                bedrijfswebsite,
                jobspagina,
                email_hr,
                email_hr_bron,
                email_algemeen,
                bedrijfsomschrijving,
                ai_enriched
            ])
        
        # Prepare response
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=companies_export.csv"
            }
        )
    
    except Exception as e:
        print(f"Error in export_companies_csv: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export companies: {str(e)}")


@router.post("/import/csv")
async def import_companies_csv(file: UploadFile = File(...)):
    """Import companies master data from CSV file. Matches companies by LinkedIn Company ID (first column)."""
    
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read file content
        content = await file.read()
        
        # Try different encodings
        content_str = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                content_str = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content_str is None:
            raise HTTPException(status_code=400, detail="Unable to decode CSV file. Please ensure it's a valid CSV.")
        
        # Detect delimiter (comma or semicolon)
        sniffer = csv.Sniffer()
        try:
            # Sample first 1024 bytes to detect delimiter
            sample = content_str[:1024]
            dialect = sniffer.sniff(sample, delimiters=',;\t')
            delimiter = dialect.delimiter
        except csv.Error:
            # Default to comma if detection fails
            delimiter = ','
        
        # Parse CSV with detected delimiter
        csv_reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
        
        # Read header
        try:
            headers = next(csv_reader)
            headers = [h.strip() for h in headers]
        except StopIteration:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Validate that first column is LinkedIn Company ID (be flexible with naming)
        first_header_lower = headers[0].lower().strip() if headers else ''
        if not first_header_lower or ('linkedin' not in first_header_lower and 'company' not in first_header_lower and 'id' not in first_header_lower):
            # Check if it looks like a valid header at all
            if not first_header_lower or len(first_header_lower) < 3:
                raise HTTPException(
                    status_code=400, 
                    detail=f"First column must be 'LinkedIn Company ID'. Found: '{headers[0] if headers else 'empty'}'. Make sure your CSV has proper headers."
                )
        
        # Map headers to indices (case-insensitive)
        header_map = {}
        for idx, header in enumerate(headers):
            header_lower = header.lower().strip()
            if 'linkedin' in header_lower and 'company' in header_lower and 'id' in header_lower:
                header_map['linkedin_company_id'] = idx
            elif 'company' in header_lower and 'name' in header_lower:
                header_map['company_name'] = idx
            elif 'industry' in header_lower:
                header_map['industry'] = idx
            elif 'founded' in header_lower and 'year' in header_lower:
                header_map['founded_year'] = idx
            elif 'website' in header_lower:
                header_map['website'] = idx
            elif 'jobs' in header_lower and 'page' in header_lower:
                header_map['jobs_page_url'] = idx
            elif 'contact' in header_lower and 'email' in header_lower:
                header_map['contact_email'] = idx
        
        stats = {
            'total_rows': 0,
            'skipped_rows': 0,
            'companies_found': 0,
            'companies_not_found': 0,
            'master_data_created': 0,
            'master_data_updated': 0,
            'errors': []
        }
        
        # Process each row
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            stats['total_rows'] += 1
            
            try:
                # Get LinkedIn Company ID from first column
                if not row or len(row) == 0:
                    stats['skipped_rows'] += 1
                    continue
                
                linkedin_company_id = row[0].strip() if row[0] else ''
                
                # Skip empty rows or rows without LinkedIn Company ID
                if not linkedin_company_id:
                    stats['skipped_rows'] += 1
                    continue
                
                # Convert to string and remove any decimal points (Excel formatting issue)
                linkedin_company_id = str(linkedin_company_id).split('.')[0]
                
                # Find company by linkedin_company_id
                result = db.client.table("companies")\
                    .select("id, name")\
                    .eq("linkedin_company_id", linkedin_company_id)\
                    .execute()
                
                if not result.data:
                    stats['companies_not_found'] += 1
                    # Get company name from row for better error message
                    company_name = row[header_map.get('company_name', 1)] if 'company_name' in header_map and len(row) > header_map.get('company_name', 1) else 'Unknown'
                    stats['errors'].append({
                        'row': row_num,
                        'linkedin_id': linkedin_company_id,
                        'company_name': company_name,
                        'error': 'Company not found in database'
                    })
                    continue
                
                company = result.data[0]
                stats['companies_found'] += 1
                company_id = company['id']
                
                # Helper function to safely get value from row
                def get_value(key):
                    if key not in header_map:
                        return None
                    idx = header_map[key]
                    if idx >= len(row):
                        return None
                    value = row[idx].strip() if row[idx] else ''
                    return value if value else None
                
                # Prepare master data - only include fields that have values
                master_data = {}
                
                # String fields
                if get_value('industry'):
                    master_data['industry'] = get_value('industry')
                if get_value('website'):
                    master_data['website'] = get_value('website')
                if get_value('jobs_page_url'):
                    master_data['jobs_page_url'] = get_value('jobs_page_url')
                if get_value('contact_email'):
                    master_data['contact_email'] = get_value('contact_email')
                
                # Parse founded year
                founded_year_str = get_value('founded_year')
                if founded_year_str:
                    try:
                        # Remove any non-digit characters
                        clean_str = ''.join(c for c in founded_year_str if c.isdigit())
                        if clean_str:
                            master_data['founded_year'] = int(clean_str)
                    except ValueError:
                        pass
                
                # Skip if no data to import
                if not master_data:
                    stats['skipped_rows'] += 1
                    continue
                
                # Check if master data exists
                existing = db.client.table("company_master_data")\
                    .select("id")\
                    .eq("company_id", company_id)\
                    .execute()
                
                if existing.data:
                    # Update existing master data
                    db.client.table("company_master_data")\
                        .update(master_data)\
                        .eq("company_id", company_id)\
                        .execute()
                    stats['master_data_updated'] += 1
                else:
                    # Create new master data
                    master_data['company_id'] = company_id
                    db.client.table("company_master_data")\
                        .insert(master_data)\
                        .execute()
                    stats['master_data_created'] += 1
                    
            except Exception as e:
                stats['errors'].append({
                    'row': row_num,
                    'linkedin_id': row[0] if row else 'Unknown',
                    'error': str(e)
                })
        
        return {
            'success': True,
            'message': f"Import completed: {stats['master_data_created']} created, {stats['master_data_updated']} updated",
            'stats': stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in import_companies_csv: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to import companies: {str(e)}")


# ==================== LOGO UPLOAD ====================

@router.post("/{company_id}/logo")
async def upload_company_logo(company_id: str, file: UploadFile = File(...)):
    """Upload a logo for a company."""
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )
        
        # Read file data
        logo_data = await file.read()
        
        # Validate file size
        if len(logo_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Update database with binary data
        db.client.table("companies")\
            .update({
                "logo_data": logo_data,
                "logo_filename": file.filename,
                "logo_content_type": file.content_type
            })\
            .eq("id", company_id)\
            .execute()
        
        return {"message": "Logo uploaded successfully", "filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/logo")
async def get_company_logo(company_id: str):
    """Get the logo for a company."""
    try:
        result = db.client.table("companies")\
            .select("logo_data, logo_content_type, logo_filename")\
            .eq("id", company_id)\
            .single()\
            .execute()
        
        if not result.data or not result.data.get("logo_data"):
            raise HTTPException(status_code=404, detail="Logo not found")
        
        return Response(
            content=bytes(result.data["logo_data"]),
            media_type=result.data.get("logo_content_type", "image/png")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{company_id}/logo")
async def delete_company_logo(company_id: str):
    """Delete the logo for a company."""
    try:
        db.client.table("companies")\
            .update({
                "logo_data": None,
                "logo_filename": None,
                "logo_content_type": None
            })\
            .eq("id", company_id)\
            .execute()
        
        return {"message": "Logo deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMPANY ENRICHMENT ====================

def _enrich_company_background(company_id: str, company_name: str, logo_url: str):
    """Background task for enriching a single company."""
    try:
        from ingestion.company_enrichment import enrich_company
        logger.info(f"🔄 Background enrichment started for company: {company_name}")
        result = enrich_company(company_id, company_name, logo_url)
        if result["success"]:
            logger.info(f"✅ Background enrichment complete for company: {company_name}")
        else:
            logger.error(f"❌ Background enrichment failed for company: {company_name} - {result.get('error')}")
    except Exception as e:
        logger.error(f"❌ Background enrichment error for company: {company_name} - {e}")


@router.post("/{company_id}/enrich")
async def enrich_single_company(company_id: str, background_tasks: BackgroundTasks):
    """Enrich a single company with AI (runs in background)."""
    try:
        # Get company details
        company = db.client.table("companies")\
            .select("id, name, logo_url")\
            .eq("id", company_id)\
            .single()\
            .execute()
        
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_data = company.data
        
        # Add to background tasks
        background_tasks.add_task(
            _enrich_company_background,
            company_id,
            company_data.get("name", "Unknown"),
            company_data.get("logo_url")
        )
        
        return {
            "message": "Company enrichment started in background",
            "company_id": company_id,
            "company_name": company_data.get("name")
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _enrich_companies_batch_background(company_ids: List[str]):
    """Background task for batch enriching companies."""
    try:
        from ingestion.company_enrichment import enrich_companies_batch
        logger.info(f"🔄 Background batch enrichment started for {len(company_ids)} companies")
        stats = enrich_companies_batch(company_ids)
        logger.info(f"✅ Background batch enrichment complete: {stats['successful']} successful, {stats['failed']} failed")
    except Exception as e:
        logger.error(f"❌ Background batch enrichment error: {e}")


@router.post("/enrich/batch")
async def enrich_companies_batch_endpoint(company_ids: List[str], background_tasks: BackgroundTasks):
    """Enrich multiple companies in batch (runs in background)."""
    try:
        if not company_ids:
            raise HTTPException(status_code=400, detail="No company IDs provided")
        
        # Add to background tasks
        background_tasks.add_task(_enrich_companies_batch_background, company_ids)
        
        return {
            "message": f"Batch enrichment started in background for {len(company_ids)} companies",
            "company_count": len(company_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrich/unenriched")
async def get_unenriched_companies(limit: int = 1000):
    """Get list of companies that haven't been enriched yet."""
    try:
        from ingestion.company_enrichment import get_unenriched_companies
        
        company_ids = get_unenriched_companies(limit)
        
        return {
            "company_ids": company_ids,
            "count": len(company_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrich/stats")
async def get_enrichment_stats():
    """Get statistics about company enrichment."""
    try:
        from ingestion.company_enrichment import get_enrichment_stats
        
        stats = get_enrichment_stats()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMPANY SIZE CLASSIFICATION ====================
# Note: Size classification is now included in the unified enrichment (prompt v5)
# Use /enrich/batch or /companies/{id}/enrich instead

@router.post("/{company_id}/classify-size")
async def classify_company_size(company_id: str):
    """
    DEPRECATED: Use unified enrichment instead.
    Size classification is now automatically included in company enrichment (prompt v5).
    This endpoint triggers a full re-enrichment.
    """
    try:
        from ingestion.company_enrichment import enrich_company
        
        # Get company data
        company = db.client.table("companies")\
            .select("id, name, logo_url")\
            .eq("id", company_id)\
            .single()\
            .execute()
        
        if not company.data:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_name = company.data.get("name")
        company_url = company.data.get("logo_url")
        
        if not company_name:
            raise HTTPException(status_code=400, detail="Company has no name")
        
        # Run unified enrichment (includes size classification)
        result = enrich_company(company_id, company_name, company_url)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Enrichment failed"))
        
        # Extract classification from enrichment data
        enrichment_data = result.get("data", {})
        classification = {
            "category": enrichment_data.get("category"),
            "confidence": enrichment_data.get("confidence"),
            "summary": enrichment_data.get("summary"),
            "key_arguments": enrichment_data.get("key_arguments"),
            "sources": enrichment_data.get("sources")
        }
        
        return {
            "success": True,
            "classification": classification,
            "note": "This endpoint is deprecated. Size classification is now included in unified enrichment."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/size-classification/stats")
async def get_size_classification_stats():
    """Get statistics about company size classifications."""
    try:
        from ingestion.company_size_enrichment import get_classification_stats
        
        stats = get_classification_stats()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
