"""Bright Data LinkedIn Jobs Scraper API client."""

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


class BrightDataLinkedInClient:
    """
    Client for Bright Data LinkedIn Jobs Scraper API.
    Docs: https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api
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
                connect=30.0,  # 30s to establish connection
                read=300.0,    # 5min to read response
                write=30.0,    # 30s to send request
                pool=30.0      # 30s to get connection from pool
            )
        )
        
        logger.info(f"Bright Data client initialized for dataset {dataset_id}")
    
    async def trigger_collection(
        self,
        keyword: str,
        location: str,
        posted_date_range: str = "past_week",
        limit: int = 1000
    ) -> str:
        """
        Trigger a new data collection.
        
        Args:
            keyword: Search keyword (e.g., "Data Engineer")
            location: Location filter (e.g., "België")
            posted_date_range: "past_24h", "past_week", or "past_month"
            limit: Maximum results to fetch
        
        Returns:
            snapshot_id for polling
        """
        # Map our date range to Bright Data's time_range format
        time_range_map = {
            "past_24h": "Past 24 hours",
            "past_week": "Past week",
            "past_month": "Past month"
        }
        time_range = time_range_map.get(posted_date_range, "Past week")
        
        # Auto-detect Belgium cities and add country code
        belgium_cities = ["gent", "ghent", "antwerpen", "antwerp", "brussel", "brussels", 
                         "brugge", "bruges", "leuven", "mechelen", "aalst", "hasselt", 
                         "genk", "oostende", "kortrijk", "charleroi", "liège", "luik", "namur", "namen"]
        
        # Normalize location for better LinkedIn matching
        location_normalized = location
        country_code = ""
        
        location_lower = location.lower().strip()
        if location_lower in belgium_cities:
            # Add country code for Belgium cities
            country_code = "BE"
            # Use English name for better LinkedIn compatibility
            if location_lower == "gent":
                location_normalized = "Ghent, Belgium"
            elif location_lower == "antwerpen":
                location_normalized = "Antwerp, Belgium"
            elif location_lower == "brussel":
                location_normalized = "Brussels, Belgium"
            elif location_lower == "brugge":
                location_normalized = "Bruges, Belgium"
            elif "," not in location:
                # Add ", Belgium" if not already present
                location_normalized = f"{location}, Belgium"
        
        logger.info(f"Location normalized: '{location}' → '{location_normalized}' (country: {country_code or 'auto'})")
        
        # Bright Data expects "input" array format
        payload = {
            "input": [
                {
                    "keyword": keyword,
                    "location": location_normalized,
                    "time_range": time_range,
                    "country": country_code,  # Add country code for Belgium
                    "job_type": "",  # Optional filter
                    "experience_level": "",  # Optional filter
                    "remote": "",  # Optional filter
                    "company": "",  # Optional filter
                    "location_radius": ""  # Optional filter
                }
            ]
        }
        
        try:
            logger.info(f"Triggering Bright Data collection: {keyword} in {location} ({posted_date_range})")
            
            # Use the trigger endpoint for async workflow (better for long-running scrapes)
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
            
            # Trigger returns snapshot_id for polling
            snapshot_id = data.get("snapshot_id")
            
            if not snapshot_id:
                raise BrightDataError(f"No snapshot_id in response: {data}")
            
            logger.success(f"Collection triggered successfully: snapshot_id={snapshot_id}")
            return snapshot_id
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout triggering collection: {e}")
            raise BrightDataError(f"Bright Data API timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error triggering collection: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                raise QuotaExceededError("Rate limit exceeded")
            elif e.response.status_code == 402:
                raise QuotaExceededError("Subscription quota exceeded")
            elif e.response.status_code == 401:
                raise BrightDataError("Invalid API token")
            else:
                raise BrightDataError(f"API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception(f"Unexpected error triggering collection: {e}")
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
            List of job postings (LinkedIn JSON format)
        """
        try:
            logger.info(f"Downloading results for snapshot {snapshot_id}")
            
            response = await self.client.get(
                f"{self.BASE_URL}/snapshot/{snapshot_id}",
                params={"format": "json"}
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Log raw response for debugging
            logger.info(f"Raw Bright Data response type: {type(data).__name__}")
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                logger.debug(f"First job raw data: {data[0]}")
            
            # Validate that we got a list, not a status dict
            if isinstance(data, dict):
                # Sometimes Bright Data returns {"status": "building"} even after status check
                if data.get("status") == "building":
                    raise BrightDataError(f"Snapshot still building (race condition): {data}")
                else:
                    raise BrightDataError(f"Expected list of jobs, got dict: {data}")
            
            if not isinstance(data, list):
                raise BrightDataError(f"Expected list of jobs, got {type(data).__name__}")
            
            # Filter out error items - Bright Data returns error objects for failed requests
            # Error items have 'error' and 'error_code' fields but no job data
            jobs = []
            error_count = 0
            for item in data:
                if isinstance(item, dict):
                    if 'error' in item or 'error_code' in item:
                        # This is an error item, not a job
                        error_count += 1
                        logger.warning(f"Bright Data error item: {item.get('error', 'Unknown error')}")
                    else:
                        # This is actual job data
                        jobs.append(item)
                else:
                    jobs.append(item)
            
            if error_count > 0:
                logger.warning(f"Filtered out {error_count} error items from Bright Data response")
            
            logger.info(f"Downloaded {len(jobs)} LinkedIn jobs from snapshot {snapshot_id} ({error_count} errors filtered)")
            return jobs
            
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
        
        logger.info(f"Waiting for snapshot {snapshot_id} to complete (timeout: {timeout}s)")
        
        poll_count = 0
        while time.time() - start_time < timeout:
            poll_count += 1
            elapsed = time.time() - start_time
            
            try:
                status_data = await self.get_snapshot_status(snapshot_id)
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                if status == "ready":
                    logger.success(f"Snapshot {snapshot_id} completed successfully after {elapsed:.0f}s")
                    return await self.download_results(snapshot_id)
                
                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    raise BrightDataError(f"Snapshot failed: {error_msg}")
                
                logger.info(f"Snapshot {snapshot_id}: {progress}% complete (status: {status}) - Poll #{poll_count}, elapsed: {elapsed:.0f}s")
                await asyncio.sleep(poll_interval)
                
            except BrightDataError:
                raise
            except Exception as e:
                logger.error(f"Error polling snapshot status: {e}")
                # Continue polling unless we hit timeout
                await asyncio.sleep(poll_interval)
        
        elapsed = time.time() - start_time
        raise SnapshotTimeoutError(f"Snapshot {snapshot_id} did not complete in {timeout}s (elapsed: {elapsed:.0f}s, polls: {poll_count})")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def get_brightdata_client() -> BrightDataLinkedInClient:
    """Factory function to create Bright Data client."""
    return BrightDataLinkedInClient(
        api_token=settings.brightdata_api_token,
        dataset_id=settings.brightdata_dataset_id,
        timeout=settings.brightdata_timeout,
        poll_interval=settings.brightdata_poll_interval
    )
