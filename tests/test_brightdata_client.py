"""Pytest tests for Bright Data API clients."""

import pytest
import asyncio
from clients.mock_brightdata import MockBrightDataLinkedInClient
from clients.brightdata_linkedin import (
    BrightDataLinkedInClient,
    BrightDataError,
    QuotaExceededError,
    SnapshotTimeoutError
)


class TestMockBrightDataClient:
    """Test mock Bright Data client."""
    
    @pytest.fixture
    def client(self):
        """Create mock client."""
        return MockBrightDataLinkedInClient()
    
    @pytest.mark.asyncio
    async def test_trigger_collection(self, client):
        """Test triggering a collection."""
        snapshot_id = await client.trigger_collection(
            keyword="Data Engineer",
            location="Netherlands",
            limit=10
        )
        assert snapshot_id is not None
        assert snapshot_id.startswith("mock_snapshot_")
    
    @pytest.mark.asyncio
    async def test_get_snapshot_status(self, client):
        """Test getting snapshot status."""
        snapshot_id = await client.trigger_collection("test", "test", limit=1)
        status = await client.get_snapshot_status(snapshot_id)
        
        assert "status" in status
        assert "progress" in status
        assert status["status"] in ["running", "ready", "failed"]
    
    @pytest.mark.asyncio
    async def test_wait_for_completion(self, client):
        """Test waiting for completion."""
        snapshot_id = await client.trigger_collection(
            keyword="Data Engineer",
            location="Netherlands",
            limit=5
        )
        
        results = await client.wait_for_completion(
            snapshot_id,
            poll_interval=1,
            timeout=30
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert "job_posting_id" in results[0]
    
    @pytest.mark.asyncio
    async def test_download_results(self, client):
        """Test downloading results."""
        snapshot_id = await client.trigger_collection("test", "test", limit=3)
        
        # Wait for completion
        await client.wait_for_completion(snapshot_id, poll_interval=1, timeout=10)
        
        # Download results
        results = await client.download_results(snapshot_id)
        assert isinstance(results, list)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_snapshot_id(self, client):
        """Test handling invalid snapshot ID."""
        status = await client.get_snapshot_status("invalid_id")
        assert status["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_download_before_ready(self, client):
        """Test downloading before snapshot is ready."""
        snapshot_id = await client.trigger_collection("test", "test", limit=1)
        
        # Try to download immediately (should fail)
        with pytest.raises(ValueError):
            await client.download_results(snapshot_id)
    
    @pytest.mark.asyncio
    async def test_progress_simulation(self, client):
        """Test that progress increases over time."""
        snapshot_id = await client.trigger_collection("test", "test", limit=1)
        
        # Check initial status
        status1 = await client.get_snapshot_status(snapshot_id)
        initial_progress = status1["progress"]
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check again
        status2 = await client.get_snapshot_status(snapshot_id)
        later_progress = status2["progress"]
        
        # Progress should have increased
        assert later_progress >= initial_progress


class TestRealBrightDataClient:
    """Test real Bright Data client (initialization only, no API calls)."""
    
    def test_client_initialization(self):
        """Test that client can be initialized."""
        client = BrightDataLinkedInClient(
            api_token="test_token",
            dataset_id="test_dataset",
            timeout=1800,
            poll_interval=30
        )
        
        assert client.api_token == "test_token"
        assert client.dataset_id == "test_dataset"
        assert client.timeout == 1800
        assert client.poll_interval == 30
        assert client.BASE_URL == "https://api.brightdata.com/datasets/v3"
    
    def test_exception_classes(self):
        """Test custom exception classes."""
        # Test that exceptions can be raised
        with pytest.raises(BrightDataError):
            raise BrightDataError("Test error")
        
        with pytest.raises(QuotaExceededError):
            raise QuotaExceededError("Quota exceeded")
        
        with pytest.raises(SnapshotTimeoutError):
            raise SnapshotTimeoutError("Timeout")
        
        # Test inheritance
        assert issubclass(QuotaExceededError, BrightDataError)
        assert issubclass(SnapshotTimeoutError, BrightDataError)


class TestClientFactory:
    """Test client factory functions."""
    
    def test_get_client_returns_mock(self):
        """Test that get_client returns mock when USE_MOCK_API=true."""
        from clients import get_client
        
        client = get_client()
        assert isinstance(client, MockBrightDataLinkedInClient)
    
    def test_get_mock_client(self):
        """Test get_mock_brightdata_client."""
        from clients import get_mock_brightdata_client
        
        client = get_mock_brightdata_client()
        assert isinstance(client, MockBrightDataLinkedInClient)
    
    def test_get_real_client(self):
        """Test get_brightdata_client."""
        from clients import get_brightdata_client
        
        client = get_brightdata_client()
        assert isinstance(client, BrightDataLinkedInClient)
