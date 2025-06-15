"""Integration tests for login functionality."""
import pytest
from unittest.mock import MagicMock, patch
from utils import login_to_linkedin, login

def test_login_to_linkedin_success(mock_driver):
    """Test successful LinkedIn login."""
    # Setup mock elements
    mock_driver.find_element.return_value = MagicMock()
    
    # Mock environment variables
    with patch.dict('os.environ', {
        'LINKEDIN_EMAIL': 'test@example.com',
        'LINKEDIN_PASSWORD': 'password'
    }):
        result = login_to_linkedin(mock_driver)
        
        # Verify results
        assert result is True
        mock_driver.get.assert_called_with('https://www.linkedin.com/login')
        assert mock_driver.find_element.call_count >= 2  # At least username and password fields

@patch('utils.LINKEDIN_EMAIL', 'test@example.com')
@patch('utils.LINKEDIN_PASSWORD', 'password')
def test_login_to_linkedin_failure(mock_driver):
    """Test LinkedIn login failure."""
    # Make find_element raise an exception to simulate login failure
    mock_driver.find_element.side_effect = Exception("Element not found")
    
    result = login_to_linkedin(mock_driver)
    assert result is False

def test_generic_login_success(mock_driver):
    """Test generic login functionality."""
    # Setup mock elements
    mock_username = MagicMock()
    mock_password = MagicMock()
    mock_submit = MagicMock()
    
    # Configure side effects to return different elements
    def find_element_side_effect(by, value):
        if "username" in value:
            return mock_username
        elif "password" in value:
            return mock_password
        elif "submit" in value:
            return mock_submit
        return MagicMock()
    
    mock_driver.find_element.side_effect = find_element_side_effect
    
    # Test data
    login_fields = {
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "#submit"
    }
    
    # Test the function
    result = login(mock_driver, "https://example.com/login", login_fields)
    
    # Verify results
    assert result is True
    mock_username.send_keys.assert_called_once()
    mock_password.send_keys.assert_called_once()
    mock_submit.click.assert_called_once()
