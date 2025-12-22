"""Scheduler service using APScheduler for automated scrape runs."""

import asyncio
from datetime import datetime, time, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from database import db
from scraper import execute_scrape_run
from scheduler.retry_service import get_retry_service
from services.similar_jobs import get_similar_jobs_service


class SchedulerService:
    """Service for managing scheduled scrape runs."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("📅 Scheduler started")
            
            # Add stuck run checker (runs every hour)
            self.scheduler.add_job(
                self._check_stuck_runs,
                trigger=IntervalTrigger(hours=1),
                id="stuck_run_checker",
                replace_existing=True
            )
            logger.info("🔍 Stuck run checker scheduled (every 1 hour)")
            
            # Add retry processor (runs every 30 minutes)
            self.scheduler.add_job(
                self._process_retries,
                trigger=IntervalTrigger(minutes=30),
                id="retry_processor",
                replace_existing=True
            )
            logger.info("🔄 Retry processor scheduled (every 30 minutes)")
            
            # Add job verification (runs weekly on Saturday at 10:00 AM)
            self.scheduler.add_job(
                self._verify_active_jobs,
                trigger=CronTrigger(day_of_week='sat', hour=10, minute=0),
                id="job_verifier",
                replace_existing=True
            )
            logger.info("✅ Job verification scheduled (weekly on Saturday at 10:00 AM)")

            # Add similar job recompute (nightly at 02:00 AM)
            self.scheduler.add_job(
                self._refresh_similar_jobs,
                trigger=CronTrigger(hour=2, minute=0),
                id="similar_job_refresher",
                replace_existing=True
            )
            logger.info("🤝 Similar job refresher scheduled (daily at 02:00 AM)")
            
            # Add location enrichment (daily at 05:30 AM)
            self.scheduler.add_job(
                self._enrich_unenriched_locations,
                trigger=CronTrigger(hour=5, minute=30),
                id="location_enricher",
                replace_existing=True
            )
            logger.info("🌍 Location enrichment scheduled (daily at 05:30 AM)")
            
            # Load and schedule all active queries
            self._load_scheduled_queries()
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("📅 Scheduler stopped")
    
    def _load_scheduled_queries(self):
        """Load all scheduled queries from database and add them to scheduler."""
        try:
            queries = db.client.table("search_queries")\
                .select("*")\
                .eq("is_active", True)\
                .eq("schedule_enabled", True)\
                .execute()
            
            if not queries.data:
                logger.info("No scheduled queries found")
                return
            
            for query in queries.data:
                self.schedule_query(query)
            
            logger.info(f"Loaded {len(queries.data)} scheduled queries")
        except Exception as e:
            logger.error(f"Failed to load scheduled queries: {e}")
    
    def schedule_query(self, query: dict):
        """
        Add a query to the scheduler.
        
        Args:
            query: Query dict with schedule configuration
        """
        query_id = query["id"]
        search_query = query["search_query"]
        location_query = query["location_query"]
        schedule_type = query.get("schedule_type")
        source = query.get("source", "linkedin")  # Get source from query
        
        # Remove existing job if any
        self.unschedule_query(query_id)
        
        # Create trigger based on schedule type
        trigger = None
        
        if schedule_type == "daily":
            # Daily at specific time
            schedule_time = query.get("schedule_time")
            if schedule_time:
                # Parse time string (HH:MM:SS)
                hour, minute = schedule_time.split(":")[:2]
                trigger = CronTrigger(hour=int(hour), minute=int(minute))
                logger.info(f"Scheduled '{search_query}' in '{location_query}' daily at {schedule_time}")
        
        elif schedule_type == "interval":
            # Every X hours
            interval_hours = query.get("schedule_interval_hours", 6)
            trigger = IntervalTrigger(hours=interval_hours)
            logger.info(f"Scheduled '{search_query}' in '{location_query}' every {interval_hours} hours")
        
        elif schedule_type == "weekly":
            # Specific days of week
            days_of_week = query.get("schedule_days_of_week", [])
            schedule_time = query.get("schedule_time", "09:00:00")
            hour, minute = schedule_time.split(":")[:2]
            
            # Convert day numbers to cron day_of_week format
            # APScheduler uses: mon=0, tue=1, ..., sun=6
            # Our format: sun=0, mon=1, ..., sat=6
            # Convert: our_day -> (our_day - 1) % 7
            cron_days = ",".join(str((day - 1) % 7) for day in days_of_week)
            
            trigger = CronTrigger(day_of_week=cron_days, hour=int(hour), minute=int(minute))
            logger.info(f"Scheduled '{search_query}' in '{location_query}' weekly on days {days_of_week}")
        
        if trigger:
            # Add job to scheduler
            self.scheduler.add_job(
                self._run_scheduled_scrape,
                trigger=trigger,
                args=[query_id, search_query, location_query, query.get("lookback_days", 7), query.get("job_type_id"), source],
                id=query_id,
                replace_existing=True,
                misfire_grace_time=3600  # Allow 1 hour grace period for missed runs
            )
            
            # Update next_run_at in database
            next_run = self.scheduler.get_job(query_id).next_run_time
            if next_run:
                db.client.table("search_queries")\
                    .update({"next_run_at": next_run.isoformat()})\
                    .eq("id", query_id)\
                    .execute()
    
    def unschedule_query(self, query_id: str):
        """
        Remove a query from the scheduler.
        
        Args:
            query_id: UUID of the query
        """
        try:
            self.scheduler.remove_job(query_id)
            logger.info(f"Unscheduled query {query_id}")
        except Exception:
            # Job doesn't exist, that's fine
            pass
    
    async def _run_scheduled_scrape(self, query_id: str, search_query: str, location_query: str, lookback_days: int, job_type_id: str = None, source: str = "linkedin"):
        """
        Execute a scheduled scrape run.
        
        Args:
            query_id: UUID of the search query
            search_query: Search term
            location_query: Location
            lookback_days: Days to look back
            job_type_id: Job type ID for classification
            source: Source platform ('linkedin' or 'indeed')
        """
        logger.info(f"🤖 Running scheduled {source} scrape: '{search_query}' in '{location_query}'")
        
        try:
            # Execute scrape with trigger_type='scheduled' and correct source
            result = await execute_scrape_run(
                query=search_query,
                location=location_query,
                lookback_days=lookback_days,
                trigger_type="scheduled",
                search_query_id=query_id,
                job_type_id=job_type_id,
                source=source
            )
            
            # Update last_run_at and next_run_at
            next_run = self.scheduler.get_job(query_id).next_run_time
            
            db.client.table("search_queries")\
                .update({
                    "last_run_at": datetime.utcnow().isoformat(),
                    "next_run_at": next_run.isoformat() if next_run else None
                })\
                .eq("id", query_id)\
                .execute()
            
            logger.info(f"✅ Scheduled scrape completed: {result.jobs_found} jobs found")
        except Exception as e:
            logger.error(f"❌ Scheduled scrape failed: {e}")
    
    def get_scheduled_jobs(self):
        """Get all scheduled jobs."""
        return self.scheduler.get_jobs()
    
    def get_job_info(self, query_id: str) -> Optional[dict]:
        """Get info about a scheduled job."""
        job = self.scheduler.get_job(query_id)
        if job:
            return {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
        return None
    
    async def _check_stuck_runs(self):
        """Check for stuck runs and mark them as failed if stuck for more than 2 hours."""
        logger.info("🔍 Checking for stuck runs...")
        
        try:
            # Calculate cutoff time (2 hours ago)
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            # Find stuck runs (both LinkedIn and Indeed)
            stuck_runs = db.client.table("scrape_runs")\
                .select("id, search_query, location_query, started_at, platform")\
                .eq("status", "running")\
                .lt("started_at", cutoff_time.isoformat())\
                .execute()
            
            if not stuck_runs.data:
                logger.info("✅ No stuck runs found")
                return
            
            # Mark each as failed
            cleaned_count = 0
            for run in stuck_runs.data:
                try:
                    db.client.table("scrape_runs")\
                        .update({
                            "status": "failed",
                            "completed_at": datetime.utcnow().isoformat(),
                            "error_message": "Run stuck for more than 2 hours - automatically marked as failed"
                        })\
                        .eq("id", run["id"])\
                        .execute()
                    
                    cleaned_count += 1
                    logger.warning(
                        f"⚠️ Marked stuck run as failed: {run['id']}\n"
                        f"  Query: {run.get('search_query')}\n"
                        f"  Location: {run.get('location_query')}\n"
                        f"  Platform: {run.get('platform')}\n"
                        f"  Started: {run.get('started_at')}"
                    )
                except Exception as e:
                    logger.error(f"Failed to clean up run {run['id']}: {e}")
            
            logger.success(f"✅ Cleaned up {cleaned_count} stuck runs")
        except Exception as e:
            logger.error(f"Error checking stuck runs: {e}")
    
    async def _process_retries(self):
        """Process pending retry runs."""
        logger.info("🔄 Processing pending retries...")
        
        try:
            retry_service = get_retry_service()
            await retry_service.process_pending_retries()
        except Exception as e:
            logger.error(f"Error processing retries: {e}")
    
    async def _verify_active_jobs(self):
        """Verify active LinkedIn and Indeed jobs via Bright Data API."""
        logger.info("✅ Starting scheduled job verification...")
        
        try:
            from services.job_verification import get_verification_service
            
            verification_service = get_verification_service()
            stats = await verification_service.verify_active_jobs(
                batch_size=100,
                only_data_jobs=True,  # Only verify Data jobs
                source=None,  # Verify both LinkedIn and Indeed
                trigger_type="scheduled"
            )
            
            logger.success(
                f"✅ Job verification complete: {stats['verified']} verified, "
                f"{stats['still_active']} still active, "
                f"{stats['marked_inactive']} marked inactive"
            )
        except Exception as e:
            logger.error(f"Error verifying jobs: {e}")

    async def _refresh_similar_jobs(self):
        """Nightly task to recompute similar_job_ids for active postings."""
        logger.info("🤝 Recomputing similar_job_ids for active jobs...")

        loop = asyncio.get_running_loop()
        service = get_similar_jobs_service()

        try:
            count, duration = await loop.run_in_executor(
                None, service.recompute_all_active_jobs
            )
            logger.success(
                f"🤝 Similar jobs updated for {count} jobs in {duration:.2f}s"
            )
        except Exception as exc:
            logger.error(f"Failed to refresh similar jobs: {exc}")

    async def _enrich_unenriched_locations(self):
        """Daily task to enrich locations with missing data (city names, provinces, etc.)."""
        logger.info("🌍 Starting scheduled location enrichment...")
        
        try:
            from ingestion.location_enrichment import enrich_location
            
            # Find locations that need enrichment:
            # - Missing city_name_nl, city_name_fr, city_name_en
            # - Missing subdivision_name, subdivision_name_fr, subdivision_name_en
            # - Missing country_name_nl, country_name_fr, country_name_en
            # - ai_enriched is null or false
            result = db.client.table("locations")\
                .select("id, city, country_code, region, full_location_string")\
                .or_(
                    "ai_enriched.is.null,"
                    "ai_enriched.eq.false,"
                    "city_name_nl.is.null,"
                    "city_name_fr.is.null,"
                    "city_name_en.is.null,"
                    "subdivision_name.is.null,"
                    "subdivision_name_fr.is.null,"
                    "subdivision_name_en.is.null"
                )\
                .limit(50)\
                .execute()
            
            locations = result.data if result.data else []
            
            if not locations:
                logger.info("✅ No unenriched locations found")
                return
            
            logger.info(f"🌍 Found {len(locations)} unenriched locations to process")
            
            # Enrich each location
            success_count = 0
            failed_count = 0
            
            for location in locations:
                try:
                    location_id = location["id"]
                    city = location.get("city")
                    country_code = location.get("country_code")
                    region = location.get("region")
                    full_location = location.get("full_location_string", "Unknown")
                    
                    logger.info(f"Enriching: {full_location}")
                    
                    # Enrich the location
                    enrichment_result = enrich_location(
                        location_id=location_id,
                        city=city,
                        country_code=country_code,
                        region=region
                    )
                    
                    if enrichment_result.get("success"):
                        success_count += 1
                        logger.success(f"✅ Enriched: {full_location}")
                    else:
                        failed_count += 1
                        error = enrichment_result.get("error", "Unknown error")
                        logger.warning(f"⚠️ Failed to enrich {full_location}: {error}")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to enrich location {location.get('full_location_string', 'Unknown')}: {e}")
                    continue
            
            logger.success(
                f"✅ Location enrichment complete: {success_count} enriched, {failed_count} failed"
            )
        
        except Exception as e:
            logger.error(f"Error in scheduled location enrichment: {e}")


# Global scheduler instance
_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler
