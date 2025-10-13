"""Pytest tests for LinkedIn Pydantic models."""

import pytest
import json
from pathlib import Path
from models.linkedin import (
    LinkedInJobPosting,
    LinkedInBaseSalary,
    LinkedInLocation,
    LinkedInCompany,
    LinkedInJobPoster
)
from uuid import uuid4


class TestLinkedInBaseSalary:
    """Test salary parsing."""
    
    def test_yearly_salary_parsing(self):
        """Test parsing yearly salary."""
        salary = LinkedInBaseSalary.from_string("$120,000.00/yr - $150,000.00/yr")
        assert salary is not None
        assert salary.currency == "$"
        assert salary.min_amount == 120000.0
        assert salary.max_amount == 150000.0
        assert salary.payment_period == "yr"
    
    def test_hourly_salary_parsing(self):
        """Test parsing hourly salary."""
        salary = LinkedInBaseSalary.from_string("$15.50/hr - $18.00/hr")
        assert salary is not None
        assert salary.currency == "$"
        assert salary.min_amount == 15.5
        assert salary.max_amount == 18.0
        assert salary.payment_period == "hr"
    
    def test_euro_salary_parsing(self):
        """Test parsing Euro salary."""
        salary = LinkedInBaseSalary.from_string("€50,000/yr - €60,000/yr")
        assert salary is not None
        assert salary.currency == "€"
        assert salary.min_amount == 50000.0
        assert salary.max_amount == 60000.0
    
    def test_invalid_salary_string(self):
        """Test invalid salary string returns None."""
        salary = LinkedInBaseSalary.from_string("invalid")
        assert salary is None
    
    def test_none_salary_string(self):
        """Test None salary string returns None."""
        salary = LinkedInBaseSalary.from_string(None)
        assert salary is None


class TestLinkedInLocation:
    """Test location parsing."""
    
    def test_city_state_country(self):
        """Test parsing city, state, country."""
        location = LinkedInLocation.from_string("Amsterdam, North Holland, Netherlands")
        assert location.full_location_string == "Amsterdam, North Holland, Netherlands"
        assert location.city == "Amsterdam"
        assert location.region == "North Holland"
        assert location.country_code is None
    
    def test_city_state_code(self):
        """Test parsing city with state code."""
        location = LinkedInLocation.from_string("New York, NY")
        assert location.city == "New York"
        assert location.region == "NY"
        assert location.country_code == "NY"
    
    def test_single_location(self):
        """Test parsing single location."""
        location = LinkedInLocation.from_string("België")
        assert location.full_location_string == "België"
        assert location.city is None
    
    def test_to_db_dict(self):
        """Test conversion to database dict."""
        location = LinkedInLocation.from_string("San Francisco, CA")
        db_dict = location.to_db_dict()
        assert "full_location_string" in db_dict
        assert "city" in db_dict
        assert db_dict["city"] == "San Francisco"


class TestLinkedInCompany:
    """Test company model."""
    
    def test_company_creation(self):
        """Test creating company from dict."""
        company = LinkedInCompany(
            company_id="12345",
            company_name="Tech Corp",
            company_url="https://linkedin.com/company/techcorp"
        )
        assert company.linkedin_company_id == "12345"
        assert company.name == "Tech Corp"
    
    def test_company_to_db_dict(self):
        """Test conversion to database dict."""
        company = LinkedInCompany(
            company_id="12345",
            company_name="Tech Corp"
        )
        db_dict = company.to_db_dict()
        assert db_dict["linkedin_company_id"] == "12345"
        assert db_dict["name"] == "Tech Corp"


class TestLinkedInJobPoster:
    """Test job poster model."""
    
    def test_poster_creation(self):
        """Test creating poster."""
        poster = LinkedInJobPoster(
            name="Jane Recruiter",
            title="Technical Recruiter",
            url="https://linkedin.com/in/jane"
        )
        assert poster.name == "Jane Recruiter"
    
    def test_poster_to_db_dict(self):
        """Test conversion to database dict."""
        poster = LinkedInJobPoster(name="Jane Recruiter")
        job_id = uuid4()
        db_dict = poster.to_db_dict(job_id)
        assert db_dict is not None
        assert db_dict["job_posting_id"] == str(job_id)
        assert db_dict["name"] == "Jane Recruiter"
    
    def test_empty_poster_returns_none(self):
        """Test empty poster returns None."""
        poster = LinkedInJobPoster()
        job_id = uuid4()
        db_dict = poster.to_db_dict(job_id)
        assert db_dict is None


