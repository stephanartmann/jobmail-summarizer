"""Unit tests for cache-related functions in utils.py."""
import os
import json
import pytest
from pathlib import Path
from utils import load_job_nonlinks_cache, save_job_nonlinks_cache, remember_non_job_link

def test_load_job_nonlinks_cache(cache_file,test_data, monkeypatch):
    """Test loading cache from a file."""
    # Create a temporary cache file with the expected structure
    with open(cache_file, 'w') as f:
        json.dump(test_data, f)
    
    # Patch the CACHE_FILE constant
    monkeypatch.setattr('utils.CACHE_FILE', str(cache_file))
    
    # Test loading
    cache = load_job_nonlinks_cache()
    assert cache == test_data

def test_load_nonexistent_cache(cache_file, monkeypatch):
    """Test loading a non-existent cache file returns default structure."""
    # Point to a non-existent file
    monkeypatch.setattr('utils.CACHE_FILE', str(cache_file))
    
    cache = load_job_nonlinks_cache()
    assert cache == {"version": "1.0", "cache": {}}

def test_save_job_nonlinks_cache(cache_file,test_data, monkeypatch):
    """Test saving cache to a file."""
    
    # Patch the CACHE_FILE constant
    monkeypatch.setattr('utils.CACHE_FILE', str(cache_file))
    
    # Test saving
    save_job_nonlinks_cache(test_data)
    
    # Verify file was created and contains correct data
    assert cache_file.exists()
    loaded_data = json.loads(cache_file.read_text())
    assert loaded_data == test_data

def test_remember_non_job_link(cache_file, monkeypatch):
    """Test adding a non-job link to cache."""
    # Point to a non-existent file
    monkeypatch.setattr('utils.CACHE_FILE', str(cache_file))
    update_complete = remember_non_job_link("test@example.com", "https://example.com/unsubscribe")
    
    assert update_complete
    updated_cache = load_job_nonlinks_cache()
    assert "test@example.com" in updated_cache["cache"]
    assert "https://example.com/unsubscribe" in updated_cache["cache"]["test@example.com"]
    assert len(updated_cache["cache"]["test@example.com"]) == 1

def test_remember_non_job_link_existing_sender(cache_file, monkeypatch):
    """Test adding a non-job link for existing sender."""
    # Point to a non-existent file
    monkeypatch.setattr('utils.CACHE_FILE', str(cache_file))
    update_complete = remember_non_job_link("test@example.com", "https://example.com/unsubscribe")
    assert update_complete

    update_complete = remember_non_job_link("test@example.com", "https://example.com/settings")
    assert update_complete

    updated_cache = load_job_nonlinks_cache()

    assert len(updated_cache["cache"]["test@example.com"]) == 2
    assert "https://example.com/settings" in updated_cache["cache"]["test@example.com"]
    assert "https://example.com/unsubscribe" in updated_cache["cache"]["test@example.com"]

def test_remember_non_job_link_duplicate():
    """Test adding a duplicate non-job link."""
    update_complete = remember_non_job_link("test@example.com", "https://example.com/unsubscribe")
    assert update_complete
    update_complete = remember_non_job_link("test@example.com", "https://example.com/unsubscribe")
    assert update_complete
    updated_cache = load_job_nonlinks_cache()
    
    # Should not add duplicate
    assert len(updated_cache["cache"]["test@example.com"]) == 1

def test_remember_non_job_link_with_remove_after():
    """Test that remove_after parameter works correctly."""
    update_complete = remember_non_job_link(
        "test@example.com", 
        "https://example.com/unsubscribe?param=value", 
        remove_after=['?'],
    )
    assert update_complete
    updated_cache = load_job_nonlinks_cache()
    assert "test@example.com" in updated_cache["cache"]
    assert "https://example.com/unsubscribe" in updated_cache["cache"]["test@example.com"]
    assert len(updated_cache["cache"]["test@example.com"]) == 1
    