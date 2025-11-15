"""Scrape orchestrator for coordinating complete scrape runs."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from loguru import logger

from database.client import db
from clients import get_client
from scraper.date_strategy import determine_date_range
from ingestion.processor import process_jobs_batch, BatchResult


class ScrapeRunResult:
    """Result of a complete scrape run."""
    
    def __init__(
        self,
        run_id: UUID,
        query: str,
        location: str,
        status: str,
        jobs_found: int,
        jobs_new: int,
        jobs_updated: int,
        duration_seconds: float,
        snapshot_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.run_id = run_id
        self.query = query
        self.location = location
        self.status = status
        self.jobs_found = jobs_found
        self.jobs_new = jobs_new
        self.jobs_updated = jobs_updated
        self.duration_seconds = duration_seconds
        self.snapshot_id = snapshot_id
        self.error = error
    
    def summary(self) -> str:
        """Get summary string of scrape run."""
        if self.status == 'completed':
            return (
                f"Scrape completed: {self.query} in {self.location}\n"
                f"  Jobs found: {self.jobs_found}\n"
                f"  New: {self.jobs_new}\n"
                f"  Updated: {self.jobs_updated}\n"
                f"  Duration: {self.duration_seconds:.1f}s"
            )
        else:
            return f"Scrape failed: {self.error}"


async def execute_scrape_run(
    query: str,
    location: str,
    lookback_days: Optional[int] = None,
    trigger_type: str = "manual",
    search_query_id: Optional[str] = None,
    job_type_id: Optional[str] = None,
    source: str = "linkedin"
) -> ScrapeRunResult:
    """
    Execute a complete scrape run for one query+location combination.
    
    Workflow:
    1. Determine date range for incremental scraping
    2. Create scrape_run record (status='running')
    3. Trigger Bright Data collection
    4. Wait for completion (poll with progress logging)
    5. Process all jobs through ingestion pipeline
    6. Update scrape_run with results
    7. Assign job types to found jobs
    8. Return summary
    
    Args:
        query: Search keyword (e.g., "Data Engineer")
        location: Location filter (e.g., "België")
        lookback_days: Optional manual override for lookback period
        trigger_type: How the scrape was triggered ('manual', 'scheduled', 'api')
        search_query_id: Optional UUID of the search_query record
        job_type_id: Optional UUID of the job type for classification
        source: Job source - "linkedin" or "indeed"
    
    Returns:
        ScrapeRunResult with counts and timing
    """
    start_time = datetime.utcnow()
    
    logger.info(f"=== Starting {source} scrape run: '{query}' in '{location}' (type: {job_type_id or 'none'}) ===")
    
    # Step 1: Determine date range
    date_range, expected_lookback = determine_date_range(query, location, lookback_days)
    logger.info(f"Using date range: {date_range} (lookback: {expected_lookback} days)")
    
    # Step 2: Create scrape_run record
    platform = f"{source}_brightdata"
    run_data = {
        "search_query": query,
        "location_query": location,
        "platform": platform,
        "status": "running",
        "trigger_type": trigger_type,
        "search_query_id": search_query_id,
        "job_type_id": job_type_id,
        "metadata": {
            "date_range": date_range,
            "lookback_days": expected_lookback,
            "source": source
        }
    }
    run_id = db.create_scrape_run(run_data)
    logger.info(f"Created scrape run: {run_id}")
    
    try:
        # Step 3: Get Bright Data client (mock or real based on settings)
        brightdata = get_client(source=source)
        
        # Step 4: Trigger collection
        snapshot_id = await brightdata.trigger_collection(
            keyword=query,
            location=location,
            posted_date_range=date_range,
            limit=1000
        )
        
        logger.info(f"Bright Data snapshot triggered: {snapshot_id}")
        
        # Step 5: Wait for completion (with progress logging)
        jobs_data = await brightdata.wait_for_completion(snapshot_id)
        
        logger.info(f"Received {len(jobs_data)} jobs from Bright Data")
        
        # Log warning if no jobs found
        if len(jobs_data) == 0:
            logger.warning(
                f"⚠️ No jobs returned from Bright Data!\n"
                f"  Query: '{query}'\n"
                f"  Location: '{location}'\n"
                f"  Date range: {date_range}\n"
                f"  Snapshot ID: {snapshot_id}\n"
                f"  This could indicate:\n"
                f"    - No jobs match the search criteria\n"
                f"    - Invalid location query\n"
                f"    - Bright Data API issue\n"
                f"    - Date range too restrictive"
            )
        
        # Step 6: Process jobs through ingestion pipeline
        batch_result = await process_jobs_batch(jobs_data, run_id, source=source)
        
        # Step 7: Assign job types to all jobs found in this run (BEFORE updating scrape_run)
        if job_type_id and batch_result.job_ids:
            logger.info(f"Assigning job type {job_type_id} to {len(batch_result.job_ids)} jobs")
            assignment_count = 0
            for job_id in batch_result.job_ids:
                try:
                    # Insert job_type_assignment (ON CONFLICT DO NOTHING handles duplicates)
                    db.client.table("job_type_assignments").insert({
                        "job_posting_id": job_id,
                        "job_type_id": job_type_id,
                        "assigned_via": "scrape"
                    }).execute()
                    assignment_count += 1
                except Exception as e:
                    # Ignore duplicate key errors
                    if "duplicate key" not in str(e).lower():
                        logger.warning(f"Failed to assign type to job {job_id}: {e}")
            
            logger.info(f"✅ Created {assignment_count} job type assignments")
        
        # Step 8: Update scrape_run with results
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        db.update_scrape_run(run_id, {
            "status": "completed",
            "completed_at": end_time.isoformat(),
            "jobs_found": len(jobs_data),
            "jobs_new": batch_result.new_count,
            "jobs_updated": batch_result.updated_count,
            "metadata": {
                "date_range": date_range,
                "lookback_days": expected_lookback,
                "snapshot_id": snapshot_id,
                "duration_seconds": duration,
                "batch_summary": batch_result.summary(),
                "jobs_error": batch_result.error_count,
                "error_details": batch_result.error_details if batch_result.error_count > 0 else [],
                "brightdata_jobs_returned": len(jobs_data),
                "query_params": {
                    "keyword": query,
                    "location": location,
                    "posted_date_range": date_range,
                    "limit": 1000
                }
            }
        })
        
        # Clean up
        await brightdata.close()
        
        # Return result
        result = ScrapeRunResult(
            run_id=run_id,
            query=query,
            location=location,
            status='completed',
            jobs_found=len(jobs_data),
            jobs_new=batch_result.new_count,
            jobs_updated=batch_result.updated_count,
            duration_seconds=duration,
            snapshot_id=snapshot_id
        )
        
        logger.success(result.summary())
        return result
        
    except Exception as e:
        # Handle errors gracefully with detailed logging
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.exception(f"Scrape run failed with {error_type}: {error_msg}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Create detailed error message
        detailed_error = f"{error_type}: {error_msg}"
        if not error_msg:
            detailed_error = f"{error_type}: Unknown error occurred"
        
        db.update_scrape_run(run_id, {
            "status": "failed",
            "completed_at": end_time.isoformat(),
            "error_message": detailed_error,
            "metadata": {
                "date_range": date_range,
                "lookback_days": expected_lookback,
                "error_type": error_type,
                "duration_seconds": duration
            }
        })
        
        logger.error(f"Run {run_id} failed after {duration:.1f}s: {detailed_error}")
        
        return ScrapeRunResult(
            run_id=run_id,
            query=query,
            location=location,
            status='failed',
            jobs_found=0,
            jobs_new=0,
            jobs_updated=0,
            duration_seconds=duration,
            error=detailed_error
        )
