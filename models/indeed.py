"""Indeed job posting models."""

import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class IndeedJobPosting(BaseModel):
    """Indeed job posting model matching Indeed API JSON."""
    
    model_config = ConfigDict(populate_by_name=True)  # Allow both field names and aliases
    
    # Core fields - only job_id and url are truly required
    jobid: str = Field(alias='job_id')  # Bright Data uses 'job_id' not 'jobid'
    url: str = Field(alias='job_url')  # Might be 'job_url' or 'url'
    
    # Important fields but optional (Bright Data might not always provide them)
    job_title: Optional[str] = Field(default="Untitled Position", alias='title')
    company_name: Optional[str] = Field(default="Unknown Company", alias='company')
    location: Optional[str] = Field(default="Unknown Location", alias='job_location')
    
    # Description fields
    description_text: Optional[str] = ""
    description: Optional[str] = None  # HTML version
    job_description_formatted: Optional[str] = None  # HTML formatted version
    
    # Optional company fields
    company_website: Optional[str] = None
    logo_url: Optional[str] = None
    company_link: Optional[str] = None  # Indeed company page
    company_rating: Optional[float] = None
    company_reviews_count: Optional[int] = None
    
    # Job details
    job_type: Optional[str] = None  # "Full-time", "Part-time", etc.
    salary_formatted: Optional[str] = None
    
    # Extra Indeed fields
    benefits: Optional[List[str]] = None
    qualifications: Optional[str] = None
    shift_schedule: Optional[List[str]] = None
    
    # Location details
    region: Optional[str] = None  # US state code (e.g., "NC")
    country: Optional[str] = None  # Country code (e.g., "US")
    job_location: Optional[str] = None  # Full address
    
    # Metadata
    date_posted: Optional[str] = None  # "30+ days ago"
    date_posted_parsed: Optional[datetime] = None
    
    # Application
    apply_link: Optional[str] = None
    is_expired: Optional[bool] = False
    
    # Domain info
    domain: Optional[str] = None
    srcname: Optional[str] = None
    discovery_input: Optional[Any] = None
    
    @field_validator('date_posted_parsed', mode='before')
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
    
    def get_company_dict(self) -> Dict[str, Any]:
        """Extract company information for database."""
        return {
            "name": self.company_name,
            "logo_url": self.logo_url,
            "company_url": self.company_website,
            "indeed_company_url": self.company_link,
            "rating": self.company_rating,
            "reviews_count": self.company_reviews_count,
        }
    
    def get_location_string(self) -> str:
        """Get location string for parsing."""
        # Prefer full address, fallback to location
        return self.job_location or self.location
    
    def _parse_salary(self) -> tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        """
        Parse salary_formatted into min/max/currency/period.
        
        Examples:
        - "$50,000 - $70,000 a year"
        - "€50k-€70k"
        - "$25 - $35 an hour"
        
        Returns:
            (min_amount, max_amount, currency_code, period)
        """
        if not self.salary_formatted:
            return None, None, None, None
        
        salary_str = self.salary_formatted
        
        # Extract currency symbol
        currency_match = re.search(r'[$€£¥]', salary_str)
        currency_symbol = currency_match.group() if currency_match else None
        
        # Map symbols to codes
        currency_map = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}
        currency_code = currency_map.get(currency_symbol, 'USD')
        
        # Detect period (year, month, hour, week)
        period = None
        if 'year' in salary_str.lower() or 'annual' in salary_str.lower():
            period = 'yearly'
        elif 'month' in salary_str.lower():
            period = 'monthly'
        elif 'hour' in salary_str.lower():
            period = 'hourly'
        elif 'week' in salary_str.lower():
            period = 'weekly'
        
        # Extract numbers (handle k/K for thousands, commas)
        # Pattern: number with optional comma and decimal, followed by optional k/K
        numbers = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*([kK])?', salary_str)
        
        if len(numbers) >= 2:
            min_val, min_mult = numbers[0]
            max_val, max_mult = numbers[1]
            
            # Remove commas and convert to float
            min_amount = float(min_val.replace(',', ''))
            max_amount = float(max_val.replace(',', ''))
            
            # Apply multiplier if present
            if min_mult and min_mult.lower() == 'k':
                min_amount *= 1000
            if max_mult and max_mult.lower() == 'k':
                max_amount *= 1000
            
            return min_amount, max_amount, currency_code, period
        elif len(numbers) == 1:
            # Single value (e.g., "Up to $50k")
            val, mult = numbers[0]
            amount = float(val.replace(',', ''))
            if mult and mult.lower() == 'k':
                amount *= 1000
            return amount, amount, currency_code, period
        
        return None, None, None, None
    
    def to_db_dict(self, company_id: UUID, location_id: UUID) -> Dict[str, Any]:
        """Convert to database insert format for job_postings table."""
        salary_min, salary_max, currency, period = self._parse_salary()
        
        return {
            "source": "indeed",
            "indeed_job_id": self.jobid,
            "linkedin_job_id": None,  # Not applicable for Indeed jobs
            "company_id": str(company_id),
            "location_id": str(location_id),
            "title": self.job_title,
            "employment_type": self.job_type,
            "posted_date": self.date_posted_parsed.isoformat() if self.date_posted_parsed else None,
            "posted_time_ago": self.date_posted,
            "base_salary_min": salary_min,
            "base_salary_max": salary_max,
            "salary_currency": currency,
            "salary_period": period,
            "job_url": self.url,
            "apply_url": self.apply_link,
            "application_available": bool(self.apply_link),
            # Indeed doesn't provide these fields:
            "seniority_level": None,
            "industries": [],
            "function_areas": [],
            "num_applicants": None,
        }
    
    def get_description_dict(self, job_posting_id: UUID) -> Dict[str, Any]:
        """Get job description data for insertion."""
        # Build summary from benefits and qualifications
        summary_parts = []
        if self.benefits:
            summary_parts.append(f"Benefits: {', '.join(self.benefits)}")
        if self.qualifications:
            summary_parts.append(f"Qualifications: {self.qualifications}")
        
        summary = " | ".join(summary_parts) if summary_parts else None
        
        # Use formatted description if available, otherwise plain description
        html_description = self.job_description_formatted or self.description
        
        return {
            "job_posting_id": str(job_posting_id),
            "summary": summary,
            "full_description_html": html_description,
            "full_description_text": self.description_text,
        }
