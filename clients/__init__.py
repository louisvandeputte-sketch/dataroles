"""External API clients."""

from clients.brightdata_linkedin import (
    BrightDataLinkedInClient,
    BrightDataError,
    QuotaExceededError,
    SnapshotTimeoutError,
    get_brightdata_client
)
from clients.brightdata_indeed import BrightDataIndeedClient
from clients.mock_brightdata import (
    MockBrightDataLinkedInClient,
    get_mock_brightdata_client
)
from config.settings import settings


def get_client(source: str = "linkedin"):
    """
    Get appropriate client based on settings and source.
    
    Args:
        source: "linkedin" or "indeed"
    
    Returns:
        Bright Data client for the specified source
    """
    if settings.use_mock_api:
        # For now, mock only supports LinkedIn
        return get_mock_brightdata_client()
    else:
        if source == "linkedin":
            return get_brightdata_client()
        elif source == "indeed":
            return get_indeed_client()
        else:
            raise ValueError(f"Unknown source: {source}")

def get_indeed_client():
    """
    Get Indeed Bright Data client.
    Uses the Indeed Jobs dataset ID: gd_l4dx9j9sscpvs7no2
    """
    # Indeed Jobs dataset ID (from Bright Data API docs)
    indeed_dataset_id = "gd_l4dx9j9sscpvs7no2"
    
    return BrightDataIndeedClient(
        api_token=settings.brightdata_api_token,
        dataset_id=indeed_dataset_id
    )


__all__ = [
    "BrightDataLinkedInClient",
    "BrightDataIndeedClient",
    "MockBrightDataLinkedInClient",
    "BrightDataError",
    "QuotaExceededError",
    "SnapshotTimeoutError",
    "get_brightdata_client",
    "get_indeed_client",
    "get_mock_brightdata_client",
    "get_client"
]
