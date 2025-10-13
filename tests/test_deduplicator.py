"""Pytest tests for deduplication logic."""

import pytest
from uuid import uuid4
from ingestion.deduplicator import (
    check_job_exists,
    fields_have_changed,
    calculate_data_hash,
    should_update_job,
    get_changed_fields
)


class TestCheckJobExists:
    """Test job existence checking."""
    
    def test_job_does_not_exist(self, monkeypatch):
        """Test checking for non-existent job."""
        # Mock the database call
        def mock_get_job(linkedin_job_id):
            return None
        
        from database import client
        monkeypatch.setattr(client.db, "get_job_by_linkedin_id", mock_get_job)
        
        exists, job_id, data = check_job_exists("nonexistent_job_id")
        
        assert exists is False
        assert job_id is None
        assert data is None
    
    def test_job_exists(self, monkeypatch):
        """Test checking for existing job."""
        # Mock the database call
        def mock_get_job(linkedin_job_id):
            return {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "linkedin_job_id": "test_job_123",
                "title": "Data Engineer"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_job_by_linkedin_id", mock_get_job)
        
        exists, job_id, data = check_job_exists("test_job_123")
        
        assert exists is True
        assert job_id is not None
        assert data is not None
        assert data["linkedin_job_id"] == "test_job_123"


class TestFieldsHaveChanged:
    """Test field change detection."""
    
    def test_no_changes(self):
        """Test when no fields have changed."""
        old_data = {
            "title": "Data Engineer",
            "num_applicants": 100,
            "salary": 50000
        }
        new_data = {
            "title": "Data Engineer",
            "num_applicants": 100,
            "salary": 50000
        }
        
        result = fields_have_changed(old_data, new_data, ["title", "num_applicants"])
        assert result is False
    
    def test_field_changed(self):
        """Test when a field has changed."""
        old_data = {
            "title": "Data Engineer",
            "num_applicants": 100
        }
        new_data = {
            "title": "Senior Data Engineer",
            "num_applicants": 100
        }
        
        result = fields_have_changed(old_data, new_data, ["title", "num_applicants"])
        assert result is True
    
    def test_numeric_field_changed(self):
        """Test when numeric field changes."""
        old_data = {"num_applicants": 100}
        new_data = {"num_applicants": 150}
        
        result = fields_have_changed(old_data, new_data, ["num_applicants"])
        assert result is True
    
    def test_none_to_value_change(self):
        """Test change from None to value."""
        old_data = {"salary": None}
        new_data = {"salary": 50000}
        
        result = fields_have_changed(old_data, new_data, ["salary"])
        assert result is True
    
    def test_value_to_none_change(self):
        """Test change from value to None."""
        old_data = {"salary": 50000}
        new_data = {"salary": None}
        
        result = fields_have_changed(old_data, new_data, ["salary"])
        assert result is True
    
    def test_missing_field(self):
        """Test when field is missing in one dict."""
        old_data = {"title": "Data Engineer"}
        new_data = {"title": "Data Engineer"}
        
        # Field not in either dict
        result = fields_have_changed(old_data, new_data, ["missing_field"])
        assert result is False


class TestCalculateDataHash:
    """Test data hashing."""
    
    def test_hash_consistency(self):
        """Test that same data produces same hash."""
        job_data = {
            "title": "Data Engineer",
            "num_applicants": 100,
            "base_salary_min": 70000,
            "base_salary_max": 90000,
            "employment_type": "Full-time",
            "seniority_level": "Mid-Senior"
        }
        
        hash1 = calculate_data_hash(job_data)
        hash2 = calculate_data_hash(job_data)
        
        assert hash1 == hash2
    
    def test_hash_changes_with_data(self):
        """Test that different data produces different hash."""
        job_data1 = {
            "title": "Data Engineer",
            "num_applicants": 100
        }
        job_data2 = {
            "title": "Senior Data Engineer",
            "num_applicants": 100
        }
        
        hash1 = calculate_data_hash(job_data1)
        hash2 = calculate_data_hash(job_data2)
        
        assert hash1 != hash2
    
    def test_hash_ignores_extra_fields(self):
        """Test that hash only considers relevant fields."""
        job_data1 = {
            "title": "Data Engineer",
            "num_applicants": 100,
            "extra_field": "ignored"
        }
        job_data2 = {
            "title": "Data Engineer",
            "num_applicants": 100,
            "different_extra": "also ignored"
        }
        
        hash1 = calculate_data_hash(job_data1)
        hash2 = calculate_data_hash(job_data2)
        
        # Should be same since extra fields are ignored
        assert hash1 == hash2
    
    def test_hash_is_md5_format(self):
        """Test that hash is valid MD5 format."""
        job_data = {"title": "Test"}
        hash_value = calculate_data_hash(job_data)
        
        # MD5 hash should be 32 characters
        assert len(hash_value) == 32
        # Should be hexadecimal
        assert all(c in '0123456789abcdef' for c in hash_value)


class TestShouldUpdateJob:
    """Test job update decision logic."""
    
    def test_no_update_needed(self):
        """Test when no update is needed."""
        existing_job = {
            "linkedin_job_id": "123",
            "title": "Data Engineer",
            "num_applicants": 100,
            "base_salary_min": 70000,
            "base_salary_max": 90000,
            "employment_type": "Full-time",
            "seniority_level": "Mid-Senior",
            "application_available": True
        }
        new_job_data = existing_job.copy()
        
        result = should_update_job(existing_job, new_job_data)
        assert result is False
    
    def test_update_needed_applicants_changed(self):
        """Test update when applicant count changes."""
        existing_job = {
            "linkedin_job_id": "123",
            "title": "Data Engineer",
            "num_applicants": 100
        }
        new_job_data = {
            "linkedin_job_id": "123",
            "title": "Data Engineer",
            "num_applicants": 150
        }
        
        result = should_update_job(existing_job, new_job_data)
        assert result is True
    
    def test_update_needed_salary_changed(self):
        """Test update when salary changes."""
        existing_job = {
            "linkedin_job_id": "123",
            "base_salary_min": 70000,
            "base_salary_max": 90000
        }
        new_job_data = {
            "linkedin_job_id": "123",
            "base_salary_min": 75000,
            "base_salary_max": 95000
        }
        
        result = should_update_job(existing_job, new_job_data)
        assert result is True
    
    def test_update_needed_title_changed(self):
        """Test update when title changes."""
        existing_job = {
            "linkedin_job_id": "123",
            "title": "Data Engineer"
        }
        new_job_data = {
            "linkedin_job_id": "123",
            "title": "Senior Data Engineer"
        }
        
        result = should_update_job(existing_job, new_job_data)
        assert result is True


class TestGetChangedFields:
    """Test changed fields detection."""
    
    def test_no_changes(self):
        """Test when no fields changed."""
        existing_job = {
            "title": "Data Engineer",
            "num_applicants": 100
        }
        new_job_data = {
            "title": "Data Engineer",
            "num_applicants": 100
        }
        
        changed = get_changed_fields(existing_job, new_job_data)
        assert changed == []
    
    def test_single_field_changed(self):
        """Test when one field changed."""
        existing_job = {
            "title": "Data Engineer",
            "num_applicants": 100
        }
        new_job_data = {
            "title": "Senior Data Engineer",
            "num_applicants": 100
        }
        
        changed = get_changed_fields(existing_job, new_job_data)
        assert "title" in changed
        assert len(changed) == 1
    
    def test_multiple_fields_changed(self):
        """Test when multiple fields changed."""
        existing_job = {
            "title": "Data Engineer",
            "num_applicants": 100,
            "salary": 50000
        }
        new_job_data = {
            "title": "Senior Data Engineer",
            "num_applicants": 150,
            "salary": 60000
        }
        
        changed = get_changed_fields(existing_job, new_job_data)
        assert "title" in changed
        assert "num_applicants" in changed
        assert "salary" in changed
        assert len(changed) == 3
    
    def test_new_field_ignored(self):
        """Test that new fields not in existing job are ignored."""
        existing_job = {
            "title": "Data Engineer"
        }
        new_job_data = {
            "title": "Data Engineer",
            "new_field": "value"
        }
        
        changed = get_changed_fields(existing_job, new_job_data)
        # new_field should not be in changed list
        assert "new_field" not in changed
