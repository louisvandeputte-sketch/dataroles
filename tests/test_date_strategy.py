"""Pytest tests for date range strategy."""

import pytest
from datetime import datetime, timedelta
from scraper.date_strategy import (
    determine_date_range,
    map_lookback_to_range,
    should_trigger_scrape
)


class TestMapLookbackToRange:
    """Test mapping lookback days to date ranges."""
    
    def test_one_day(self):
        """Test 1 day maps to past_24h."""
        assert map_lookback_to_range(1) == "past_24h"
    
    def test_less_than_one_day(self):
        """Test < 1 day maps to past_24h."""
        assert map_lookback_to_range(0) == "past_24h"
    
    def test_seven_days(self):
        """Test 7 days maps to past_week."""
        assert map_lookback_to_range(7) == "past_week"
    
    def test_three_days(self):
        """Test 3 days maps to past_week."""
        assert map_lookback_to_range(3) == "past_week"
    
    def test_thirty_days(self):
        """Test 30 days maps to past_month."""
        assert map_lookback_to_range(30) == "past_month"
    
    def test_more_than_thirty_days(self):
        """Test > 30 days maps to past_month."""
        assert map_lookback_to_range(60) == "past_month"


class TestDetermineDateRange:
    """Test date range determination logic."""
    
    def test_manual_override(self, monkeypatch):
        """Test manual lookback_days override."""
        # Mock database call (shouldn't be called)
        def mock_get_last_run(query, location):
            raise AssertionError("Should not call database with manual override")
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        date_range, days = determine_date_range("test", "test", lookback_days=5)
        assert date_range == "past_week"
        assert days == 5
    
    def test_first_run_no_history(self, monkeypatch):
        """Test first run returns past_month."""
        # Mock database call returning None
        def mock_get_last_run(query, location):
            return None
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        date_range, days = determine_date_range("Data Engineer", "Netherlands")
        assert date_range == "past_month"
        assert days == 30
    
    def test_daily_run(self, monkeypatch):
        """Test daily run returns past_24h."""
        # Mock database call returning yesterday's run
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": yesterday,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        date_range, days = determine_date_range("Data Engineer", "Netherlands")
        assert date_range == "past_24h"
        assert days == 1
    
    def test_weekly_run(self, monkeypatch):
        """Test weekly run returns past_week."""
        # Mock database call returning 5 days ago
        five_days_ago = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": five_days_ago,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        date_range, days = determine_date_range("Data Engineer", "Netherlands")
        assert date_range == "past_week"
        assert days == 7
    
    def test_monthly_run(self, monkeypatch):
        """Test monthly run returns past_month."""
        # Mock database call returning 20 days ago
        twenty_days_ago = (datetime.utcnow() - timedelta(days=20)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": twenty_days_ago,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        date_range, days = determine_date_range("Data Engineer", "Netherlands")
        assert date_range == "past_month"
        assert days == 30
    
    def test_large_gap(self, monkeypatch):
        """Test large gap (>30 days) returns past_month with warning."""
        # Mock database call returning 60 days ago
        sixty_days_ago = (datetime.utcnow() - timedelta(days=60)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": sixty_days_ago,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        date_range, days = determine_date_range("Data Engineer", "Netherlands")
        assert date_range == "past_month"
        assert days == 30


class TestShouldTriggerScrape:
    """Test scrape triggering logic."""
    
    def test_no_previous_run(self, monkeypatch):
        """Test triggers when no previous run."""
        def mock_get_last_run(query, location):
            return None
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        assert should_trigger_scrape("test", "test") is True
    
    def test_enough_time_passed(self, monkeypatch):
        """Test triggers when enough time has passed."""
        # Mock database call returning 8 hours ago
        eight_hours_ago = (datetime.utcnow() - timedelta(hours=8)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": eight_hours_ago,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        assert should_trigger_scrape("test", "test", min_interval_hours=6) is True
    
    def test_not_enough_time_passed(self, monkeypatch):
        """Test doesn't trigger when not enough time has passed."""
        # Mock database call returning 2 hours ago
        two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": two_hours_ago,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        assert should_trigger_scrape("test", "test", min_interval_hours=6) is False
    
    def test_custom_interval(self, monkeypatch):
        """Test custom minimum interval."""
        # Mock database call returning 10 hours ago
        ten_hours_ago = (datetime.utcnow() - timedelta(hours=10)).isoformat() + "Z"
        
        def mock_get_last_run(query, location):
            return {
                "completed_at": ten_hours_ago,
                "status": "completed"
            }
        
        from database import client
        monkeypatch.setattr(client.db, "get_last_successful_run", mock_get_last_run)
        
        # Should trigger with 6 hour interval
        assert should_trigger_scrape("test", "test", min_interval_hours=6) is True
        
        # Should not trigger with 12 hour interval
        assert should_trigger_scrape("test", "test", min_interval_hours=12) is False
