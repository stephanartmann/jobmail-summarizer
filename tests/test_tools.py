import pytest
from unittest.mock import patch, MagicMock

import tools

def test_login_to_webpage_linkedin():
    with patch("tools.login_to_linkedin", return_value=True):
        result = tools.login_to_webpage("https://linkedin.com", {})
        assert result is True

def test_login_to_webpage_generic():
    with patch("tools.login", return_value=True):
        result = tools.login_to_webpage(
            "https://example.com",
            {"username_selector": "#user", "password_selector": "#pass", "submit_selector": "#submit"}
        )
        assert result is True

def test_get_page_content():
    with patch("tools.get_page_content_with_driver", return_value="markdown content"):
        result = tools.get_page_content("https://example.com")
        assert result == "markdown content"