class TestLinkedInJobPosting:
    """Test job posting model."""
    
    @pytest.fixture
    def sample_jobs(self):
        """Load sample jobs from fixture."""
        sample_file = Path("tests/fixtures/linkedin_jobs_sample.json")
        with open(sample_file) as f:
            return json.load(f)
    
    def test_parse_all_sample_jobs(self, sample_jobs):
        """Test parsing all sample jobs."""
        for job_data in sample_jobs:
            job = LinkedInJobPosting(**job_data)
            assert job.job_posting_id
            assert job.job_title
            assert job.company_name
    
    def test_get_company(self, sample_jobs):
        """Test extracting company."""
        job = LinkedInJobPosting(**sample_jobs[0])
        company = job.get_company()
        assert isinstance(company, LinkedInCompany)
        assert company.name == "Tech Corp"
    
    def test_get_location(self, sample_jobs):
        """Test extracting location."""
        job = LinkedInJobPosting(**sample_jobs[0])
        location = job.get_location()
        assert isinstance(location, LinkedInLocation)
        assert location.city == "Amsterdam"
    
    def test_get_salary(self, sample_jobs):
        """Test extracting salary."""
        job = LinkedInJobPosting(**sample_jobs[0])
        salary = job.get_salary()
        assert isinstance(salary, LinkedInBaseSalary)
        assert salary.min_amount == 120000.0
    
    def test_get_poster(self, sample_jobs):
        """Test extracting poster."""
        job = LinkedInJobPosting(**sample_jobs[0])
        poster = job.get_poster()
        assert isinstance(poster, LinkedInJobPoster)
        assert poster.name == "Jane Recruiter"
    
    def test_to_db_dict(self, sample_jobs):
        """Test conversion to database dict."""
        job = LinkedInJobPosting(**sample_jobs[0])
        company_id = uuid4()
        location_id = uuid4()
        db_dict = job.to_db_dict(company_id, location_id)
        
        # Check required fields
        assert db_dict["linkedin_job_id"] == job.job_posting_id
        assert db_dict["company_id"] == str(company_id)
        assert db_dict["location_id"] == str(location_id)
        assert db_dict["title"] == job.job_title
        assert db_dict["job_url"] == job.job_url
        
        # Check salary fields
        assert db_dict["base_salary_min"] == 120000.0
        assert db_dict["base_salary_max"] == 150000.0
        assert db_dict["salary_currency"] == "$"
        assert db_dict["salary_period"] == "yr"
    
    def test_get_description_dict(self, sample_jobs):
        """Test getting description dict."""
        job = LinkedInJobPosting(**sample_jobs[0])
        job_id = uuid4()
        desc_dict = job.get_description_dict(job_id)
        
        assert desc_dict["job_posting_id"] == str(job_id)
        assert desc_dict["summary"] == job.job_summary
        assert desc_dict["full_description_html"] == job.job_description_formatted
        assert desc_dict["full_description_text"] is not None
    
    def test_hourly_salary_job(self, sample_jobs):
        """Test job with hourly salary."""
        job = LinkedInJobPosting(**sample_jobs[3])  # Part-time job
        salary = job.get_salary()
        assert salary.payment_period == "hr"
        assert salary.min_amount == 15.5
    
    def test_job_without_salary(self, sample_jobs):
        """Test job without salary."""
        job = LinkedInJobPosting(**sample_jobs[4])  # BI Developer
        salary = job.get_salary()
        assert salary is None
    
    def test_date_parsing(self, sample_jobs):
        """Test date parsing."""
        job = LinkedInJobPosting(**sample_jobs[0])
        assert job.job_posted_date is not None
        assert job.job_posted_date.year == 2025
        assert job.job_posted_date.month == 10
