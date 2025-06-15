"""Integration tests for email processing flow."""
import pytest
from unittest.mock import patch, MagicMock
from utils import extract_job_links, remember_non_job_link, get_unread_emails

def test_extract_job_links_with_cache():
    """Test job link extraction with cache integration."""
    # Setup test data
    content = """
    Check out this job: https://example.com/job/123
    Unsubscribe: https://example.com/unsubscribe
    """
    sender = "test@example.com"
    
    # First call - should process all links
    with patch('utils.load_job_nonlinks_cache', return_value={}), \
         patch('utils.save_job_nonlinks_cache') as mock_save:
        
        result = extract_job_links(content, sender)
        
        assert "https://example.com/job/123" in result
        assert "https://example.com/unsubscribe" not in result
        
        # Verify cache was saved
        assert mock_save.called
    
    # Second call with cache populated
    with patch('utils.load_job_nonlinks_cache', return_value={
        "test@example.com": ["unsubscribe"]
    }), patch('utils.save_job_nonlinks_cache') as mock_save:
        
        result = extract_job_links(content, sender)
        
        # Should still return the job link
        assert "https://example.com/job/123" in result
        # Should not have tried to save cache again
        assert not mock_save.called

@patch('imaplib.IMAP4_SSL')
def test_get_unread_emails(mock_imap):
    """Test retrieving unread emails."""
    # Setup mock IMAP server
    mock_conn = MagicMock()
    mock_imap.return_value = mock_conn
    
    # Mock IMAP responses
    mock_conn.login.return_value = ('OK', [b'Login successful'])
    mock_conn.select.return_value = ('OK', [b'1'])
    mock_conn.search.return_value = ('OK', [b'1 2 3'])
    
    # Mock email data
    email_data = {
        b'1': (b'1 (RFC822 {10}', b'From: sender@example.com\r\nTo: me@example.com\r\nSubject: Test\r\n\r\nBody'),
    }
    
    def fetch_mock(ids, _):
        return ('OK', [email_data.get(ids, (None, None))])
    
    mock_conn.fetch.side_effect = fetch_mock
    
    # Test the function
    with patch.dict('os.environ', {
        'EMAIL': 'test@example.com',
        'EMAIL_PASSWORD': 'password'
    }):
        emails = get_unread_emails()
        
        # Verify results
        assert len(emails) == 1
        assert emails[0][1] == 'sender@example.com'  # sender
        assert 'Body' in emails[0][0]  # body
