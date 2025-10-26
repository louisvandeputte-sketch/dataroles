"""API endpoints for tech stack masterdata management."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from typing import List, Optional
from pydantic import BaseModel
import io
import base64
from PIL import Image

from database.client import db

router = APIRouter()

# Allowed image types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'webp'}
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# ==================== MODELS ====================

class ProgrammingLanguageCreate(BaseModel):
    name: str
    display_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None


class ProgrammingLanguageUpdate(BaseModel):
    display_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class EcosystemCreate(BaseModel):
    name: str
    display_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None


class EcosystemUpdate(BaseModel):
    display_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== PROGRAMMING LANGUAGES ====================

@router.get("/programming-languages")
async def list_programming_languages(active_only: bool = True):
    """Get all programming languages."""
    languages = db.get_all_programming_languages(active_only=active_only)
    return {"languages": languages, "total": len(languages)}


@router.get("/programming-languages/{language_id}")
async def get_programming_language(language_id: str):
    """Get a specific programming language by ID."""
    result = db.client.table("programming_languages")\
        .select("*")\
        .eq("id", language_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Programming language not found")
    
    return result.data


@router.post("/programming-languages")
async def create_programming_language(language: ProgrammingLanguageCreate):
    """Create a new programming language."""
    try:
        language_id = db.insert_programming_language(language.model_dump())
        return {"id": str(language_id), "message": "Programming language created successfully"}
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Programming language with this name already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/programming-languages/{language_id}")
async def update_programming_language(language_id: str, updates: ProgrammingLanguageUpdate):
    """Update a programming language."""
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        db.client.table("programming_languages")\
            .update(update_data)\
            .eq("id", language_id)\
            .execute()
        
        return {"message": "Programming language updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/programming-languages/{language_id}")
async def delete_programming_language(language_id: str, hard_delete: bool = False):
    """Delete (soft or hard) a programming language."""
    try:
        if hard_delete:
            db.client.table("programming_languages")\
                .delete()\
                .eq("id", language_id)\
                .execute()
        else:
            # Soft delete
            db.client.table("programming_languages")\
                .update({"is_active": False})\
                .eq("id", language_id)\
                .execute()
        
        return {"message": "Programming language deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/programming-languages/{language_id}/logo")
async def upload_programming_language_logo(language_id: str, file: UploadFile = File(...)):
    """Upload a logo for a programming language."""
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
        
        # Convert to base64 for PostgreSQL bytea storage
        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
        
        # Update database with base64-encoded data
        db.client.table("programming_languages")\
            .update({
                "logo_data": logo_base64,
                "logo_filename": file.filename,
                "logo_content_type": file.content_type
            })\
            .eq("id", language_id)\
            .execute()
        
        return {"message": "Logo uploaded successfully", "filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/programming-languages/{language_id}/logo")
async def get_programming_language_logo(language_id: str):
    """Get the logo for a programming language."""
    try:
        result = db.client.table("programming_languages")\
            .select("logo_data, logo_content_type, logo_filename")\
            .eq("id", language_id)\
            .single()\
            .execute()
        
        if not result.data or not result.data.get("logo_data"):
            raise HTTPException(status_code=404, detail="Logo not found")
        
        # Decode base64 data
        logo_bytes = base64.b64decode(result.data["logo_data"])
        
        return Response(
            content=logo_bytes,
            media_type=result.data.get("logo_content_type", "image/png")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/programming-languages/{language_id}/logo")
async def delete_programming_language_logo(language_id: str):
    """Delete the logo for a programming language."""
    try:
        db.client.table("programming_languages")\
            .update({
                "logo_data": None,
                "logo_filename": None,
                "logo_content_type": None
            })\
            .eq("id", language_id)\
            .execute()
        
        return {"message": "Logo deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ECOSYSTEMS ====================

@router.get("/ecosystems")
async def list_ecosystems(active_only: bool = True):
    """Get all ecosystems."""
    ecosystems = db.get_all_ecosystems(active_only=active_only)
    return {"ecosystems": ecosystems, "total": len(ecosystems)}


@router.get("/ecosystems/{ecosystem_id}")
async def get_ecosystem(ecosystem_id: str):
    """Get a specific ecosystem by ID."""
    result = db.client.table("ecosystems")\
        .select("*")\
        .eq("id", ecosystem_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Ecosystem not found")
    
    return result.data


@router.post("/ecosystems")
async def create_ecosystem(ecosystem: EcosystemCreate):
    """Create a new ecosystem."""
    try:
        ecosystem_id = db.insert_ecosystem(ecosystem.model_dump())
        return {"id": str(ecosystem_id), "message": "Ecosystem created successfully"}
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Ecosystem with this name already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ecosystems/{ecosystem_id}")
async def update_ecosystem(ecosystem_id: str, updates: EcosystemUpdate):
    """Update an ecosystem."""
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        db.client.table("ecosystems")\
            .update(update_data)\
            .eq("id", ecosystem_id)\
            .execute()
        
        return {"message": "Ecosystem updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ecosystems/{ecosystem_id}")
async def delete_ecosystem(ecosystem_id: str, hard_delete: bool = False):
    """Delete (soft or hard) an ecosystem."""
    try:
        if hard_delete:
            db.client.table("ecosystems")\
                .delete()\
                .eq("id", ecosystem_id)\
                .execute()
        else:
            # Soft delete
            db.client.table("ecosystems")\
                .update({"is_active": False})\
                .eq("id", ecosystem_id)\
                .execute()
        
        return {"message": "Ecosystem deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ecosystems/{ecosystem_id}/logo")
async def upload_ecosystem_logo(ecosystem_id: str, file: UploadFile = File(...)):
    """Upload a logo for an ecosystem."""
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
        
        # Convert to base64 for PostgreSQL bytea storage
        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
        
        # Update database with base64-encoded data
        db.client.table("ecosystems")\
            .update({
                "logo_data": logo_base64,
                "logo_filename": file.filename,
                "logo_content_type": file.content_type
            })\
            .eq("id", ecosystem_id)\
            .execute()
        
        return {"message": "Logo uploaded successfully", "filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ecosystems/{ecosystem_id}/logo")
async def get_ecosystem_logo(ecosystem_id: str):
    """Get the logo for an ecosystem."""
    try:
        result = db.client.table("ecosystems")\
            .select("logo_data, logo_content_type, logo_filename")\
            .eq("id", ecosystem_id)\
            .single()\
            .execute()
        
        if not result.data or not result.data.get("logo_data"):
            raise HTTPException(status_code=404, detail="Logo not found")
        
        # Decode base64 data
        logo_bytes = base64.b64decode(result.data["logo_data"])
        
        return Response(
            content=logo_bytes,
            media_type=result.data.get("logo_content_type", "image/png")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ecosystems/{ecosystem_id}/logo")
async def delete_ecosystem_logo(ecosystem_id: str):
    """Delete the logo for an ecosystem."""
    try:
        db.client.table("ecosystems")\
            .update({
                "logo_data": None,
                "logo_filename": None,
                "logo_content_type": None
            })\
            .eq("id", ecosystem_id)\
            .execute()
        
        return {"message": "Logo deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATS ====================

@router.get("/stats")
async def get_tech_stack_stats():
    """Get statistics about tech stack masterdata."""
    try:
        # Count programming languages
        lang_result = db.client.table("programming_languages")\
            .select("id", count="exact")\
            .execute()
        
        lang_active_result = db.client.table("programming_languages")\
            .select("id", count="exact")\
            .eq("is_active", True)\
            .execute()
        
        # Count ecosystems
        eco_result = db.client.table("ecosystems")\
            .select("id", count="exact")\
            .execute()
        
        eco_active_result = db.client.table("ecosystems")\
            .select("id", count="exact")\
            .eq("is_active", True)\
            .execute()
        
        # Count job assignments
        job_lang_result = db.client.table("job_programming_languages")\
            .select("id", count="exact")\
            .execute()
        
        job_eco_result = db.client.table("job_ecosystems")\
            .select("id", count="exact")\
            .execute()
        
        return {
            "programming_languages": {
                "total": lang_result.count or 0,
                "active": lang_active_result.count or 0
            },
            "ecosystems": {
                "total": eco_result.count or 0,
                "active": eco_active_result.count or 0
            },
            "assignments": {
                "job_languages": job_lang_result.count or 0,
                "job_ecosystems": job_eco_result.count or 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
