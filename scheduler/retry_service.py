"""
Retry Service - Automatically retries failed scrape runs
Runs every 30 minutes to check for pending retries
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict
from loguru import logger

from database.client import db


class RetryService:
    """Service that automatically retries failed scrape runs."""
    
    def __init__(self, check_interval: int = 1800):  # 30 minutes
        """
        Initialize the retry service.
        
        Args:
            check_interval: Seconds between retry checks (default 1800 = 30 min)
        """
        self.check_interval = check_interval
        self.running = False
        
    async def start(self):
        """Start the retry service loop."""
        self.running = True
        logger.info("🔄 Retry Service started")
        logger.info(f"   Check interval: {self.check_interval}s ({self.check_interval/60:.0f} minutes)")
        
        while self.running:
            try:
                await self.process_pending_retries()
            except Exception as e:
                logger.error(f"Error in retry service: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    async def process_pending_retries(self):
        """Find and execute runs that are ready for retry."""
        now = datetime.now(timezone.utc)
        
        # Find runs that are ready for retry
        result = db.client.table("scrape_runs")\
            .select("id, query_id, search_query, location_query, retry_count, max_retries, original_run_id")\
            .eq("status", "pending_retry")\
            .lte("next_retry_at", now.isoformat())\
            .execute()
        
        if not result.data:
            logger.debug("No runs ready for retry")
            return
        
        runs_to_retry = result.data
        logger.info(f"🔄 Found {len(runs_to_retry)} runs ready for retry")
        
        for run in runs_to_retry:
            await self.execute_retry(run)
    
    async def execute_retry(self, run: Dict):
        """
        Execute a retry for a specific run.
        
        Args:
            run: Run data from database
        """
        run_id = run['id']
        query_id = run.get('query_id')
        query = run['search_query']
        location = run['location_query']
        retry_count = run.get('retry_count', 0)
        max_retries = run.get('max_retries', 4)
        original_run_id = run.get('original_run_id')
        
        logger.info(f"🔄 Executing retry {retry_count}/{max_retries}: {query} in {location}")
        
        try:
            # Import here to avoid circular dependency
            from scraper import execute_scrape_run
            
            # Update status to 'running'
            db.client.table("scrape_runs")\
                .update({
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "next_retry_at": None
                })\
                .eq("id", run_id)\
                .execute()
            
            # Execute the scrape run
            logger.info(f"   Starting scrape for retry {retry_count}/{max_retries}")
            
            # Get query details if we have query_id
            if query_id:
                query_result = db.client.table("scrape_queries")\
                    .select("*")\
                    .eq("id", query_id)\
                    .single()\
                    .execute()
                
                if query_result.data:
                    query_data = query_result.data
                    # Execute the scrape with the query data
                    await execute_scrape_run(
                        run_id=run_id,
                        query_id=query_id,
                        search_query=query,
                        location_query=location,
                        query_type=query_data.get('query_type', 'Data'),
                        source=query_data.get('source', 'indeed')
                    )
                    logger.success(f"✅ Retry {retry_count}/{max_retries} completed successfully")
                else:
                    raise Exception(f"Query {query_id} not found")
            else:
                # No query_id, just execute with basic params
                await execute_scrape_run(
                    run_id=run_id,
                    query_id=None,
                    search_query=query,
                    location_query=location,
                    query_type='Data',
                    source='indeed'
                )
                logger.success(f"✅ Retry {retry_count}/{max_retries} completed successfully")
                
        except Exception as e:
            logger.error(f"❌ Retry {retry_count}/{max_retries} failed: {e}")
            
            # Mark as failed
            db.client.table("scrape_runs")\
                .update({
                    "status": "failed",
                    "error_message": f"Retry {retry_count}/{max_retries} failed: {str(e)}",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", run_id)\
                .execute()
    
    def stop(self):
        """Stop the retry service."""
        logger.info("🛑 Stopping Retry Service...")
        self.running = False


# Global service instance
_retry_service = None


def get_retry_service() -> RetryService:
    """Get or create the global retry service instance."""
    global _retry_service
    if _retry_service is None:
        _retry_service = RetryService()
    return _retry_service


async def start_retry_service():
    """Start the retry service (convenience function)."""
    service = get_retry_service()
    await service.start()


if __name__ == "__main__":
    # Run the service standalone
    asyncio.run(start_retry_service())
