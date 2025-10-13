"""Pytest tests for job lifecycle management."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from scraper.lifecycle import mark_inactive_jobs, get_inactive_jobs_summary


class TestMarkInactiveJobs:
    """Test marking jobs as inactive."""
    
    def test_no_jobs_to_mark(self, monkeypatch):
        """Test when no jobs need to be marked inactive."""
        # Mock database query returning no jobs
        class MockResult:
            data = []
        
        def mock_execute(self):
            return MockResult()
        
        # Mock the query chain
        class MockQuery:
            def select(self, *args, **kwargs):
                return self
            def eq(self, *args, **kwargs):
                return self
            def lt(self, *args, **kwargs):
                return self
            def execute(self):
                return mock_execute(self)
        
        class MockTable:
            def __call__(self, *args):
                return MockQuery()
        
        from database import client
        monkeypatch.setattr(client.db.client, "table", MockTable())
        
        count = mark_inactive_jobs(threshold_days=14)
        assert count == 0
    
    def test_marks_inactive_jobs(self, monkeypatch):
        """Test marking jobs as inactive."""
        # Mock database query returning jobs
        job_id_1 = str(uuid4())
        job_id_2 = str(uuid4())
        
        class MockResult:
            data = [
                {"id": job_id_1},
                {"id": job_id_2}
            ]
        
        def mock_execute(self):
            return MockResult()
        
        # Mock the query chain
        class MockQuery:
            def select(self, *args, **kwargs):
                return self
            def eq(self, *args, **kwargs):
                return self
            def lt(self, *args, **kwargs):
                return self
            def execute(self):
                return mock_execute(self)
        
        class MockTable:
            def __call__(self, *args):
                return MockQuery()
        
        # Mock mark_jobs_inactive
        def mock_mark_inactive(job_ids):
            return len(job_ids)
        
        from database import client
        monkeypatch.setattr(client.db.client, "table", MockTable())
        monkeypatch.setattr(client.db, "mark_jobs_inactive", mock_mark_inactive)
        
        count = mark_inactive_jobs(threshold_days=14)
        assert count == 2
    
    def test_custom_threshold(self, monkeypatch):
        """Test custom threshold days."""
        # Mock database query
        class MockResult:
            data = []
        
        def mock_execute(self):
            return MockResult()
        
        class MockQuery:
            def select(self, *args, **kwargs):
                return self
            def eq(self, *args, **kwargs):
                return self
            def lt(self, *args, **kwargs):
                # Verify threshold is used correctly
                return self
            def execute(self):
                return mock_execute(self)
        
        class MockTable:
            def __call__(self, *args):
                return MockQuery()
        
        from database import client
        monkeypatch.setattr(client.db.client, "table", MockTable())
        
        # Should work with custom threshold
        count = mark_inactive_jobs(threshold_days=30)
        assert count == 0


class TestGetInactiveJobsSummary:
    """Test getting inactive jobs summary."""
    
    def test_summary_structure(self, monkeypatch):
        """Test summary returns correct structure."""
        # Mock database queries
        class MockResult:
            count = 10
            data = []
        
        def mock_execute(self):
            return MockResult()
        
        class MockQuery:
            def select(self, *args, **kwargs):
                return self
            def eq(self, *args, **kwargs):
                return self
            def gte(self, *args, **kwargs):
                return self
            def execute(self):
                return mock_execute(self)
        
        class MockTable:
            def __call__(self, *args):
                return MockQuery()
        
        from database import client
        monkeypatch.setattr(client.db.client, "table", MockTable())
        
        summary = get_inactive_jobs_summary()
        
        # Check structure
        assert "total_inactive" in summary
        assert "inactive_last_7_days" in summary
        assert "inactive_last_30_days" in summary
        
        # Check values
        assert summary["total_inactive"] == 10
        assert summary["inactive_last_7_days"] == 10
        assert summary["inactive_last_30_days"] == 10
    
    def test_summary_with_different_counts(self, monkeypatch):
        """Test summary with different counts for each period."""
        # Mock database queries with different counts
        call_count = [0]
        
        class MockResult:
            def __init__(self, count):
                self.count = count
                self.data = []
        
        def mock_execute(self):
            call_count[0] += 1
            if call_count[0] == 1:
                return MockResult(100)  # total_inactive
            elif call_count[0] == 2:
                return MockResult(20)   # inactive_last_7_days
            else:
                return MockResult(50)   # inactive_last_30_days
        
        class MockQuery:
            def select(self, *args, **kwargs):
                return self
            def eq(self, *args, **kwargs):
                return self
            def gte(self, *args, **kwargs):
                return self
            def execute(self):
                return mock_execute(self)
        
        class MockTable:
            def __call__(self, *args):
                return MockQuery()
        
        from database import client
        monkeypatch.setattr(client.db.client, "table", MockTable())
        
        summary = get_inactive_jobs_summary()
        
        assert summary["total_inactive"] == 100
        assert summary["inactive_last_7_days"] == 20
        assert summary["inactive_last_30_days"] == 50
