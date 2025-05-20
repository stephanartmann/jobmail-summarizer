import pytest
from unittest.mock import patch

from main import job_link_extraction_pipeline, summary_pipeline

def test_job_link_extraction_pipeline_returns_links():
    fake_emails = [("email content", "sender@example.com")]
    fake_links = ["http://job.example.com"]

    with patch("utils.get_unread_emails", return_value=fake_emails), \
         patch("utils.extract_job_links", return_value=fake_links):
        result = job_link_extraction_pipeline()
        assert result == [(fake_links[0], "sender@example.com")]

def test_summary_pipeline_calls_summarizer():
    fake_links = [("http://job.example.com", "sender@example.com")]
    fake_summary = {"summary": "Job summary"}

    with patch("main.job_link_extraction_pipeline", return_value=fake_links):
        def dummy_summarizer(link, sender):
            assert link == "http://job.example.com"
            assert sender == "sender@example.com"
            return fake_summary

        summaries = summary_pipeline(dummy_summarizer)
        assert summaries == [fake_summary]
