"""Test script for LinkedIn job verification service."""

import asyncio
from loguru import logger
from services.job_verification import get_verification_service


async def test_verification():
    """Test job verification with a small sample."""
    logger.info("🧪 Testing job verification service...")
    
    verification_service = get_verification_service()
    
    # Test with small batch of Data jobs only
    stats = await verification_service.verify_active_jobs(
        batch_size=10,  # Small batch for testing
        only_data_jobs=True
    )
    
    logger.info("📊 Verification Results:")
    logger.info(f"  - Verified: {stats['verified']}")
    logger.info(f"  - Still Active: {stats['still_active']}")
    logger.info(f"  - Marked Inactive: {stats['marked_inactive']}")
    logger.info(f"  - Errors: {stats['errors']}")
    
    return stats


if __name__ == "__main__":
    asyncio.run(test_verification())
