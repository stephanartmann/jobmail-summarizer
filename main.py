import sys
import os
import shutil
from datetime import datetime
from utils import get_unread_emails, extract_job_links
from tools import login_to_webpage, get_page_content, get_next_monday_connections
import logging
import agent
import static_workflow
from typing import Callable, List

import pandas as pd

def job_link_extraction_pipeline():
    all_job_links = []
    # Get unread emails
    emails = get_unread_emails()
    if not emails:
        logging.info("No unread emails found.")
        return

    # Process each email
    for email_content, sender in emails:
        try:
            # Extract job links
            job_links = extract_job_links(email_content,sender)
            if job_links:
                logging.info(f"Found {len(job_links)} job links in email from {sender}:")
                for link in job_links:
                    logging.info(f"- {link}")
                    all_job_links.append((link,sender))
            else:
                logging.info("No job links found in email.")
        except Exception as e:
            logging.error(f"Error in agent pipeline: {str(e)}")
            raise
    return all_job_links

def summary_pipeline(summarizer: Callable[str,str]) -> List[dict]:
    """
    Pipeline: Get unread emails and extract job links
    """
    logging.info("Starting summary pipeline")
    job_links = job_link_extraction_pipeline()

    # For all links: sent them to agent to summarize
    summaries = []
    for link,sender in job_links:
        try:
            logging.info(f"Summarizing job link: {link}")
            summary = summarizer(link,sender)
            summaries.append(summary)
            logging.info(f"Summary: {summary}")
        except Exception as e:
            logging.error(f"Error summarizing job link: {str(e)}")
            raise
    return summaries


def main():
    # Check for --reset_cache flag
    reset_cache = False
    if "--reset_cache" in sys.argv:
        reset_cache = True
        sys.argv.remove("--reset_cache")

    # Handle cache reset if requested
    if reset_cache:
        cache_dir = ".cache"
        old_cache_dir = os.path.join(cache_dir, "old")
        
        # Create .cache/old directory if it doesn't exist
        os.makedirs(old_cache_dir, exist_ok=True)
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Move cache files to old directory with timestamp
        for file in os.listdir(cache_dir):
            if file == "old":
                continue
            src = os.path.join(cache_dir, file)
            if os.path.isfile(src):
                base, ext = os.path.splitext(file)
                new_name = f"{base}_{timestamp}{ext}"
                dst = os.path.join(old_cache_dir, new_name)
                logging.info(f"Moving {file} to {new_name} in .cache/old directory")
                shutil.move(src, dst)

    if len(sys.argv) < 2:
        print("Usage: python main.py [pipeline_name] [--reset_cache]", file=sys.stderr)
        print("Available pipelines:")
        print("  agent - Uses AI Agent to generate job summary")
        print("  static - Less flexible and potentially more expensive, but possibly more reliable. Based on several LLM calls.")
        print("\nOptional arguments:")
        print("  --reset_cache    Reset cache and move all cache files to .cache/old directory with timestamp")
        sys.exit(1)

    pipeline = sys.argv[1]
    if pipeline == 'agent':
        summaries = summary_pipeline(agent.summarize_website)
    elif pipeline == 'static':
        summaries = summary_pipeline(static_workflow.summarize_website)
    else:
        print(f"Invalid pipeline short name: {pipeline} Should be one of 'agent' or 'static'")
        sys.exit(1)
    
    # Convert summaries to markdown table
    md_table = pd.DataFrame(summaries).to_markdown()
    
    # Send email
    send_email("Job Summaries", md_table)
    

    
if __name__ == "__main__":
    main()
