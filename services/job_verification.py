"""LinkedIn Job Verification Service.

Verifies if active LinkedIn jobs still exist by checking their URLs via Bright Data API.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from uuid import UUID
from loguru import logger

from database.client import db
from clients.brightdata_linkedin import BrightDataLinkedInClient
from clients.brightdata_indeed import BrightDataIndeedClient
from config.settings import settings


ALT_SOURCE_GRACE_DAYS = 3


class JobVerificationService:
    """Service for verifying if LinkedIn and Indeed jobs are still active."""
    
    def __init__(self):
        """Initialize the verification service."""
        linkedin_dataset_id = getattr(
            settings,
            "brightdata_linkedin_dataset_id",
            getattr(settings, "brightdata_dataset_id", None)
        )
        if not linkedin_dataset_id:
            raise ValueError("LinkedIn dataset ID is not configured")

        indeed_dataset_id = getattr(
            settings,
            "brightdata_indeed_dataset_id",
            "gd_l4dx9j9sscpvs7no2"  # Default Indeed dataset ID
        )

        self.linkedin_client = BrightDataLinkedInClient(
            api_token=settings.brightdata_api_token,
            dataset_id=linkedin_dataset_id
        )
        self.indeed_client = BrightDataIndeedClient(
            api_token=settings.brightdata_api_token,
            dataset_id=indeed_dataset_id
        )
    
    async def verify_active_jobs(
        self,
        batch_size: int = 100,
        only_data_jobs: bool = True,
        source: Optional[str] = None,
        trigger_type: str = "manual"
    ) -> Dict[str, int]:
        """
        Verify all active jobs by checking if they still exist.
        
        Args:
            batch_size: Number of jobs to verify per batch
            only_data_jobs: Only verify jobs where title_classification = 'Data'
            source: Filter by source ('linkedin', 'indeed', or None for both)
            trigger_type: How the run was triggered ('scheduled' or 'manual')
        
        Returns:
            Dictionary with counts: verified, still_active, marked_inactive, errors
        """
        sources = [source] if source else ['linkedin', 'indeed']
        logger.info(f"🔍 Starting job verification for sources: {sources}...")
        
        total_stats = {
            "verified": 0,
            "still_active": 0,
            "marked_inactive": 0,
            "errors": 0
        }
        
        for src in sources:
            logger.info(f"\n📍 Verifying {src.upper()} jobs...")
            
            # Create verification run record
            run_id = self._create_verification_run(
                source=src,
                batch_size=batch_size,
                only_data_jobs=only_data_jobs,
                trigger_type=trigger_type
            )
            
            try:
                jobs_to_verify = self._get_jobs_to_verify(
                    only_data_jobs=only_data_jobs,
                    source=src
                )
            
                if not jobs_to_verify:
                    logger.info(f"No {src} jobs to verify")
                    # Complete run with 0 jobs
                    self._complete_verification_run(run_id, {
                        "verified": 0,
                        "still_active": 0,
                        "marked_inactive": 0,
                        "errors": 0
                    })
                    continue
                
                logger.info(f"Found {len(jobs_to_verify)} {src} jobs to verify")
                
                run_stats = {
                    "verified": 0,
                    "still_active": 0,
                    "marked_inactive": 0,
                    "errors": 0,
                    "inactive_jobs": []  # Track jobs marked inactive
                }
                
                # Process in batches
                for i in range(0, len(jobs_to_verify), batch_size):
                    batch = jobs_to_verify[i:i + batch_size]
                    logger.info(f"Processing {src} batch {i // batch_size + 1} ({len(batch)} jobs)")
                    
                    batch_stats = await self._verify_batch(batch, source=src, run_id=run_id)
                    
                    run_stats["verified"] += batch_stats["verified"]
                    run_stats["still_active"] += batch_stats["still_active"]
                    run_stats["marked_inactive"] += batch_stats["marked_inactive"]
                    run_stats["errors"] += batch_stats["errors"]
                    run_stats["inactive_jobs"].extend(batch_stats.get("inactive_jobs", []))
                    
                    # Rate limiting: wait between batches
                    if i + batch_size < len(jobs_to_verify):
                        logger.info("Waiting 60s before next batch...")
                        await asyncio.sleep(60)
                
                # Complete run successfully
                self._complete_verification_run(run_id, run_stats)
                
                # Add to total stats
                total_stats["verified"] += run_stats["verified"]
                total_stats["still_active"] += run_stats["still_active"]
                total_stats["marked_inactive"] += run_stats["marked_inactive"]
                total_stats["errors"] += run_stats["errors"]
            
            except Exception as e:
                logger.error(f"Error in {src} verification run: {e}")
                self._fail_verification_run(run_id, str(e))
                total_stats["errors"] += 1
        
        logger.success(
            f"✅ Verification complete: {total_stats['verified']} verified, "
            f"{total_stats['still_active']} still active, "
            f"{total_stats['marked_inactive']} marked inactive, "
            f"{total_stats['errors']} errors"
        )
        
        return total_stats
    
    def _get_jobs_to_verify(
        self,
        only_data_jobs: bool = True,
        source: str = "linkedin"
    ) -> List[Dict]:
        """
        Get active jobs that need verification.
        
        Args:
            only_data_jobs: Only get jobs where title_classification = 'Data'
            source: Source platform ('linkedin' or 'indeed')
        
        Returns:
            List of job dictionaries with id, source_job_id, url, title, source
        """
        # Get job IDs that have this source via job_sources bridge table
        source_rows = db.client.table("job_sources")\
            .select("job_posting_id, source_job_id")\
            .eq("source", source)\
            .execute()
        source_rows = source_rows.data or []
        if not source_rows:
            return []
        
        job_id_to_source_id = {
            row["job_posting_id"]: row.get("source_job_id")
            for row in source_rows if row.get("job_posting_id")
        }
        job_ids = list(job_id_to_source_id.keys())
        if not job_ids:
            return []
        
        jobs: List[Dict] = []
        chunk_size = 200
        for i in range(0, len(job_ids), chunk_size):
            chunk = job_ids[i:i + chunk_size]
            query = db.client.table("job_postings")\
                .select("id, job_url, apply_url, title, title_classification, source, is_active, job_sources(source, source_job_id, last_seen_at)")\
                .in_("id", chunk)\
                .eq("is_active", True)
            if only_data_jobs:
                query = query.eq("title_classification", "Data")
            chunk_result = query.execute()
            for job in chunk_result.data or []:
                source_job_id = job_id_to_source_id.get(job["id"])
                if not source_job_id:
                    continue
                raw_url = job.get("job_url") or job.get("apply_url")
                normalized_url = self._normalize_job_url(raw_url)
                if not normalized_url:
                    continue
                jobs.append({
                    "id": job["id"],
                    "source_job_id": source_job_id,
                    "title": job.get("title"),
                    "title_classification": job.get("title_classification"),
                    "source": source,
                    "job_url": job.get("job_url"),
                    "apply_url": job.get("apply_url"),
                    "url": normalized_url,
                    "all_sources": job.get("job_sources") or []
                })
        
        return jobs

    def _normalize_job_url(self, url: Optional[str]) -> Optional[str]:
        """Strip unsupported LinkedIn query params keeping only `_l` if present."""
        if not url:
            return None

        try:
            parsed = urlparse(url)
            if not parsed.query:
                return url

            params = parse_qsl(parsed.query, keep_blank_values=True)
            filtered = [(k, v) for k, v in params if k == "_l"]

            new_query = urlencode(filtered, doseq=True)
            normalized = parsed._replace(query=new_query)
            normalized_url = urlunparse(normalized)
            if normalized_url != url:
                logger.debug(f"Normalized job URL: {url} -> {normalized_url}")
            return normalized_url
        except Exception:
            return url
    
    async def _verify_batch(
        self,
        jobs: List[Dict],
        source: str = "linkedin",
        run_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Verify a batch of jobs via Bright Data API.
        
        Args:
            jobs: List of job dictionaries
            source: Source platform ('linkedin' or 'indeed')
        
        Returns:
            Dictionary with batch statistics
        """
        stats = {
            "verified": 0,
            "still_active": 0,
            "marked_inactive": 0,
            "errors": 0,
            "inactive_jobs": []  # Track jobs marked inactive in this batch
        }
        
        # Prepare URLs for Bright Data
        urls = [job["url"] for job in jobs if job.get("url")]
        if urls:
            logger.debug(
                f"Prepared {len(urls)} {source} URLs for verification (sample: {urls[:3]})"
            )
        
        if not urls:
            logger.warning("No valid URLs in batch")
            return stats
        
        try:
            # Call Bright Data API to fetch job data by URL
            logger.info(f"Fetching {len(urls)} {source} job URLs from Bright Data...")
            results = await self._fetch_jobs_by_url(urls, source=source)
            
            # Safety check: If API returns no results at all, something is wrong
            # Don't mark jobs as inactive in this case
            if not results or len(results) == 0:
                logger.error(f"⚠️ Bright Data API returned 0 results for {len(urls)} URLs - skipping batch to avoid false negatives")
                stats["errors"] += len(jobs)
                return stats
            
            # Additional safety: If we get less than 10% of expected results, log warning
            if len(results) < len(urls) * 0.1:
                logger.warning(f"⚠️ Only got {len(results)} results for {len(urls)} URLs ({len(results)/len(urls)*100:.1f}%) - API may be having issues")
            
            # Create lookup map: source_job_id -> job data
            # LinkedIn uses 'job_posting_id', Indeed uses 'jobid'
            results_map = {}
            for result in results:
                if source == "linkedin":
                    job_id = result.get("job_posting_id")
                elif source == "indeed":
                    job_id = result.get("jobid")
                else:
                    job_id = None
                
                if job_id:
                    results_map[job_id] = result
            
            # Check each job
            for job in jobs:
                stats["verified"] += 1
                source_job_id = job.get("source_job_id")
                
                if not source_job_id:
                    stats["errors"] += 1
                    continue
                
                # Check if job was found in API results
                if source_job_id in results_map:
                    api_job = results_map[source_job_id]
                    
                    # Job still exists if it has a title
                    if api_job.get("job_title"):
                        db.update_job_posting(UUID(job["id"]), {
                            "last_seen_at": datetime.utcnow().isoformat()
                        })
                        self._update_source_last_seen(job["id"], source)
                        stats["still_active"] += 1
                        logger.debug(f"✅ {source.upper()} job still active: {job['title']}")
                    else:
                        # Job exists but no title = likely removed
                        stats["marked_inactive"] += 1
                        db.mark_jobs_inactive([UUID(job["id"])])
                        stats["inactive_jobs"].append({
                            "job_id": job["id"],
                            "title": job["title"],
                            "reason": "no_title"
                        })
                        logger.info(f"❌ {source.upper()} job inactive (no title): {job['title']}")
                else:
                    if self._has_recent_alternative_source(job, source):
                        stats["still_active"] += 1
                        logger.info(
                            f"🔁 Skipping inactive mark for {job['title']} because alternate source is still active"
                        )
                        continue
                    # Job not found in API results = removed
                    stats["marked_inactive"] += 1
                    db.mark_jobs_inactive([UUID(job["id"])])
                    stats["inactive_jobs"].append({
                        "job_id": job["id"],
                        "title": job["title"],
                        "reason": "not_found"
                    })
                    logger.info(f"❌ {source.upper()} job inactive (not found): {job['title']}")
        
        except Exception as e:
            logger.error(f"Error verifying {source} batch: {e}")
            stats["errors"] += len(jobs)
        
        return stats
    
    async def _fetch_jobs_by_url(
        self,
        urls: List[str],
        source: str = "linkedin"
    ) -> List[Dict]:
        """
        Fetch job data from Bright Data API by URLs.
        
        Args:
            urls: List of job URLs
            source: Source platform ('linkedin' or 'indeed')
        
        Returns:
            List of job data dictionaries
        """
        try:
            # Select appropriate client based on source
            if source == "linkedin":
                return await self.linkedin_client.fetch_jobs_by_urls(urls)
            elif source == "indeed":
                return await self.indeed_client.fetch_jobs_by_urls(urls)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Unreachable but keeps structure consistent for future sources
            results = []
            if results:
                sample_ids = []
                for item in results[:5]:
                    if source == "linkedin":
                        sample_ids.append(item.get("job_posting_id"))
                    elif source == "indeed":
                        sample_ids.append(item.get("jobid"))
                logger.debug(
                    f"Bright Data returned {len(results)} {source} results (sample IDs: {sample_ids})"
                )
            else:
                logger.debug(f"Bright Data returned 0 {source} results for URLs: {urls[:3]}")
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching {source} jobs by URL: {e}")
            return []

    def _update_source_last_seen(self, job_id: str, source: str):
        try:
            db.client.table("job_sources")\
                .update({"last_seen_at": datetime.utcnow().isoformat()})\
                .eq("job_posting_id", job_id)\
                .eq("source", source)\
                .execute()
        except Exception as e:
            logger.warning(f"Failed to update last_seen for job {job_id} source {source}: {e}")

    def _has_recent_alternative_source(self, job: Dict, current_source: str) -> bool:
        sources = job.get("all_sources") or []
        if not sources:
            return False
        threshold = datetime.utcnow() - timedelta(days=ALT_SOURCE_GRACE_DAYS)
        for src in sources:
            if src.get("source") == current_source:
                continue
            last_seen = src.get("last_seen_at")
            if not last_seen:
                continue
            try:
                parsed = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            except Exception:
                continue
            if parsed >= threshold:
                return True
        return False
    
    async def verify_single_job(self, job_id: UUID) -> Tuple[bool, Optional[str]]:
        """
        Verify a single job by its ID.
        
        Args:
            job_id: Job posting UUID
        
        Returns:
            Tuple of (is_active, error_message)
        """
        # Get job from database
        result = db.client.table("job_postings")\
            .select("id, linkedin_job_id, url, title")\
            .eq("id", str(job_id))\
            .single()\
            .execute()
        
        if not result.data:
            return False, "Job not found"
        
        job = result.data
        
        if not job.get("url"):
            return False, "Job has no URL"
        
        try:
            # Verify via API
            results = await self._fetch_jobs_by_url([job["url"]])
            
            if results and len(results) > 0:
                api_job = results[0]
                
                if api_job.get("job_title"):
                    # Job still exists
                    db.update_job_posting(job_id, {
                        "last_seen_at": datetime.utcnow().isoformat()
                    })
                    return True, None
                else:
                    # Job exists but no title
                    db.mark_jobs_inactive([job_id])
                    return False, "Job has no title (likely removed)"
            else:
                # Job not found
                db.mark_jobs_inactive([job_id])
                return False, "Job not found in API"
        
        except Exception as e:
            logger.error(f"Error verifying job {job_id}: {e}")
            return False, str(e)


    def _create_verification_run(
        self,
        source: str,
        batch_size: int,
        only_data_jobs: bool,
        trigger_type: str
    ) -> str:
        """Create a new verification run record in database."""
        result = db.client.table("job_verification_runs").insert({
            "source": source,
            "batch_size": batch_size,
            "only_data_jobs": only_data_jobs,
            "trigger_type": trigger_type,
            "status": "running"
        }).execute()
        
        run_id = result.data[0]["id"]
        logger.info(f"Created verification run: {run_id}")
        return run_id
    
    def _complete_verification_run(self, run_id: str, stats: Dict):
        """Mark verification run as completed with stats."""
        db.client.table("job_verification_runs").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "jobs_checked": stats["verified"],
            "jobs_still_active": stats["still_active"],
            "jobs_marked_inactive": stats["marked_inactive"],
            "jobs_errors": stats["errors"]
        }).eq("id", run_id).execute()
        
        # Log inactive jobs
        inactive_jobs = stats.get("inactive_jobs", [])
        if inactive_jobs:
            for job_info in inactive_jobs:
                # Get full job details
                job_result = db.client.table("job_postings")\
                    .select("id, title, url, source, companies(name)")\
                    .eq("id", job_info["job_id"])\
                    .single()\
                    .execute()
                
                if job_result.data:
                    job = job_result.data
                    db.client.table("job_verification_inactive_jobs").insert({
                        "verification_run_id": run_id,
                        "job_posting_id": job["id"],
                        "job_title": job.get("title"),
                        "company_name": job.get("companies", {}).get("name") if job.get("companies") else None,
                        "source": job.get("source"),
                        "url": job.get("url"),
                        "reason": job_info["reason"]
                    }).execute()
        
        logger.info(f"Completed verification run: {run_id}")
    
    def _fail_verification_run(self, run_id: str, error_message: str):
        """Mark verification run as failed."""
        db.client.table("job_verification_runs").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": error_message
        }).eq("id", run_id).execute()
        
        logger.error(f"Failed verification run: {run_id} - {error_message}")


# Global service instance
_verification_service: Optional[JobVerificationService] = None


def get_verification_service() -> JobVerificationService:
    """Get or create the global verification service instance."""
    global _verification_service
    if _verification_service is None:
        _verification_service = JobVerificationService()
    return _verification_service
