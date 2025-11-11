"""Bright Data Indeed Jobs Scraper API client."""

import httpx
import asyncio
import time
from typing import List, Dict, Optional
from loguru import logger
from config.settings import settings


class BrightDataError(Exception):
    """Base exception for Bright Data errors."""
    pass


class QuotaExceededError(BrightDataError):
    """Raised when API quota is exceeded."""
    pass


class SnapshotTimeoutError(BrightDataError):
    """Raised when snapshot doesn't complete in time."""
    pass


class BrightDataIndeedClient:
    """
    Client for Bright Data Indeed Jobs Scraper API.
    Similar structure to LinkedIn client but adapted for Indeed API format.
    """
    
    BASE_URL = "https://api.brightdata.com/datasets/v3"
    
    def __init__(
        self,
        api_token: str,
        dataset_id: str,
        timeout: int = 1800,
        poll_interval: int = 30
    ):
        self.api_token = api_token
        self.dataset_id = dataset_id
        self.timeout = timeout
        self.poll_interval = poll_interval
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(
                connect=30.0,
                read=300.0,
                write=30.0,
                pool=30.0
            )
        )
        
        logger.info(f"Bright Data Indeed client initialized for dataset {dataset_id}")
    
    async def trigger_collection(
        self,
        keyword: str,
        location: str,
        posted_date_range: str = "past_week",
        limit: int = 1000
    ) -> str:
        """
        Trigger a new Indeed data collection.
        
        Args:
            keyword: Search keyword (e.g., "Data Engineer")
            location: Location filter (e.g., "Belgium" or "Charlotte, NC")
            posted_date_range: "past_24h", "past_week", or "past_month"
            limit: Maximum results to fetch
        
        Returns:
            snapshot_id for polling
        """
        # Map our date range to Indeed's date_posted format
        time_range_map = {
            "past_24h": "Last 24 hours",
            "past_week": "Last 7 days",
            "past_month": "Last 30 days"
        }
        date_posted = time_range_map.get(posted_date_range, "Last 7 days")
        
        # Detect country and domain from location
        # Default to US if not specified
        country = "US"
        domain = "indeed.com"
        
        location_lower = location.lower()
        if "belgium" in location_lower or "belgië" in location_lower:
            country = "BE"
            domain = "be.indeed.com"
        elif "france" in location_lower or "paris" in location_lower:
            country = "FR"
            domain = "fr.indeed.com"
        elif "uk" in location_lower or "london" in location_lower or "united kingdom" in location_lower:
            country = "GB"
            domain = "uk.indeed.com"
        elif "netherlands" in location_lower or "amsterdam" in location_lower:
            country = "NL"
            domain = "nl.indeed.com"
        elif "germany" in location_lower or "berlin" in location_lower:
            country = "DE"
            domain = "de.indeed.com"
        
        logger.info(f"Detected country: {country}, domain: {domain}")
        
        # Indeed API payload format (from Bright Data docs)
        payload = {
            "input": [
                {
                    "country": country,
                    "domain": domain,
                    "keyword_search": keyword,
                    "location": location,
                    "date_posted": date_posted,
                    "posted_by": "",
                    "location_radius": ""
                }
            ]
        }
        
        try:
            logger.info(f"Triggering Indeed collection: {keyword} in {location} ({posted_date_range})")
            
            # Use trigger endpoint for async workflow
            url = f"{self.BASE_URL}/trigger"
            params = {
                "dataset_id": self.dataset_id,
                "include_errors": "true",
                "type": "discover_new",
                "discover_by": "keyword"
            }
            
            logger.debug(f"POST {url} with params: {params}")
            logger.debug(f"Payload: {payload}")
            
            response = await self.client.post(
                url,
                json=payload,
                params=params
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Response data: {data}")
            
            snapshot_id = data.get("snapshot_id")
            
            if not snapshot_id:
                raise BrightDataError(f"No snapshot_id in response: {data}")
            
            logger.success(f"Indeed collection triggered: snapshot_id={snapshot_id}")
            return snapshot_id
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout triggering Indeed collection: {e}")
            raise BrightDataError(f"Bright Data API timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                raise QuotaExceededError("Rate limit exceeded")
            elif e.response.status_code == 402:
                raise QuotaExceededError("Subscription quota exceeded")
            elif e.response.status_code == 401:
                raise BrightDataError("Invalid API token")
            else:
                raise BrightDataError(f"API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception(f"Unexpected error triggering Indeed collection: {e}")
            raise BrightDataError(f"Failed to trigger collection: {e}")
    
    async def get_snapshot_status(self, snapshot_id: str) -> Dict:
        """
        Check status of a collection.
        
        Returns:
            {"status": "running|ready|failed", "progress": 0-100}
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/progress/{snapshot_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BrightDataError(f"Failed to get snapshot status: {e}")
    
    async def download_results(self, snapshot_id: str) -> List[Dict]:
        """
        Download results of a completed snapshot.
        
        Returns:
            List of job postings (Indeed JSON format)
        """
        try:
            logger.info(f"Downloading Indeed results for snapshot {snapshot_id}")
            
            response = await self.client.get(
                f"{self.BASE_URL}/snapshot/{snapshot_id}",
                params={"format": "json"}
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Validate response format
            if isinstance(data, dict):
                if data.get("status") == "building":
                    raise BrightDataError(f"Snapshot still building: {data}")
                else:
                    raise BrightDataError(f"Expected list of jobs, got dict: {data}")
            
            if not isinstance(data, list):
                raise BrightDataError(f"Expected list of jobs, got {type(data).__name__}")
            
            logger.info(f"Downloaded {len(data)} Indeed jobs from snapshot {snapshot_id}")
            return data
            
        except httpx.HTTPStatusError as e:
            raise BrightDataError(f"Failed to download results: {e}")
    
    async def wait_for_completion(
        self,
        snapshot_id: str,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict]:
        """
        Poll until collection is complete, then download results.
        
        Args:
            snapshot_id: Snapshot to wait for
            poll_interval: Seconds between polls (default: self.poll_interval)
            timeout: Max wait time in seconds (default: self.timeout)
        
        Returns:
            List of job postings
        """
        poll_interval = poll_interval or self.poll_interval
        timeout = timeout or self.timeout
        start_time = time.time()
        
        logger.info(f"Waiting for Indeed snapshot {snapshot_id} to complete (timeout: {timeout}s)")
        
        poll_count = 0
        while time.time() - start_time < timeout:
            poll_count += 1
            elapsed = time.time() - start_time
            
            try:
                status_data = await self.get_snapshot_status(snapshot_id)
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                if status == "ready":
                    logger.success(f"Indeed snapshot {snapshot_id} completed after {elapsed:.0f}s")
                    return await self.download_results(snapshot_id)
                
                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    raise BrightDataError(f"Snapshot failed: {error_msg}")
                
                logger.info(f"Indeed snapshot {snapshot_id}: {progress}% complete (status: {status}) - Poll #{poll_count}, elapsed: {elapsed:.0f}s")
                await asyncio.sleep(poll_interval)
                
            except BrightDataError:
                raise
            except Exception as e:
                logger.error(f"Error polling snapshot status: {e}")
                await asyncio.sleep(poll_interval)
        
        elapsed = time.time() - start_time
        raise SnapshotTimeoutError(f"Indeed snapshot {snapshot_id} did not complete in {timeout}s (elapsed: {elapsed:.0f}s, polls: {poll_count})")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
