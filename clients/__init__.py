"""External API clients."""

from clients.brightdata_linkedin import (
    BrightDataLinkedInClient,
    BrightDataError,
    QuotaExceededError,
    SnapshotTimeoutError,
    get_brightdata_client
)
from clients.mock_brightdata import (
    MockBrightDataLinkedInClient,
    get_mock_brightdata_client
)
from config.settings import settings


def get_client():
    """
    Get appropriate client based on settings.
    Returns mock client if USE_MOCK_API is True.
    """
    if settings.use_mock_api:
        return get_mock_brightdata_client()
    else:
        return get_brightdata_client()


__all__ = [
    "BrightDataLinkedInClient",
    "MockBrightDataLinkedInClient",
    "BrightDataError",
    "QuotaExceededError",
    "SnapshotTimeoutError",
    "get_brightdata_client",
    "get_mock_brightdata_client",
    "get_client"
]
