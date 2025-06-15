"""Unit tests for parsing functions in utils.py."""
import pytest
from utils import extract_job_links_with_exceptions, extract_job_links_by_tag

def test_extract_job_links_with_exclusions(sample_email_content):
    """Test that job links are extracted while excluding specified patterns."""
    exclusions = ["unsubscribe", "settings"]
    result = extract_job_links_with_exceptions(sample_email_content, exclusions)
    
    assert "https://example.com/job/123" in result
    assert "https://example.com/careers/456" in result
    assert "https://example.com/unsubscribe" not in result
    assert len(result) == 2
    
    result = extract_job_links_with_exceptions(sample_email_content, exclusions)
    
    assert "https://example.com/job/123" in result
    assert "https://example.com/careers/456" in result
    assert "https://example.com/unsubscribe" not in result
    assert len(result) == 2

def test_extract_job_links_by_tag(sample_html):
    """Test HTML parsing and job link extraction."""

    result = extract_job_links_by_tag(sample_html,['job','career'])
    
    assert "https://example.com/job/123" in result
    assert "https://example.com/careers/456" in result
    assert "https://example.com/unsubscribe" not in result
    assert len(result) == 2


@pytest.mark.parametrize("html,expected_links", [
    # URL - should be included as is
    ('<a href="https://example.com/job/123">Job</a>', ["https://example.com/job/123"]),
    # Empty HTML - should return empty list
    ('', []),
    # Non-HTTP link - should be excluded
    ('<a href="mailto:test@example.com">Email</a>', []),
    # Link without job-related keywords - should be excluded
    ('<a href="https://example.com/about">About</a>', []),
])
def test_extract_job_links_by_tag_edge_cases(html, expected_links):
    """Test edge cases for job link extraction."""
    result = extract_job_links_by_tag(html)
    assert result == expected_links

def test_extract_job_links_with_exceptions_empty_exclusions():
    """Test that all links are returned when no exclusions are provided."""
    content = """
    Job: https://example.com/job/123
    Unsubscribe: https://example.com/unsubscribe
    """
    result = extract_job_links_with_exceptions(content, [])
    assert len(result) == 2
    assert "https://example.com/job/123" in result
    assert "https://example.com/unsubscribe" in result
