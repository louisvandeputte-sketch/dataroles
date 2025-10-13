"""Data normalization utilities for job postings."""

import re
from typing import Dict, Any, Optional
from loguru import logger


def normalize_company(raw_company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize company data for database insertion.
    
    Args:
        raw_company_data: Raw company dict from LinkedIn
    
    Returns:
        Cleaned company data
    """
    normalized = {}
    
    # Clean company name
    name = raw_company_data.get("name", "").strip()
    if not name:
        logger.warning("Company name is empty")
    normalized["name"] = name
    
    # LinkedIn ID
    linkedin_id = raw_company_data.get("linkedin_company_id")
    normalized["linkedin_company_id"] = linkedin_id.strip() if linkedin_id else None
    
    # URLs - validate format
    company_url = raw_company_data.get("company_url", "")
    if company_url and not company_url.startswith("http"):
        company_url = f"https://{company_url}"
    normalized["company_url"] = company_url or None
    
    logo_url = raw_company_data.get("logo_url", "")
    normalized["logo_url"] = logo_url if logo_url and logo_url.startswith("http") else None
    
    # Industry
    normalized["industry"] = raw_company_data.get("industry", "").strip() or None
    
    return normalized


def normalize_location(location_string: str) -> Dict[str, Any]:
    """
    Parse location string into structured components.
    
    Args:
        location_string: Location string like "City, State, Country" or "Belgium"
    
    Returns:
        Dictionary with parsed location fields
    """
    parts = [p.strip() for p in location_string.split(',')]
    
    normalized = {
        "full_location_string": location_string.strip()
    }
    
    if len(parts) == 1:
        # Just country or city
        part = parts[0]
        if len(part) == 2:  # Likely country code
            normalized["country_code"] = part.upper()
        else:
            normalized["city"] = part
    elif len(parts) == 2:
        # City, State/Country
        normalized["city"] = parts[0]
        if len(parts[1]) == 2:  # State abbreviation
            normalized["region"] = parts[1].upper()
        elif len(parts[1]) <= 3:  # Could be state code
            normalized["region"] = parts[1].upper()
        else:
            normalized["country_code"] = None
    else:
        # City, State, Country
        normalized["city"] = parts[0]
        normalized["region"] = parts[1]
        if len(parts[2]) == 2:
            normalized["country_code"] = parts[2].upper()
    
    return normalized


def normalize_job_description(html: Optional[str]) -> Optional[str]:
    """
    Strip HTML tags and clean job description for text version.
    
    Args:
        html: Job description with HTML formatting
    
    Returns:
        Clean text version
    """
    if not html:
        return None
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    
    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#x27;', "'")
    text = text.replace('&#x2019;', "'")
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text if text else None


def validate_url(url: Optional[str]) -> Optional[str]:
    """
    Ensure URL has proper schema.
    
    Args:
        url: URL string that may or may not have http(s)://
    
    Returns:
        URL with proper schema or None
    """
    if not url:
        return None
    
    url = url.strip()
    if not url:
        return None
    
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    return url


def parse_industries(industries_string: Optional[str]) -> list[str]:
    """
    Parse comma-separated industries string into list.
    
    Args:
        industries_string: "Industry1, Industry2, Industry3"
    
    Returns:
        List of industry strings
    """
    if not industries_string:
        return []
    
    return [i.strip() for i in industries_string.split(',') if i.strip()]
