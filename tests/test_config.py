"""Test configuration and settings."""

import pytest
from pydantic import ValidationError


def test_settings_requires_env_vars():
    """Test that settings validation works."""
    # This test will pass if .env is properly configured
    # or fail with ValidationError if required vars are missing
    try:
        from config.settings import settings
        assert settings.supabase_url
        assert settings.supabase_key
        assert settings.brightdata_api_token
        assert settings.brightdata_dataset_id == "gd_lpfll7v5hcqtkxl6l"
    except ValidationError as e:
        pytest.skip(f"Environment variables not configured: {e}")


def test_settings_defaults():
    """Test that default settings are correct."""
    try:
        from config.settings import settings
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.web_port == 8000
        assert settings.brightdata_max_concurrent_requests == 3
        assert settings.brightdata_poll_interval == 30
    except ValidationError:
        pytest.skip("Environment variables not configured")
