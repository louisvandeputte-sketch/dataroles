"""Pytest configuration and fixtures."""

import pytest
from typing import Generator


@pytest.fixture
def sample_linkedin_job():
    """Sample LinkedIn job data for testing."""
    return {
        "job_id": "3791234567",
        "job_url": "https://www.linkedin.com/jobs/view/3791234567",
        "job_title": "Senior Data Engineer",
        "company_name": "Tech Corp",
        "company_url": "https://www.linkedin.com/company/techcorp",
        "company_logo": "https://media.licdn.com/dms/image/logo.png",
        "location": "Amsterdam, North Holland, Netherlands",
        "posted_date": "2025-10-01",
        "applicants_count": 150,
        "seniority_level": "Mid-Senior level",
        "employment_type": "Full-time",
        "job_function": "Engineering",
        "industries": "Information Technology & Services"
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing without database."""
    # TODO: Implement mock client
    pass
