"""Date range strategy for incremental scraping."""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from database.client import db


def determine_date_range(
    query: str,
    location: str,
    lookback_days: Optional[int] = None
) -> Tuple[str, int]:
    """
    Determine optimal Bright Data date_range for incremental scraping.
    
    Args:
        query: Search query (e.g., "Data Engineer")
        location: Location filter (e.g., "België")
        lookback_days: Optional manual override for lookback period
    
    Returns:
        (bright_data_date_range, expected_lookback_days)
        date_range options: "past_24h", "past_week", "past_month"
    """
    
    # If manual lookback specified, use that
    if lookback_days is not None:
        return map_lookback_to_range(lookback_days), lookback_days
    
    # Get last successful run for this query+location
    last_run = db.get_last_successful_run(query, location)
    
    if not last_run:
        # First run: fetch past month
        logger.info(f"No previous run found for '{query}' in '{location}' - fetching past_month")
        return "past_month", 30
    
    # Calculate days since last run
    last_completed = datetime.fromisoformat(last_run["completed_at"].replace('Z', '+00:00'))
    days_since_last_run = (datetime.utcnow() - last_completed.replace(tzinfo=None)).days
    
    logger.info(f"Last run was {days_since_last_run} days ago")
    
    # Map to Bright Data options
    if days_since_last_run <= 1:
        return "past_24h", 1
    elif days_since_last_run <= 7:
        return "past_week", 7
    elif days_since_last_run <= 30:
        return "past_month", 30
    else:
        # Gap > 30 days: use past_month and log warning
        logger.warning(
            f"Large gap detected: {days_since_last_run} days since last run. "
            f"Using past_month but may miss some jobs."
        )
        return "past_month", 30


def map_lookback_to_range(lookback_days: int) -> str:
    """
    Map lookback days to Bright Data date_range options.
    
    Args:
        lookback_days: Number of days to look back
    
    Returns:
        Bright Data date_range string
    """
    if lookback_days <= 1:
        return "past_24h"
    elif lookback_days <= 7:
        return "past_week"
    else:
        return "past_month"


def should_trigger_scrape(query: str, location: str, min_interval_hours: int = 6) -> bool:
    """
    Check if enough time has passed since last run to trigger new scrape.
    
    Args:
        query: Search query
        location: Location filter
        min_interval_hours: Minimum hours between runs
    
    Returns:
        True if scrape should be triggered
    """
    last_run = db.get_last_successful_run(query, location)
    
    if not last_run:
        return True
    
    last_completed = datetime.fromisoformat(last_run["completed_at"].replace('Z', '+00:00'))
    hours_since = (datetime.utcnow() - last_completed.replace(tzinfo=None)).total_seconds() / 3600
    
    if hours_since < min_interval_hours:
        logger.info(f"Skipping scrape: only {hours_since:.1f} hours since last run (min: {min_interval_hours})")
        return False
    
    return True
