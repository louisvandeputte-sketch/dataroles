"""Mock Bright Data client for development and testing."""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from uuid import uuid4


class MockBrightDataLinkedInClient:
    """
    Mock client that simulates Bright Data API behavior.
    Uses sample data from fixtures for testing without consuming API credits.
    """
    
    def __init__(
        self,
        api_token: str = "mock_token",
        dataset_id: str = "mock_dataset",
        timeout: int = 1800,
        poll_interval: int = 2  # Faster polling for mock
    ):
        self.api_token = api_token
        self.dataset_id = dataset_id
        self.timeout = timeout
        self.poll_interval = poll_interval
        
        # Track mock snapshots
        self._snapshots = {}
        
        logger.info(f"Mock Bright Data client initialized (dataset: {dataset_id})")
    
    async def trigger_collection(
        self,
        keyword: str,
        location: str,
        posted_date_range: str = "past_week",
        limit: int = 1000
    ) -> str:
        """
        Simulate triggering a collection.
        Returns a mock snapshot_id.
        """
        snapshot_id = f"mock_snapshot_{uuid4().hex[:8]}"
        
        logger.info(f"[MOCK] Triggering collection: {keyword} in {location}")
        logger.info(f"[MOCK] Snapshot ID: {snapshot_id}")
        
        # Load sample data
        sample_file = Path("tests/fixtures/linkedin_jobs_sample.json")
        if sample_file.exists():
            with open(sample_file) as f:
                sample_data = json.load(f)
        else:
            # Fallback minimal data
            sample_data = [
                {
                    "job_posting_id": f"mock_job_{i}",
                    "job_title": f"{keyword} Position {i}",
                    "company_name": f"Company {i}",
                    "job_location": location,
                    "job_url": f"https://linkedin.com/jobs/view/mock_{i}",
                    "job_posted_date": "2025-10-09T12:00:00Z",
                    "job_employment_type": "Full-time"
                }
                for i in range(min(5, limit))
            ]
        
        # Store snapshot with simulated progress
        self._snapshots[snapshot_id] = {
            "status": "running",
            "progress": 0,
            "data": sample_data[:limit],
            "keyword": keyword,
            "location": location
        }
        
        # Simulate async processing
        asyncio.create_task(self._simulate_processing(snapshot_id))
        
        return snapshot_id
    
    async def _simulate_processing(self, snapshot_id: str):
        """Simulate gradual progress of a snapshot."""
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return
        
        # Simulate progress: 0% -> 50% -> 100%
        await asyncio.sleep(1)
        snapshot["progress"] = 50
        snapshot["status"] = "running"
        
        await asyncio.sleep(2)
        snapshot["progress"] = 100
        snapshot["status"] = "ready"
        
        logger.info(f"[MOCK] Snapshot {snapshot_id} completed")
    
    async def get_snapshot_status(self, snapshot_id: str) -> Dict:
        """
        Get status of a mock snapshot.
        
        Returns:
            {"status": "running|ready|failed", "progress": 0-100}
        """
        snapshot = self._snapshots.get(snapshot_id)
        
        if not snapshot:
            return {
                "status": "failed",
                "progress": 0,
                "error": "Snapshot not found"
            }
        
        return {
            "status": snapshot["status"],
            "progress": snapshot["progress"]
        }
    
    async def download_results(self, snapshot_id: str) -> List[Dict]:
        """
        Download results of a completed mock snapshot.
        
        Returns:
            List of job postings (LinkedIn JSON format)
        """
        snapshot = self._snapshots.get(snapshot_id)
        
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        if snapshot["status"] != "ready":
            raise ValueError(f"Snapshot {snapshot_id} is not ready (status: {snapshot['status']})")
        
        logger.info(f"[MOCK] Downloaded {len(snapshot['data'])} jobs from snapshot {snapshot_id}")
        return snapshot["data"]
    
    async def wait_for_completion(
        self,
        snapshot_id: str,
        poll_interval: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict]:
        """
        Poll until mock collection is complete, then download results.
        
        Args:
            snapshot_id: Snapshot to wait for
            poll_interval: Seconds between polls (default: self.poll_interval)
            timeout: Max wait time in seconds (default: self.timeout)
        
        Returns:
            List of job postings
        """
        poll_interval = poll_interval or self.poll_interval
        timeout = timeout or self.timeout
        start_time = asyncio.get_event_loop().time()
        
        logger.info(f"[MOCK] Waiting for snapshot {snapshot_id} to complete")
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            status_data = await self.get_snapshot_status(snapshot_id)
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            if status == "ready":
                logger.success(f"[MOCK] Snapshot {snapshot_id} completed successfully")
                return await self.download_results(snapshot_id)
            
            elif status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                raise ValueError(f"Snapshot failed: {error_msg}")
            
            logger.info(f"[MOCK] Snapshot {snapshot_id}: {progress}% complete")
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Snapshot {snapshot_id} did not complete in {timeout}s")
    
    async def close(self):
        """Close the mock client (no-op)."""
        logger.info("[MOCK] Client closed")


def get_mock_brightdata_client() -> MockBrightDataLinkedInClient:
    """Factory function to create mock Bright Data client."""
    return MockBrightDataLinkedInClient()
