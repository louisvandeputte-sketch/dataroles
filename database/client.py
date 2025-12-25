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
    
    def get_company_by_name(self, name: str) -> Optional[Dict]:
        """
        Get company by exact name match.
        
        Priority: Returns company with logo_data first, then linkedin_company_id, then first match.
        This ensures we reuse the "best" company when deduplicating by name.
        """
        result = self.client.table("companies")\
            .select("*")\
            .eq("name", name)\
            .execute()
        
        if not result.data:
            return None
        
        if len(result.data) == 1:
            return result.data[0]
        
        # Multiple companies with same name - return best one
        # Priority: logo_data > linkedin_company_id > first
        companies = result.data
        
        # First try: company with logo
        with_logo = [c for c in companies if c.get('logo_data')]
        if with_logo:
            return with_logo[0]
        
        # Second try: company with LinkedIn ID
        with_linkedin = [c for c in companies if c.get('linkedin_company_id')]
        if with_linkedin:
            return with_linkedin[0]
        
        # Fallback: first one
        return companies[0]
    
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
    
    # ==================== PROGRAMMING LANGUAGES ====================
    
    def get_programming_language_by_name(self, name: str) -> Optional[Dict]:
        """Get programming language by canonical name."""
        result = self.client.table("programming_languages")\
            .select("*")\
            .eq("name", name)\
            .eq("is_active", True)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def insert_programming_language(self, data: Dict[str, Any]) -> UUID:
        """Insert a new programming language, return UUID."""
        result = self.client.table("programming_languages").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    def upsert_programming_language(self, data: Dict[str, Any]) -> UUID:
        """Insert or update programming language, return UUID."""
        result = self.client.table("programming_languages")\
            .upsert(data, on_conflict="name")\
            .execute()
        return UUID(result.data[0]["id"])
    
    def get_all_programming_languages(self, active_only: bool = True) -> List[Dict]:
        """Get all programming languages with pagination to handle >1000 records."""
        all_languages = []
        page_size = 1000
        offset = 0
        
        while True:
            query = self.client.table("programming_languages").select("*")
            if active_only:
                query = query.eq("is_active", True)
            result = query.order("name").range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
                
            all_languages.extend(result.data)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        return all_languages
    
    # ==================== ECOSYSTEMS ====================
    
    def get_ecosystem_by_name(self, name: str) -> Optional[Dict]:
        """Get ecosystem by canonical name."""
        result = self.client.table("ecosystems")\
            .select("*")\
            .eq("name", name)\
            .eq("is_active", True)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def insert_ecosystem(self, data: Dict[str, Any]) -> UUID:
        """Insert a new ecosystem, return UUID."""
        result = self.client.table("ecosystems").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    def upsert_ecosystem(self, data: Dict[str, Any]) -> UUID:
        """Insert or update ecosystem, return UUID."""
        result = self.client.table("ecosystems")\
            .upsert(data, on_conflict="name")\
            .execute()
        return UUID(result.data[0]["id"])
    
    def get_all_ecosystems(self, active_only: bool = True) -> List[Dict]:
        """Get all ecosystems with pagination to handle >1000 records."""
        all_ecosystems = []
        page_size = 1000
        offset = 0
        
        while True:
            query = self.client.table("ecosystems").select("*")
            if active_only:
                query = query.eq("is_active", True)
            result = query.order("name").range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
                
            all_ecosystems.extend(result.data)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        return all_ecosystems
    
    # ==================== TECH STACK ALIASES ====================
    
    def get_tech_alias(self, alias: str, tech_type: str) -> Optional[Dict]:
        """Get canonical name for an alias (case-insensitive)."""
        result = self.client.table("tech_stack_aliases")\
            .select("*")\
            .ilike("alias", alias)\
            .eq("type", tech_type)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def create_tech_alias(self, alias: str, canonical_name: str, tech_type: str, notes: str = None) -> UUID:
        """Create a new tech stack alias."""
        data = {
            "alias": alias,
            "canonical_name": canonical_name,
            "type": tech_type
        }
        if notes:
            data["notes"] = notes
        
        result = self.client.table("tech_stack_aliases").insert(data).execute()
        return UUID(result.data[0]["id"])
    
    # ==================== JOB TECH STACK ASSIGNMENTS ====================
    
    def assign_programming_language_to_job(
        self, 
        job_id: UUID, 
        language_id: UUID, 
        requirement_level: str
    ) -> None:
        """Assign a programming language to a job."""
        self.client.table("job_programming_languages").insert({
            "job_posting_id": str(job_id),
            "programming_language_id": str(language_id),
            "requirement_level": requirement_level
        }).execute()
    
    def assign_ecosystem_to_job(
        self, 
        job_id: UUID, 
        ecosystem_id: UUID, 
        requirement_level: str
    ) -> None:
        """Assign an ecosystem to a job."""
        self.client.table("job_ecosystems").insert({
            "job_posting_id": str(job_id),
            "ecosystem_id": str(ecosystem_id),
            "requirement_level": requirement_level
        }).execute()
    
    def get_job_programming_languages(self, job_id: UUID) -> List[Dict]:
        """Get all programming languages for a job with requirement levels."""
        result = self.client.table("job_programming_languages")\
            .select("*, programming_languages(*)")\
            .eq("job_posting_id", str(job_id))\
            .execute()
        return result.data if result.data else []
    
    def get_job_ecosystems(self, job_id: UUID) -> List[Dict]:
        """Get all ecosystems for a job with requirement levels."""
        result = self.client.table("job_ecosystems")\
            .select("*, ecosystems(*)")\
            .eq("job_posting_id", str(job_id))\
            .execute()
        return result.data if result.data else []
    
    # ==================== JOB POSTINGS ====================
    
    def get_job_by_linkedin_id(self, linkedin_job_id: str) -> Optional[Dict]:
        """Get job posting by LinkedIn job ID."""
        result = self.client.table("job_postings")\
            .select("*")\
            .eq("linkedin_job_id", linkedin_job_id)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def get_job_by_indeed_id(self, indeed_job_id: str) -> Optional[Dict]:
        """Get job posting by Indeed job ID."""
        result = self.client.table("job_postings")\
            .select("*")\
            .eq("indeed_job_id", indeed_job_id)\
            .maybe_single()\
            .execute()
        return result.data if result else None
    
    def insert_job_posting(self, data: Dict[str, Any]) -> UUID:
        """
        Insert a new job posting, return UUID.
        Automatically sets posted_date_corrected if not provided.
        """
        # Automatically set posted_date_corrected if not provided
        # This ensures new jobs always have this field populated
        if "posted_date_corrected" not in data and "posted_date" in data:
            data["posted_date_corrected"] = data["posted_date"]
        
        result = self.client.table("job_postings").insert(data).execute()
        job_id = UUID(result.data[0]["id"])
        
        # After insert, check if we need to update posted_date_corrected with first_seen_at
        # This happens when job_sources is inserted after job_postings
        if "posted_date" in data:
            # Schedule an async update to check first_seen_at later
            # For now, we use posted_date as initial value
            pass
        
        return job_id
    
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
        type_ids: Optional[List[str]] = None,
        seniority: Optional[List[str]] = None,
        employment: Optional[List[str]] = None,
        posted_date: Optional[str] = None,
        ai_enriched: Optional[bool] = None,
        title_classification: Optional[str] = None,
        type_datarol: Optional[str] = None,
        contract: Optional[str] = None,
        subdivision_name_en: Optional[str] = None,
        source: Optional[str] = None,
        active_only: bool = True,
        job_ids: Optional[List[str]] = None,
        sort_field: str = "ranking_position",  # Changed from posted_date to ranking_position
        sort_direction: str = "asc",  # Changed from desc to asc (lower rank = better)
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict], int]:
        """
        Search jobs with filters. Returns (jobs, total_count).
        Default sort is by ranking_position (ASC) to show best jobs first.
        """
        # Build query - include job_sources for multi-source support and llm_enrichment for type_datarol/contract filtering
        # Use explicit relationship name for locations to avoid ambiguity with location_id_override
        query = self.client.table("job_postings")\
            .select("*, companies(id, name, logo_url), locations!job_postings_location_id_fkey(id, city, country_code, subdivision_name_en), job_sources(source, source_job_id), llm_enrichment(type_datarol, seniority, rolniveau, contract, enrichment_completed_at)", count="exact")
        
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
        
        # Filter by posted date
        if posted_date and posted_date != 'all':
            from datetime import datetime, timedelta
            now = datetime.now()
            if posted_date == 'today':
                date_threshold = now - timedelta(days=1)
            elif posted_date == 'week':
                date_threshold = now - timedelta(days=7)
            elif posted_date == 'month':
                date_threshold = now - timedelta(days=30)
            else:
                date_threshold = None
            
            if date_threshold:
                query = query.gte("posted_date", date_threshold.isoformat())
        
        # Filter by title classification
        if title_classification:
            query = query.eq("title_classification", title_classification)
        
        # Filter by data role type (requires join with llm_enrichment)
        if type_datarol:
            # Note: This requires llm_enrichment to be joined in the select
            query = query.eq("llm_enrichment.type_datarol", type_datarol)
        
        # Filter by contract type (requires join with llm_enrichment)
        if contract:
            query = query.eq("llm_enrichment.contract", contract)
        
        # Filter by subdivision (province/region) in English
        if subdivision_name_en:
            query = query.eq("locations.subdivision_name_en", subdivision_name_en)
        
        # Filter by source (linkedin or indeed)
        if source:
            query = query.eq("source", source)
        
        # Filter by AI enrichment status (server-side)
        if ai_enriched is not None:
            if ai_enriched:
                # Only enriched: must have llm_enrichment with completed_at
                query = query.not_.is_("llm_enrichment.enrichment_completed_at", "null")
            else:
                # Only unenriched: either no llm_enrichment OR enrichment_completed_at is null
                # Use OR filter: llm_enrichment is null OR enrichment_completed_at is null
                query = query.or_("llm_enrichment.is.null,llm_enrichment.enrichment_completed_at.is.null")
        
        # Execute with pagination and sorting
        # Apply sorting based on parameters
        is_desc = sort_direction.lower() == "desc"
        
        # If sorting by ranking_position, add secondary sort by ranking_score DESC
        # This ensures correct order even if there are duplicate positions
        # NULLS LAST ensures unranked jobs appear at the bottom
        if sort_field == "ranking_position":
            result = query.order(sort_field, desc=is_desc, nullsfirst=False)\
                .order("ranking_score", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
        else:
            result = query.order(sort_field, desc=is_desc)\
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
            
            # Filter by type_ids if specified
            if type_ids and len(type_ids) > 0:
                job_type_ids = [jt["id"] for jt in job_types]
                # Check if any of the job's types match the filter
                if not any(type_id in job_type_ids for type_id in type_ids):
                    continue  # Skip this job
            
            # Get AI enrichment status from joined data
            enrichment_data = job.get("llm_enrichment")
            if enrichment_data:
                job["ai_enriched"] = enrichment_data.get("enrichment_completed_at") is not None
                job["ai_data"] = enrichment_data if job["ai_enriched"] else None
            else:
                job["ai_enriched"] = False
                job["ai_data"] = None
            
            jobs_with_types.append(job)
        
        return jobs_with_types, result.count
    
    def get_recent_jobs_with_runs(self, hours: int = 24, limit: int = 200) -> List[Dict]:
        """Get jobs scraped in the last N hours with run metadata."""
        from datetime import datetime, timedelta

        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        history_result = self.client.table("job_scrape_history")\
            .select("job_posting_id, scrape_run_id, detected_at")\
            .gte("detected_at", since)\
            .order("detected_at", desc=True)\
            .limit(limit)\
            .execute()

        history = history_result.data or []
        if not history:
            return []

        # Fetch run metadata for all referenced runs
        run_ids = [h["scrape_run_id"] for h in history if h.get("scrape_run_id")]
        run_map: Dict[str, Dict] = {}
        if run_ids:
            runs_result = self.client.table("scrape_runs")\
                .select("id, search_query, source, started_at")\
                .in_("id", list(set(run_ids)))\
                .execute()
            if runs_result.data:
                run_map = {run["id"]: run for run in runs_result.data}

        # Fetch job details for all referenced jobs (include inactive)
        job_ids = [h["job_posting_id"] for h in history if h.get("job_posting_id")]
        job_map: Dict[str, Dict] = {}
        earliest_detected: Dict[str, str] = {}
        if job_ids:
            unique_job_ids = list(set(job_ids))
            jobs, _ = self.search_jobs(job_ids=unique_job_ids, active_only=False, limit=len(unique_job_ids))
            job_map = {job["id"]: job for job in jobs}

            all_history = self.client.table("job_scrape_history")\
                .select("job_posting_id, detected_at")\
                .in_("job_posting_id", unique_job_ids)\
                .order("detected_at", desc=False)\
                .execute()

            for row in all_history.data or []:
                jp = row.get("job_posting_id")
                if jp and jp not in earliest_detected:
                    earliest_detected[jp] = row.get("detected_at")

        recent_jobs: List[Dict] = []
        for entry in history:
            job = job_map.get(entry.get("job_posting_id"))
            if not job:
                continue

            run = run_map.get(entry.get("scrape_run_id"))
            company = job.get("companies") or {}
            job_types = job.get("job_types") or []
            detected_at = entry.get("detected_at")

            recent_jobs.append({
                "job_id": job.get("id"),
                "title": job.get("title"),
                "company_name": company.get("name"),
                "posted_date": job.get("posted_date"),
                "title_classification": job.get("title_classification"),
                "job_types": job_types,
                "run_id": entry.get("scrape_run_id"),
                "run_search_query": run.get("search_query") if run else None,
                "run_source": run.get("source") if run else job.get("source"),
                "run_started_at": run.get("started_at") if run else None,
                "detected_at": detected_at,
                "is_new": detected_at == earliest_detected.get(job.get("id"))
            })

        return recent_jobs

    # ==================== VAGUE LOCATIONS CONFIG ====================

    def get_vague_location_patterns(self) -> List[str]:
        """
        Get list of active vague location patterns from config table.
        Returns list of pattern strings (e.g., ['Flemish Region', 'Belgium']).
        Falls back to hardcoded defaults if table doesn't exist or is empty.
        """
        try:
            result = self.client.table("vague_locations_config")\
                .select("pattern")\
                .eq("is_active", True)\
                .execute()
            
            if result.data:
                patterns = [row["pattern"] for row in result.data]
                logger.debug(f"Loaded {len(patterns)} vague location patterns from config")
                return patterns
            else:
                logger.warning("No vague location patterns found in config, using defaults")
                return self._get_default_vague_patterns()
        except Exception as e:
            logger.warning(f"Could not load vague location patterns from config: {e}, using defaults")
            return self._get_default_vague_patterns()
    
    def _get_default_vague_patterns(self) -> List[str]:
        """Fallback default vague location patterns."""
        return [
            "Flemish Region",
            "Walloon Region",
            "Brussels-Capital Region",
            "Belgium",
            "België"
        ]


# Global client instance
db = SupabaseClient()


def get_supabase_client() -> Client:
    """Get the global Supabase client instance."""
    return db.client
