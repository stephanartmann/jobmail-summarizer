"""Tests for OpenAI integration functions."""
import pytest
from unittest.mock import MagicMock, patch
from utils import get_joblink_tags, exclude_non_joblinks

@patch('utils.openai')
def test_get_joblink_tags(mock_openai):
    """Test getting job link tags using OpenAI."""
    # Setup mock client and response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '["job", "career"]'
    mock_openai.chat.completions.create.return_value = mock_response

    # Test the function
    result = get_joblink_tags("<html>test</html>")
    
    # Verify results
    assert isinstance(result, list)
    assert "job" in result
    assert "career" in result
    mock_openai.chat.completions.create.assert_called_once()

@patch('utils.openai')
def test_exclude_non_joblinks(mock_openai):
    """Test excluding non-job links using OpenAI."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '["unsubscribe", "settings"]'
    mock_openai.chat.completions.create.return_value = mock_response
    
    # Test the function
    result = exclude_non_joblinks("<html>test</html>")
    
    # Verify results
    assert isinstance(result, list)
    assert "unsubscribe" in result
    assert "settings" in result
    mock_openai.chat.completions.create.assert_called_once()

@patch('utils.openai')
def test_get_joblink_tags_error_handling(mock_openai):
    """Test error handling in get_joblink_tags."""
    # Make the API call raise an exception
    mock_openai.side_effect = Exception("API Error")
    
    # Test the function
    result = get_joblink_tags("<html>test</html>")
    
    # Should return False on error
    assert result is False
