"""LinkedIn Job Verification Service.

Verifies if active LinkedIn jobs still exist by checking their URLs via Bright Data API.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from loguru import logger

from database.client import db
from clients.brightdata_linkedin import BrightDataLinkedInClient
from clients.brightdata_indeed import BrightDataIndeedClient
from config.settings import settings


class JobVerificationService:
    """Service for verifying if LinkedIn and Indeed jobs are still active."""
    
    def __init__(self):
        """Initialize the verification service."""
        self.linkedin_client = BrightDataLinkedInClient(
            api_token=settings.BRIGHTDATA_API_TOKEN,
            dataset_id=settings.BRIGHTDATA_LINKEDIN_DATASET_ID
        )
        self.indeed_client = BrightDataIndeedClient(
            api_token=settings.BRIGHTDATA_API_TOKEN,
            dataset_id=settings.BRIGHTDATA_INDEED_DATASET_ID
        )
    
    async def verify_active_jobs(
        self,
        batch_size: int = 100,
        only_data_jobs: bool = True,
        source: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Verify all active jobs by checking if they still exist.
        
        Args:
            batch_size: Number of jobs to verify per batch
            only_data_jobs: Only verify jobs where title_classification = 'Data'
            source: Filter by source ('linkedin', 'indeed', or None for both)
        
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
            jobs_to_verify = self._get_jobs_to_verify(
                only_data_jobs=only_data_jobs,
                source=src
            )
        
            if not jobs_to_verify:
                logger.info(f"No {src} jobs to verify")
                continue
            
            logger.info(f"Found {len(jobs_to_verify)} {src} jobs to verify")
            
            # Process in batches
            for i in range(0, len(jobs_to_verify), batch_size):
                batch = jobs_to_verify[i:i + batch_size]
                logger.info(f"Processing {src} batch {i // batch_size + 1} ({len(batch)} jobs)")
                
                batch_stats = await self._verify_batch(batch, source=src)
                
                total_stats["verified"] += batch_stats["verified"]
                total_stats["still_active"] += batch_stats["still_active"]
                total_stats["marked_inactive"] += batch_stats["marked_inactive"]
                total_stats["errors"] += batch_stats["errors"]
                
                # Rate limiting: wait between batches
                if i + batch_size < len(jobs_to_verify):
                    logger.info("Waiting 60s before next batch...")
                    await asyncio.sleep(60)
        
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
        # Select appropriate ID field based on source
        if source == "linkedin":
            id_field = "linkedin_job_id"
        elif source == "indeed":
            id_field = "indeed_job_id"
        else:
            raise ValueError(f"Unsupported source: {source}")
        
        query = db.client.table("job_postings")\
            .select(f"id, {id_field}, url, title, title_classification, source")\
            .eq("is_active", True)\
            .eq("source", source)\
            .not_.is_(id_field, "null")
        
        if only_data_jobs:
            query = query.eq("title_classification", "Data")
        
        result = query.execute()
        
        # Normalize the response to have consistent 'source_job_id' field
        jobs = result.data or []
        for job in jobs:
            job["source_job_id"] = job.get(id_field)
        
        return jobs
    
    async def _verify_batch(
        self,
        jobs: List[Dict],
        source: str = "linkedin"
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
            "errors": 0
        }
        
        # Prepare URLs for Bright Data
        urls = [job["url"] for job in jobs if job.get("url")]
        
        if not urls:
            logger.warning("No valid URLs in batch")
            return stats
        
        try:
            # Call Bright Data API to fetch job data by URL
            logger.info(f"Fetching {len(urls)} {source} job URLs from Bright Data...")
            results = await self._fetch_jobs_by_url(urls, source=source)
            
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
                        stats["still_active"] += 1
                        # Update last_seen_at
                        db.update_job_posting(UUID(job["id"]), {
                            "last_seen_at": datetime.utcnow().isoformat()
                        })
                        logger.debug(f"✅ {source.upper()} job still active: {job['title']}")
                    else:
                        # Job exists but no title = likely removed
                        stats["marked_inactive"] += 1
                        db.mark_jobs_inactive([UUID(job["id"])])
                        logger.info(f"❌ {source.upper()} job inactive (no title): {job['title']}")
                else:
                    # Job not found in API results = removed
                    stats["marked_inactive"] += 1
                    db.mark_jobs_inactive([UUID(job["id"])])
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
                client = self.linkedin_client
            elif source == "indeed":
                client = self.indeed_client
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Trigger collection with URLs
            snapshot_id = await client.trigger_collection_by_urls(urls)
            
            # Wait for results
            results = await client.get_snapshot_data(snapshot_id)
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching {source} jobs by URL: {e}")
            return []
    
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


# Global service instance
_verification_service: Optional[JobVerificationService] = None


def get_verification_service() -> JobVerificationService:
    """Get or create the global verification service instance."""
    global _verification_service
    if _verification_service is None:
        _verification_service = JobVerificationService()
    return _verification_service
