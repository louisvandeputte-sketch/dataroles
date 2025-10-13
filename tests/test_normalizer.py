"""Pytest tests for data normalization utilities."""

import pytest
from ingestion.normalizer import (
    normalize_company,
    normalize_location,
    normalize_job_description,
    validate_url,
    parse_industries
)


class TestNormalizeCompany:
    """Test company normalization."""
    
    def test_normalize_complete_company(self):
        """Test normalizing company with all fields."""
        raw = {
            "name": "  Tech Corp  ",
            "linkedin_company_id": "12345",
            "company_url": "linkedin.com/company/techcorp",
            "logo_url": "https://example.com/logo.png",
            "industry": "Information Technology"
        }
        
        result = normalize_company(raw)
        
        assert result["name"] == "Tech Corp"
        assert result["linkedin_company_id"] == "12345"
        assert result["company_url"] == "https://linkedin.com/company/techcorp"
        assert result["logo_url"] == "https://example.com/logo.png"
        assert result["industry"] == "Information Technology"
    
    def test_normalize_company_missing_url_schema(self):
        """Test that URLs without http:// get it added."""
        raw = {
            "name": "Test Company",
            "company_url": "example.com"
        }
        
        result = normalize_company(raw)
        assert result["company_url"] == "https://example.com"
    
    def test_normalize_company_invalid_logo(self):
        """Test that invalid logo URLs are set to None."""
        raw = {
            "name": "Test Company",
            "logo_url": "not-a-url"
        }
        
        result = normalize_company(raw)
        assert result["logo_url"] is None
    
    def test_normalize_company_empty_fields(self):
        """Test handling of empty fields."""
        raw = {
            "name": "",
            "linkedin_company_id": "",
            "company_url": "",
            "industry": ""
        }
        
        result = normalize_company(raw)
        assert result["name"] == ""
        assert result["linkedin_company_id"] is None
        assert result["company_url"] is None
        assert result["industry"] is None
    
    def test_normalize_company_minimal(self):
        """Test with only required name field."""
        raw = {"name": "Minimal Corp"}
        
        result = normalize_company(raw)
        assert result["name"] == "Minimal Corp"
        assert result["linkedin_company_id"] is None


class TestNormalizeLocation:
    """Test location normalization."""
    
    def test_single_word_location(self):
        """Test single word location."""
        result = normalize_location("Belgium")
        assert result["full_location_string"] == "Belgium"
        assert result["city"] == "Belgium"
        assert result.get("country_code") is None
    
    def test_country_code(self):
        """Test two-letter country code."""
        result = normalize_location("NL")
        assert result["full_location_string"] == "NL"
        assert result["country_code"] == "NL"
    
    def test_city_state(self):
        """Test city and state."""
        result = normalize_location("New York, NY")
        assert result["full_location_string"] == "New York, NY"
        assert result["city"] == "New York"
        assert result["region"] == "NY"
    
    def test_city_state_country(self):
        """Test city, state, and country."""
        result = normalize_location("Amsterdam, North Holland, NL")
        assert result["full_location_string"] == "Amsterdam, North Holland, NL"
        assert result["city"] == "Amsterdam"
        assert result["region"] == "North Holland"
        assert result["country_code"] == "NL"
    
    def test_city_full_country(self):
        """Test city with full country name."""
        result = normalize_location("London, England, United Kingdom")
        assert result["city"] == "London"
        assert result["region"] == "England"
        # UK is not 2 letters, so no country_code
        assert result.get("country_code") is None


class TestNormalizeJobDescription:
    """Test job description normalization."""
    
    def test_remove_html_tags(self):
        """Test HTML tag removal."""
        html = "<div><p>This is a <strong>job</strong> description.</p></div>"
        result = normalize_job_description(html)
        assert result == "This is a job description."
    
    def test_decode_html_entities(self):
        """Test HTML entity decoding."""
        html = "Company &amp; Partners &lt;test&gt; &quot;quote&quot;"
        result = normalize_job_description(html)
        assert result == 'Company & Partners <test> "quote"'
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        html = "<p>Line 1</p>    <p>Line 2</p>"
        result = normalize_job_description(html)
        assert "  " not in result
    
    def test_none_input(self):
        """Test None input."""
        result = normalize_job_description(None)
        assert result is None
    
    def test_empty_string(self):
        """Test empty string."""
        result = normalize_job_description("")
        assert result is None
    
    def test_complex_html(self):
        """Test complex HTML with lists."""
        html = """
        <div>
            <h2>About the role</h2>
            <ul>
                <li>Requirement 1</li>
                <li>Requirement 2</li>
            </ul>
        </div>
        """
        result = normalize_job_description(html)
        assert "About the role" in result
        assert "Requirement 1" in result
        assert "<" not in result
        assert ">" not in result


class TestValidateUrl:
    """Test URL validation."""
    
    def test_url_with_https(self):
        """Test URL that already has https://."""
        url = "https://example.com"
        result = validate_url(url)
        assert result == "https://example.com"
    
    def test_url_with_http(self):
        """Test URL that already has http://."""
        url = "http://example.com"
        result = validate_url(url)
        assert result == "http://example.com"
    
    def test_url_without_schema(self):
        """Test URL without schema."""
        url = "example.com"
        result = validate_url(url)
        assert result == "https://example.com"
    
    def test_url_with_path(self):
        """Test URL with path."""
        url = "example.com/path/to/page"
        result = validate_url(url)
        assert result == "https://example.com/path/to/page"
    
    def test_none_url(self):
        """Test None URL."""
        result = validate_url(None)
        assert result is None
    
    def test_empty_url(self):
        """Test empty URL."""
        result = validate_url("")
        assert result is None
    
    def test_whitespace_url(self):
        """Test URL with whitespace."""
        url = "  example.com  "
        result = validate_url(url)
        assert result == "https://example.com"


class TestParseIndustries:
    """Test industry parsing."""
    
    def test_single_industry(self):
        """Test single industry."""
        result = parse_industries("Information Technology")
        assert result == ["Information Technology"]
    
    def test_multiple_industries(self):
        """Test multiple industries."""
        result = parse_industries("IT, Software, Consulting")
        assert result == ["IT", "Software", "Consulting"]
    
    def test_industries_with_whitespace(self):
        """Test industries with extra whitespace."""
        result = parse_industries("  IT  ,  Software  ,  Consulting  ")
        assert result == ["IT", "Software", "Consulting"]
    
    def test_none_input(self):
        """Test None input."""
        result = parse_industries(None)
        assert result == []
    
    def test_empty_string(self):
        """Test empty string."""
        result = parse_industries("")
        assert result == []
    
    def test_trailing_commas(self):
        """Test string with trailing commas."""
        result = parse_industries("IT, Software, ")
        assert result == ["IT", "Software"]
