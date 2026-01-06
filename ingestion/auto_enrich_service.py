"""
Auto-enrichment service for locations, job titles, and Data jobs.
Automatically enriches new location records, classifies job titles, and enriches Data jobs in the background.
Includes automatic retry for quota errors after 24h.
"""

import asyncio
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from database.client import db
from ingestion.location_enrichment import enrich_location
from ingestion.job_title_classifier import classify_job_title
from ingestion.relevance_scorer import score_programming_language, score_ecosystem
from ingestion.llm_enrichment import process_job_enrichment
from ingestion.company_enrichment import enrich_companies_batch, get_unenriched_companies


class AutoEnrichService:
    """Service to automatically enrich new location records, classify job titles, enrich Data jobs, score tech stack relevance, and enrich companies."""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
        self.retry_check_interval = 3600  # Check for retries every hour (3600 seconds)
        self.ranking_check_interval = 3600  # Calculate rankings every hour (3600 seconds)
        self.company_check_interval = 600  # Check for companies every 10 minutes (600 seconds)
        self.cleanup_check_interval = 3600  # Cleanup stuck enrichments every hour (3600 seconds)
        self.last_retry_check = datetime.utcnow()
        self.last_ranking_check = datetime.utcnow()
        self.last_company_check = datetime.utcnow()
        self.last_cleanup_check = datetime.utcnow()
        self.company_enrichment_running = False  # Flag to prevent overlapping batches
        self.job_enrichment_running = False  # Flag to prevent overlapping job enrichment batches
    
    async def start(self):
        """Start the auto-enrichment service."""
        self.running = True
        logger.info("🤖 Auto-enrichment service started (locations + job titles + Data jobs + tech relevance + companies)")
        
        # Wait before first check to avoid blocking startup
        logger.info(f"⏳ Waiting {self.check_interval}s before first enrichment check")
        await asyncio.sleep(self.check_interval)
        
        while self.running:
            try:
                # Process all enrichment tasks
                await self.process_pending_locations()
                await self.process_pending_job_titles()
                
                # Only process jobs if not already running (prevent overlapping batches)
                if not self.job_enrichment_running:
                    await self.process_pending_data_jobs()
                else:
                    logger.warning("⚠️ Skipping job enrichment - previous batch still running")
                
                await self.process_pending_tech_scores()
                
                # Check if it's time for company enrichment (every 10 minutes)
                # Skip if previous batch is still running
                time_since_last_company = (datetime.utcnow() - self.last_company_check).total_seconds()
                if time_since_last_company >= self.company_check_interval:
                    if not self.company_enrichment_running:
                        logger.info("⏰ Running company enrichment check")
                        await self.process_pending_companies()
                        self.last_company_check = datetime.utcnow()
                    else:
                        logger.warning("⚠️ Skipping company enrichment - previous batch still running")
                
                # Check if it's time for hourly retry check
                time_since_last_retry = (datetime.utcnow() - self.last_retry_check).total_seconds()
                if time_since_last_retry >= self.retry_check_interval:
                    logger.info("⏰ Running hourly retry check for failed enrichments")
                    await self.retry_failed_enrichments()
                    self.last_retry_check = datetime.utcnow()
                
                # Check if it's time for hourly ranking calculation
                time_since_last_ranking = (datetime.utcnow() - self.last_ranking_check).total_seconds()
                if time_since_last_ranking >= self.ranking_check_interval:
                    logger.info("⏰ Running hourly ranking calculation")
                    await self.calculate_rankings()
                    self.last_ranking_check = datetime.utcnow()
                
                # Check if it's time for stuck enrichment cleanup
                time_since_last_cleanup = (datetime.utcnow() - self.last_cleanup_check).total_seconds()
                if time_since_last_cleanup >= self.cleanup_check_interval:
                    logger.info("⏰ Running stuck enrichment cleanup")
                    await self.cleanup_stuck_enrichments()
                    self.last_cleanup_check = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error in auto-enrichment service: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the auto-enrichment service."""
        self.running = False
        logger.info("🛑 Auto-enrichment service stopped")
    
    async def process_pending_locations(self):
        """Process locations that need enrichment, including retry of old quota errors."""
        try:
            # Calculate retry cutoff (24 hours ago)
            retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Find locations that need enrichment:
            # 1. Never enriched (ai_enriched is null or false) AND no error
            # 2. Has error AND error is old enough to retry (>24h)
            result = db.client.table("locations")\
                .select("id, city, country_code, region, ai_enrichment_error, ai_enriched_at")\
                .or_(
                    f"and(ai_enriched.is.null,ai_enrichment_error.is.null),"
                    f"and(ai_enriched.eq.false,ai_enrichment_error.is.null),"
                    f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{retry_cutoff})"
                )\
                .limit(10)\
                .execute()
            
            locations = result.data if result.data else []
            
            if not locations:
                return  # No pending locations
            
            # Count retries vs new
            retry_count = sum(1 for loc in locations if loc.get("ai_enrichment_error"))
            new_count = len(locations) - retry_count
            
            logger.info(f"🔄 Auto-enriching {len(locations)} locations ({new_count} new, {retry_count} retries)")
            
            # Enrich each location
            for location in locations:
                try:
                    location_id = location["id"]
                    city = location.get("city")
                    country_code = location.get("country_code")
                    region = location.get("region")
                    has_error = location.get("ai_enrichment_error")
                    
                    if has_error:
                        logger.info(f"Retrying: {city}, {country_code} (previous error)")
                    else:
                        logger.info(f"Enriching: {city}, {country_code}")
                    
                    # Enrich the location
                    enrichment_data = enrich_location(
                        location_id=location_id,
                        city=city,
                        country_code=country_code,
                        region=region
                    )
                    
                    if enrichment_data:
                        logger.success(f"✅ Auto-enriched: {city}")
                    else:
                        logger.warning(f"⚠️ Failed to auto-enrich: {city}")
                
                except Exception as e:
                    logger.error(f"Failed to enrich location {location.get('city')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending locations: {e}")
    
    async def process_pending_job_titles(self):
        """Process job titles that need classification."""
        try:
            # Find jobs that need title classification:
            # title_classification is null
            result = db.client.table("job_postings")\
                .select("id, title")\
                .is_("title_classification", "null")\
                .limit(20)\
                .execute()
            
            jobs = result.data if result.data else []
            
            if not jobs:
                return  # No pending jobs
            
            logger.info(f"🏷️  Auto-classifying {len(jobs)} job titles")
            
            # Classify each job title
            for job in jobs:
                try:
                    job_id = job["id"]
                    title = job.get("title")
                    
                    if not title:
                        logger.warning(f"Job {job_id} has no title, skipping")
                        continue
                    
                    logger.debug(f"Classifying: {title}")
                    
                    # Classify the title
                    classification, error = classify_job_title(title)
                    
                    if classification:
                        # Save classification to database
                        db.client.table("job_postings")\
                            .update({
                                "title_classification": classification
                            })\
                            .eq("id", job_id)\
                            .execute()
                        
                        logger.success(f"✅ Classified '{title}' as {classification}")
                    elif error:
                        # Save error (but don't retry - classification errors are usually permanent)
                        logger.warning(f"⚠️ Failed to classify '{title}': {error}")
                
                except Exception as e:
                    logger.error(f"Failed to classify job title '{job.get('title')}': {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending job titles: {e}")
    
    async def process_pending_data_jobs(self):
        """
        Process Data jobs that need LLM enrichment.
        Uses client-side filtering to prevent re-enrichments.
        Prevents overlapping batches with flag.
        """
        # Set flag to prevent overlapping batches
        self.job_enrichment_running = True
        start_time = datetime.utcnow()
        
        try:
            # Check if auto-enrichment is disabled via env var
            import os
            if os.getenv("DISABLE_AUTO_ENRICHMENT", "false").lower() == "true":
                logger.info("⏭️  Auto-enrichment disabled via DISABLE_AUTO_ENRICHMENT env var")
                return  # Skip auto-enrichment
            
            # OPTIMIZED: Fetch only recent Data jobs and check their enrichment status
            # This avoids fetching all jobs + all enrichments every time
            # Instead: fetch 500 recent jobs + check enrichment for those 500
            recent_jobs = db.client.table("job_postings")\
                .select("id, title")\
                .eq("title_classification", "Data")\
                .eq("is_active", True)\
                .order("posted_date", desc=True)\
                .limit(500)\
                .execute()
            
            if not recent_jobs.data:
                return  # No Data jobs
            
            # Get enrichment status for these specific jobs only
            job_ids = [j["id"] for j in recent_jobs.data]
            enrichments = db.client.table("llm_enrichment")\
                .select("job_posting_id, enrichment_completed_at")\
                .in_("job_posting_id", job_ids)\
                .execute()
            
            # Build set of enriched job IDs (only from this batch)
            enriched_ids = {
                e["job_posting_id"] 
                for e in enrichments.data 
                if e.get("enrichment_completed_at")
            }
            
            # Filter to only unenriched jobs, take first 30
            jobs = [
                {"id": j["id"], "title": j["title"]}
                for j in recent_jobs.data
                if j["id"] not in enriched_ids
            ][:30]
            
            if not jobs:
                return  # No pending Data jobs
            
            logger.info(f"🧠 Auto-enriching {len(jobs)} Data jobs with LLM (batch started at {start_time.isoformat()})")
            
            # Enrich each Data job
            for job in jobs:
                try:
                    job_id = job["id"]
                    title = job.get("title", "Unknown")
                    
                    logger.info(f"Enriching Data job: {title}")
                    
                    # Process LLM enrichment (force=False, so it won't re-enrich)
                    result = await asyncio.to_thread(
                        process_job_enrichment,
                        job_id,
                        force=False
                    )
                    
                    if result and result.get("success"):
                        if result.get("skipped"):
                            logger.debug(f"⏭️  Skipped (already enriched): {title}")
                        else:
                            logger.success(f"✅ Auto-enriched Data job: {title}")
                    else:
                        logger.warning(f"⚠️ Failed to auto-enrich Data job: {title}")
                    
                    # Small delay between jobs to avoid rate limiting (reduced from 2s to 1s)
                    await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"Failed to enrich Data job '{job.get('title')}': {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending Data jobs (check query size): {e}")
        
        finally:
            # Always clear the flag when done (CRITICAL for preventing stuck state)
            self.job_enrichment_running = False
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"🔓 Job enrichment batch complete in {duration:.1f}s, flag cleared")
    
    async def cleanup_stuck_enrichments(self):
        """
        Clean up stuck enrichment records for active Data jobs.
        Removes records that are >1 hour old with no completed_at and no error.
        This prevents jobs from being permanently blocked.
        """
        try:
            from datetime import timedelta
            
            # Define cutoff: 1 hour ago
            cutoff = datetime.utcnow() - timedelta(hours=1)
            cutoff_str = cutoff.isoformat()
            
            # Find stuck enrichment records for active Data jobs
            stuck = db.client.table("llm_enrichment")\
                .select("id, job_posting_id, job_postings!inner(title_classification, is_active)")\
                .eq("job_postings.title_classification", "Data")\
                .eq("job_postings.is_active", True)\
                .is_("enrichment_completed_at", "null")\
                .is_("enrichment_error", "null")\
                .lt("created_at", cutoff_str)\
                .execute()
            
            if not stuck.data:
                logger.debug("No stuck enrichments found")
                return
            
            logger.warning(f"Found {len(stuck.data)} stuck enrichment records, cleaning up...")
            
            # Delete stuck records
            deleted_count = 0
            for e in stuck.data:
                try:
                    db.client.table("llm_enrichment")\
                        .delete()\
                        .eq("id", e["id"])\
                        .execute()
                    deleted_count += 1
                except Exception as ex:
                    logger.error(f"Failed to delete stuck enrichment {e['id']}: {ex}")
            
            logger.success(f"✅ Cleaned up {deleted_count} stuck enrichment records")
        
        except Exception as e:
            logger.error(f"Failed to cleanup stuck enrichments: {e}")
    
    async def process_pending_tech_scores(self):
        """Process programming languages and ecosystems that need relevance scoring."""
        try:
            # Find programming languages without relevance_score
            languages_result = db.client.table("programming_languages")\
                .select("id, name")\
                .is_("relevance_score", "null")\
                .limit(10)\
                .execute()
            
            languages = languages_result.data if languages_result.data else []
            
            # Find ecosystems without relevance_score
            ecosystems_result = db.client.table("ecosystems")\
                .select("id, name")\
                .is_("relevance_score", "null")\
                .limit(10)\
                .execute()
            
            ecosystems = ecosystems_result.data if ecosystems_result.data else []
            
            total = len(languages) + len(ecosystems)
            
            if total == 0:
                return  # Nothing to score
            
            logger.info(f"📊 Auto-scoring {len(languages)} languages + {len(ecosystems)} ecosystems")
            
            # Score programming languages
            for lang in languages:
                try:
                    lang_id = lang["id"]
                    name = lang.get("name")
                    
                    if not name:
                        logger.warning(f"Language {lang_id} has no name, skipping")
                        continue
                    
                    logger.debug(f"Scoring language: {name}")
                    score_programming_language(lang_id, name)
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to score language '{lang.get('name')}': {e}")
                    continue
            
            # Score ecosystems
            for eco in ecosystems:
                try:
                    eco_id = eco["id"]
                    name = eco.get("name")
                    
                    if not name:
                        logger.warning(f"Ecosystem {eco_id} has no name, skipping")
                        continue
                    
                    logger.debug(f"Scoring ecosystem: {name}")
                    score_ecosystem(eco_id, name)
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to score ecosystem '{eco.get('name')}': {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending tech items: {e}")
    
    async def retry_failed_enrichments(self):
        """
        Retry enrichments for Data jobs with empty AI column (no type_datarol).
        This runs every hour to catch failed enrichments.
        
        DISABLED: This was causing infinite re-enrichments of jobs with NULL type_datarol.
        """
        logger.info("⏭️  Retry failed enrichments DISABLED - skipping")
        return  # DISABLED to prevent infinite re-enrichments
        
        try:
            logger.info("🔄 Checking for Data jobs with empty AI column...")
            
            # Find Data jobs with enrichment records but no type_datarol (empty AI column)
            result = db.client.table("llm_enrichment")\
                .select("job_posting_id, enrichment_error, job_postings!inner(title, title_classification)")\
                .eq("job_postings.title_classification", "Data")\
                .is_("type_datarol", "null")\
                .limit(50)\
                .execute()
            
            jobs = result.data if result.data else []
            
            if not jobs:
                logger.info("✅ No Data jobs with empty AI column found")
                return
            
            logger.info(f"🔄 Found {len(jobs)} Data jobs with empty AI column - retrying enrichment")
            
            # Retry enrichment for each job
            retry_count = 0
            for job in jobs:
                try:
                    job_id = job["job_posting_id"]
                    title = job.get("job_postings", {}).get("title", "Unknown")
                    error = job.get("enrichment_error")
                    
                    if error:
                        logger.info(f"Retrying (had error): {title}")
                    else:
                        logger.info(f"Retrying (incomplete): {title}")
                    
                    # Force re-enrichment
                    success = await asyncio.to_thread(
                        process_job_enrichment,
                        job_id,
                        force=True  # Force re-enrichment
                    )
                    
                    if success:
                        retry_count += 1
                        logger.success(f"✅ Retry successful: {title}")
                    else:
                        logger.warning(f"⚠️ Retry failed: {title}")
                    
                    # Delay between retries
                    await asyncio.sleep(2)
                
                except Exception as e:
                    logger.error(f"Failed to retry enrichment for job: {e}")
                    continue
            
            logger.info(f"✅ Retry complete: {retry_count}/{len(jobs)} successful")
        
        except Exception as e:
            logger.error(f"Failed to retry failed enrichments: {e}")
    
    async def process_pending_companies(self):
        """
        Process companies that need enrichment.
        Runs every 10 minutes and processes up to 3 companies per batch.
        Each company takes ~2 minutes + 3s delay = ~2.05 min per company.
        3 companies × 2.05 min = ~6 minutes (safe margin for 10 min interval).
        Includes automatic retry for quota errors after 24h.
        """
        # Check if already running (safety check)
        if self.company_enrichment_running:
            logger.warning("⚠️ Company enrichment already running, skipping this cycle")
            return
        
        # Set flag to prevent overlapping batches
        self.company_enrichment_running = True
        start_time = datetime.utcnow()
        logger.info(f"🏢 Starting company enrichment batch at {start_time.isoformat()}")
        
        try:
            # Get unenriched companies
            # TEMPORARILY DISABLED RETRIES to stop infinite enrichment loop
            # TODO: Re-enable retries once LLM output issues are resolved
            # Query limit is high (1000) to find all pending companies
            # But we only process 3 at a time (3 × 2min = 6min, safe for 10min interval)
            company_ids = await asyncio.to_thread(
                get_unenriched_companies,
                limit=1000,  # Query limit: check up to 1000 companies
                include_retries=False  # DISABLED: was causing infinite retry loops
            )
            
            # Process up to 3 companies per batch (safe for 10min interval)
            if len(company_ids) > 3:
                logger.info(f"Found {len(company_ids)} pending companies, processing first 3")
                company_ids = company_ids[:3]
            
            if not company_ids:
                logger.debug("No pending companies to enrich")
                return  # No pending companies
            
            logger.info(f"🏢 Auto-enriching {len(company_ids)} companies (estimated time: {len(company_ids) * 2} minutes)...")
            
            # Run enrichment in thread to avoid blocking
            stats = await asyncio.to_thread(
                enrich_companies_batch,
                company_ids,
                max_companies=3  # Keep at 3 for stability
            )
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.success(
                f"✅ Company enrichment batch complete in {duration:.1f}s: "
                f"{stats['successful']}/{stats['total']} successful, "
                f"{stats['failed']} failed"
            )
            
            # If there were failures, log them
            if stats['failed'] > 0 and stats.get('errors'):
                logger.warning(f"Errors: {stats['errors'][:3]}")  # Show first 3 errors
        
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Failed to process pending companies after {duration:.1f}s: {e}")
            # Log full traceback for debugging
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        finally:
            # Always clear the flag when done (CRITICAL for preventing stuck state)
            self.company_enrichment_running = False
            logger.info(f"🔓 Company enrichment flag cleared, ready for next batch")
    
    async def calculate_rankings(self):
        """
        Calculate rankings for ALL enriched Data jobs.
        Runs every hour to update rankings with fresh hourly variance.
        
        Non-enriched jobs get very high rank numbers (bottom of list).
        """
        try:
            from ranking.job_ranker import calculate_and_save_rankings
            
            logger.info("📊 Running hourly ranking calculation for ALL enriched Data jobs...")
            logger.info("   This includes hourly variance for dynamic rankings")
            
            # Run ranking calculation in thread to avoid blocking
            # This will rank ALL active Data jobs (enriched + non-enriched)
            # Non-enriched jobs will rank low due to missing data
            num_ranked = await asyncio.to_thread(calculate_and_save_rankings)
            
            logger.success(f"✅ Ranked {num_ranked} jobs successfully (hourly refresh)")
        
        except Exception as e:
            logger.error(f"Failed to calculate rankings: {e}")


# Global service instance
_auto_enrich_service: Optional[AutoEnrichService] = None


def get_auto_enrich_service() -> AutoEnrichService:
    """Get or create the auto-enrichment service instance."""
    global _auto_enrich_service
    if _auto_enrich_service is None:
        _auto_enrich_service = AutoEnrichService()
    return _auto_enrich_service
