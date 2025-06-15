"""Common test fixtures and utilities."""
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver instance."""
    return MagicMock()

@pytest.fixture
def sample_html():
    """Sample HTML content for testing HTML parsing."""
    return """
    <html><body>
        <a href="https://example.com/job/123">Job 1</a>
        <a href="https://example.com/unsubscribe">Unsubscribe</a>
        <a href="https://example.com/careers/456">Career</a>
    </body></html>
    """

@pytest.fixture
def sample_email_content():
    """Sample email content for testing email parsing."""
    return """
    Check out this job: https://example.com/job/123
    Or this one: https://example.com/careers/456
    Unsubscribe: https://example.com/unsubscribe
    """

@pytest.fixture
def temp_cache_file(tmp_path):
    """Create a temporary cache file for testing."""
    cache_file = tmp_path / "test_cache.json"
    cache_data = {
        "test@example.com": ["unsubscribe", "settings"]
    }
    cache_file.write_text(json.dumps(cache_data))
    return str(cache_file)

@pytest.fixture
def cache_file(tmp_path):
    """Create a temporary cache file path for testing."""
    return tmp_path / "test_cache.json"

@pytest.fixture
def test_data():
    """Sample test data for cache tests."""
    return {"version": "1.0", "cache": {"test@example.com": ["unsubscribe"]}}