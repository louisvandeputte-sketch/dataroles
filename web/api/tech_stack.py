"""API endpoints for tech stack masterdata management."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from database.client import db

router = APIRouter()


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
