"""Supabase client wrapper for database operations."""

from supabase import create_client, Client
from config.settings import settings
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from loguru import logger


class SupabaseClient:
    """Wrapper around Supabase client for database operations."""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("Supabase client initialized")
    
    def test_connection(self) -> bool:
        """Test database connection by querying a simple table."""
        try:
            # Try to query scrape_runs table (should exist after schema setup)
            result = self.client.table("scrape_runs").select("id").limit(1).execute()
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    # ==================== COMPANIES ====================
    
    def insert_company(self, data: Dict[str, Any]) -> UUID:
        """Insert a new company, return UUID."""
        result = self.client.table("companies").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    def get_company_by_linkedin_id(self, linkedin_id: str) -> Optional[Dict]:
        """Get company by LinkedIn company ID."""
        result = self.client.table("companies")\
            .select("*")\
            .eq("linkedin_company_id", linkedin_id)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def upsert_company(self, data: Dict[str, Any]) -> UUID:
        """Insert or update company, return UUID."""
        result = self.client.table("companies")\
            .upsert(data, on_conflict="linkedin_company_id")\
            .execute()
        return UUID(result.data[0]["id"])
    
    # ==================== LOCATIONS ====================
    
    def get_location_by_string(self, location_string: str) -> Optional[Dict]:
        """Get location by exact full_location_string match."""
        result = self.client.table("locations")\
            .select("*")\
            .eq("full_location_string", location_string)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def insert_location(self, data: Dict[str, Any]) -> UUID:
        """Insert a new location, return UUID."""
        result = self.client.table("locations").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    # ==================== JOB POSTINGS ====================
    
    def get_job_by_linkedin_id(self, linkedin_job_id: str) -> Optional[Dict]:
        """Get job posting by LinkedIn job ID."""
        result = self.client.table("job_postings")\
            .select("*")\
            .eq("linkedin_job_id", linkedin_job_id)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def insert_job_posting(self, data: Dict[str, Any]) -> UUID:
        """Insert a new job posting, return UUID."""
        result = self.client.table("job_postings").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    def update_job_posting(self, job_id: UUID, data: Dict[str, Any]) -> None:
        """Update existing job posting."""
        self.client.table("job_postings")\
            .update(data)\
            .eq("id", str(job_id))\
            .execute()
    
    def mark_jobs_inactive(self, job_ids: List[UUID]) -> int:
        """Mark multiple jobs as inactive."""
        result = self.client.table("job_postings")\
            .update({
                "is_active": False,
                "detected_inactive_at": datetime.utcnow().isoformat()
            })\
            .in_("id", [str(jid) for jid in job_ids])\
            .execute()
        return len(result.data)
    
    # ==================== JOB DESCRIPTIONS ====================
    
    def insert_job_description(self, data: Dict[str, Any]) -> UUID:
        """Insert job description."""
        result = self.client.table("job_descriptions").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    # ==================== JOB POSTERS ====================
    
    def insert_job_poster(self, data: Dict[str, Any]) -> UUID:
        """Insert job poster if data available."""
        result = self.client.table("job_posters").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    # ==================== LLM ENRICHMENT ====================
    
    def insert_llm_enrichment_stub(self, job_posting_id: UUID) -> UUID:
        """Insert empty LLM enrichment record for future processing."""
        result = self.client.table("llm_enrichment")\
            .insert({"job_posting_id": str(job_posting_id)})\
            .execute()
        return UUID(result.data[0]["id"])
    
    # ==================== SCRAPE RUNS ====================
    
    def create_scrape_run(self, data: Dict[str, Any]) -> UUID:
        """Create a new scrape run record."""
        result = self.client.table("scrape_runs").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    def update_scrape_run(self, run_id: UUID, data: Dict[str, Any]) -> None:
        """Update scrape run with results/status."""
        self.client.table("scrape_runs")\
            .update(data)\
            .eq("id", str(run_id))\
            .execute()
    
    def get_last_successful_run(self, query: str, location: str) -> Optional[Dict]:
        """Get the most recent successful run for a query+location."""
        result = self.client.table("scrape_runs")\
            .select("*")\
            .eq("search_query", query)\
            .eq("location_query", location)\
            .eq("status", "completed")\
            .order("completed_at", desc=True)\
            .limit(1)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def get_scrape_runs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get scrape runs with optional filtering."""
        query = self.client.table("scrape_runs").select("*")
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("started_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return result.data
    
    # ==================== JOB SCRAPE HISTORY ====================
    
    def insert_scrape_history(self, job_id: UUID, run_id: UUID) -> None:
        """Record that a job was seen in a scrape run."""
        self.client.table("job_scrape_history").insert({
            "job_posting_id": str(job_id),
            "scrape_run_id": str(run_id)
        }).execute()
    
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics for dashboard."""
        stats = {}
        
        # Total jobs
        result = self.client.table("job_postings").select("id", count="exact").execute()
        stats["total_jobs"] = result.count
        
        # Active jobs
        result = self.client.table("job_postings")\
            .select("id", count="exact")\
            .eq("is_active", True)\
            .execute()
        stats["active_jobs"] = result.count
        
        # Companies
        result = self.client.table("companies").select("id", count="exact").execute()
        stats["total_companies"] = result.count
        
        # Recent runs (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        result = self.client.table("scrape_runs")\
            .select("id", count="exact")\
            .gte("started_at", week_ago)\
            .execute()
        stats["runs_last_7_days"] = result.count
        
        return stats
    
    # ==================== JOB QUERIES ====================
    
    def search_jobs(
        self,
        search_query: Optional[str] = None,
        location: Optional[str] = None,
        company_ids: Optional[List[str]] = None,
        location_ids: Optional[List[str]] = None,
        seniority: Optional[List[str]] = None,
        employment: Optional[List[str]] = None,
        active_only: bool = True,
        job_ids: Optional[List[str]] = None,  # NEW: Filter by specific job IDs
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict], int]:
        """
        Search jobs with filters. Returns (jobs, total_count).
        """
        # Build query
        query = self.client.table("job_postings")\
            .select("*, companies(*), locations(*)", count="exact")
        
        # NEW: Filter by job IDs if provided (for run_id filtering)
        if job_ids is not None:
            if len(job_ids) == 0:
                # No jobs in this run, return empty
                return [], 0
            query = query.in_("id", job_ids)
        
        if active_only:
            query = query.eq("is_active", True)
        
        if search_query:
            # Simple text search in title
            query = query.ilike("title", f"%{search_query}%")
        
        # Filter by company IDs
        if company_ids and len(company_ids) > 0:
            query = query.in_("company_id", company_ids)
        
        # Filter by location IDs
        if location_ids and len(location_ids) > 0:
            query = query.in_("location_id", location_ids)
        
        # Filter by seniority (can be multiple)
        if seniority and len(seniority) > 0:
            query = query.in_("seniority_level", seniority)
        
        # Filter by employment type (can be multiple)
        if employment and len(employment) > 0:
            query = query.in_("employment_type", employment)
        
        # Execute with pagination
        result = query.order("posted_date", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Enrich jobs with their types and AI enrichment status
        jobs_with_types = []
        for job in result.data:
            # Get job types for this job
            types_result = self.client.table("job_type_assignments")\
                .select("job_types(id, name, color)")\
                .eq("job_posting_id", job["id"])\
                .execute()
            
            # Extract types from nested structure
            job_types = []
            if types_result.data:
                for assignment in types_result.data:
                    if assignment.get("job_types"):
                        job_types.append(assignment["job_types"])
            
            job["job_types"] = job_types
            
            # Get AI enrichment status
            enrichment_result = self.client.table("llm_enrichment")\
                .select("enrichment_completed_at, type_datarol, rolniveau")\
                .eq("job_posting_id", job["id"])\
                .single()\
                .execute()
            
            if enrichment_result.data:
                job["ai_enriched"] = enrichment_result.data.get("enrichment_completed_at") is not None
                job["ai_data"] = enrichment_result.data if job["ai_enriched"] else None
            else:
                job["ai_enriched"] = False
                job["ai_data"] = None
            
            jobs_with_types.append(job)
        
        return jobs_with_types, result.count


# Global client instance
db = SupabaseClient()


def get_supabase_client() -> Client:
    """Get the global Supabase client instance."""
    return db.client
