import sys
import os
import shutil
from datetime import datetime
from utils import get_unread_emails, extract_job_links
from tools import login_to_webpage, get_page_content, get_next_monday_connections

def agent_pipeline():
    """
    Agent Pipeline: Get unread emails and extract job links
    """
    try:
        # Get unread emails
        emails = get_unread_emails()
        if not emails:
            print("No unread emails found.")
            return

        # Process each email
        for email_content, sender in emails:
            # Extract job links
            job_links = extract_job_links(email_content,sender)
            if job_links:
                print(f"Found {len(job_links)} job links in email from {sender}:")
                for link in job_links:
                    print(f"- {link}")
            else:
                print("No job links found in email.")

    except Exception as e:
        print(f"Error in agent pipeline: {str(e)}")
        raise

def static_pipeline():
    """
    Static Pipeline: Currently same as agent pipeline
    """
    return agent_pipeline()

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
                print(f"Moving {file} to {new_name} in .cache/old directory")
                shutil.move(src, dst)

    if len(sys.argv) < 2:
        print("Usage: python main.py [pipeline_number] [--reset_cache]", file=sys.stderr)
        print("Available pipelines:")
        print("  agent - Get unread emails and extract job links")
        print("  static - Currently same as agent pipeline")
        print("\nOptional arguments:")
        print("  --reset_cache    Move all cache files to .cache/old directory with timestamp")
        sys.exit(1)

    pipeline = sys.argv[1]
    if pipeline == 'agent':
        agent_pipeline()
    elif pipeline == 'static':
        static_pipeline()
    else:
        print(f"Invalid pipeline number: {pipeline}")
        sys.exit(1)

if __name__ == "__main__":
    main()
