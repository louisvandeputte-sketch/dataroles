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


# Global scheduler instance
_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler
