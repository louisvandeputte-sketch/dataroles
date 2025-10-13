"""Pydantic models for LinkedIn job data validation and parsing."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class LinkedInBaseSalary(BaseModel):
    """Parse salary range from string."""
    currency: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    payment_period: Optional[str] = None
    
    @classmethod
    def from_string(cls, salary_string: Optional[str]) -> Optional['LinkedInBaseSalary']:
        """
        Parse strings like "$120,000.00/yr - $150,000.00/yr" or "$15.50/hr - $16.75/hr"
        """
        if not salary_string:
            return None
        
        try:
            # Extract currency symbol
            currency = salary_string[0] if salary_string[0] in ['$', '€', '£'] else None
            
            # Split on dash
            parts = salary_string.split('-')
            if len(parts) != 2:
                return None
            
            # Extract min amount
            min_part = parts[0].strip()
            min_amount = float(''.join(c for c in min_part if c.isdigit() or c == '.'))
            
            # Extract max amount and period
            max_part = parts[1].strip()
            max_amount = float(''.join(c for c in max_part.split('/')[0] if c.isdigit() or c == '.'))
            
            # Extract payment period (yr, hr, mo)
            period = max_part.split('/')[-1] if '/' in max_part else None
            
            return cls(
                currency=currency,
                min_amount=min_amount,
                max_amount=max_amount,
                payment_period=period
            )
        except Exception:
            return None


class LinkedInCompany(BaseModel):
    """Company information from LinkedIn."""
    linkedin_company_id: Optional[str] = Field(None, alias="company_id")
    name: str = Field(..., alias="company_name")
    company_url: Optional[str] = None
    logo_url: Optional[str] = Field(None, alias="company_logo")
    
    model_config = {"populate_by_name": True}
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to database insert format."""
        return {
            "linkedin_company_id": self.linkedin_company_id,
            "name": self.name,
            "company_url": self.company_url,
            "logo_url": self.logo_url
        }


class LinkedInLocation(BaseModel):
    """Parse location string into components."""
    full_location_string: str
    city: Optional[str] = None
    region: Optional[str] = None
    country_code: Optional[str] = None
    
    @classmethod
    def from_string(cls, location_string: str) -> 'LinkedInLocation':
        """
        Parse strings like "New Lenox, IL" or "Pembroke Pines, FL" or "België"
        """
        parts = [p.strip() for p in location_string.split(',')]
        
        if len(parts) == 1:
            # Just country or city
            return cls(
                full_location_string=location_string,
                city=None,
                region=None,
                country_code=parts[0] if len(parts[0]) == 2 else None
            )
        elif len(parts) == 2:
            # City, State/Country
            return cls(
                full_location_string=location_string,
                city=parts[0],
                region=parts[1] if len(parts[1]) <= 3 else None,
                country_code=parts[1] if len(parts[1]) == 2 else None
            )
        else:
            # City, State, Country
            return cls(
                full_location_string=location_string,
                city=parts[0],
                region=parts[1],
                country_code=parts[2] if len(parts[2]) == 2 else None
            )
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to database insert format."""
        return {
            "full_location_string": self.full_location_string,
            "city": self.city,
            "region": self.region,
            "country_code": self.country_code
        }


class LinkedInJobPoster(BaseModel):
    """Job poster information."""
    name: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    
    def to_db_dict(self, job_posting_id: UUID) -> Optional[Dict[str, Any]]:
        """Convert to database insert format."""
        if not self.name:
            return None
        return {
            "job_posting_id": str(job_posting_id),
            "name": self.name,
            "title": self.title,
            "profile_url": self.url
        }


class LinkedInJobPosting(BaseModel):
    """Main job posting model matching LinkedIn API JSON."""
    
    # Core fields
    job_posting_id: str
    job_title: str
    company_name: str
    job_location: str
    job_url: str = Field(..., alias="url")  # Bright Data sends "url" instead of "job_url"
    
    # Optional identification
    company_id: Optional[str] = None
    company_logo: Optional[str] = None
    company_url: Optional[str] = None
    
    # Job details
    job_summary: Optional[str] = None
    job_seniority_level: Optional[str] = None
    job_function: Optional[str] = None
    job_employment_type: Optional[str] = None
    job_industries: Optional[str] = None
    
    # Salary
    job_base_pay_range: Optional[str] = None
    base_salary: Optional[Dict] = None
    
    # Description
    job_description_formatted: Optional[str] = None
    
    # Metadata
    job_posted_date: Optional[datetime] = None
    job_posted_time: Optional[str] = None
    job_num_applicants: Optional[int] = None
    
    # Application
    apply_link: Optional[str] = None
    application_availability: Optional[bool] = None
    
    # Poster
    job_poster: Optional[Dict] = None
    
    model_config = {"populate_by_name": True}
    
    @field_validator('job_posted_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse ISO8601 date string to datetime."""
        if not v:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        except Exception:
            return None
    
    def get_company(self) -> LinkedInCompany:
        """Extract company information."""
        return LinkedInCompany(
            company_id=self.company_id,
            company_name=self.company_name,
            company_url=self.company_url,
            company_logo=self.company_logo
        )
    
    def get_location(self) -> LinkedInLocation:
        """Extract location information."""
        return LinkedInLocation.from_string(self.job_location)
    
    def get_salary(self) -> Optional[LinkedInBaseSalary]:
        """Parse salary information."""
        if self.base_salary:
            return LinkedInBaseSalary(**self.base_salary)
        elif self.job_base_pay_range:
            return LinkedInBaseSalary.from_string(self.job_base_pay_range)
        return None
    
    def get_poster(self) -> Optional[LinkedInJobPoster]:
        """Extract job poster if available."""
        if not self.job_poster:
            return None
        return LinkedInJobPoster(**self.job_poster)
    
    def to_db_dict(self, company_id: UUID, location_id: UUID) -> Dict[str, Any]:
        """Convert to database insert format for job_postings table."""
        salary = self.get_salary()
        
        # Parse industries into array
        industries = []
        if self.job_industries:
            industries = [i.strip() for i in self.job_industries.split(',')]
        
        return {
            "linkedin_job_id": self.job_posting_id,
            "company_id": str(company_id),
            "location_id": str(location_id),
            "title": self.job_title,
            "seniority_level": self.job_seniority_level,
            "employment_type": self.job_employment_type,
            "industries": industries,
            "function_areas": [self.job_function] if self.job_function else [],
            "posted_date": self.job_posted_date.isoformat() if self.job_posted_date else None,
            "posted_time_ago": self.job_posted_time,
            "num_applicants": self.job_num_applicants,
            "base_salary_min": salary.min_amount if salary else None,
            "base_salary_max": salary.max_amount if salary else None,
            "salary_currency": salary.currency if salary else None,
            "salary_period": salary.payment_period if salary else None,
            "job_url": self.job_url,
            "apply_url": self.apply_link,
            "application_available": self.application_availability
        }
    
    def get_description_dict(self, job_posting_id: UUID) -> Dict[str, Any]:
        """Get job description data for insertion."""
        # Import here to avoid circular dependency
        from ingestion.normalizer import normalize_job_description
        
        return {
            "job_posting_id": str(job_posting_id),
            "summary": self.job_summary,
            "full_description_html": self.job_description_formatted,
            "full_description_text": normalize_job_description(self.job_description_formatted) if self.job_description_formatted else None
        }
