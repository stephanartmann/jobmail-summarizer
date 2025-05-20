# %%
import os
import time
from datetime import datetime
import pandas as pd
import openai
import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any, Tuple
import logging

import imaplib
import email
from email.header import decode_header
import os
from typing import List
import re

import json
from pathlib import Path

from docling.document_converter import DocumentConverter

# %% Logging and configs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CHROME_OPTIONS = {
    'headless': True,
    'no_sandbox': True,
    'disable_dev_shm_usage': True
}

# Load environment variables
load_dotenv()

# OpenAI API configuration
openai.api_key = os.getenv('OPENAI_API_KEY')

# Gmail API configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Email and LinkedIn configuration
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# LinkedIn configuration
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'



def get_chrome_driver() -> webdriver.Chrome:
    """Initialize Chrome driver"""
    try:
        chrome_install = ChromeDriverManager().install()
        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver")
        service = Service(chromedriver_path)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {str(e)}")
        raise


# %% Helper Functions



def extract_job_links_with_exceptions(content: str, exclude_patterns: List[str]) -> List[str]:
    """
    Extract all HTTPS links from email content while excluding links that contain specific patterns.
    
    Args:
        content: Email content to extract links from
        exclude_patterns: List of strings that, if present in a URL, will exclude that URL from results
        
    Returns:
        List of extracted HTTPS links that don't match any exclude patterns
    """
    # Find all HTTPS links using regex and exclude trailing non-URL characters
    https_links = re.findall(r'https://[\w.-]+(?:/[\w.-]*)*(?:\?[\w.-]*)?(?:#[\w.-]*)?(?=[\s>]|$)', content)
    
    # Filter out links that contain any of the exclude patterns
    filtered_links = list(set([
        link for link in https_links 
        if not any(pattern in link for pattern in exclude_patterns)
    ]))
    
    return filtered_links

# %% Helper Functions
def get_joblink_tags(page_content:str)->List[str]:
    """
    Use GPT-4o to return html tags of job links so that we can add them as keywords
    to extract_job_links
    """
    try:
        prompt = f"""
        You are a job link extractor. Extract the html tags (href) of job links from the page content
        that the user provides.
        
        Please ignore links pointing to "further jobs" or subscription settings etc. 
        Format your response as a list of tags: ["tag1", "tag2", ...]
        """

        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": page_content}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        analysis = json.loads(result)  # Parse JSON response
        return (analysis)
    except Exception as e:
        print(f"Error analyzing email: {str(e)}")
        return (False)

def exclude_non_joblinks(page_content:str)->List[str]:
    """
    Use GPT-4o to return html patterns so that we can exlude non-joblinks
    """
    try:
        prompt = f"""
        You are a non-job link extractor. Extract the html patterns https://... of non-job links from the page content
        that the user provides. Make the patterns as short as possible so that they are the specific 
        start of the link that does not point to a job.
        
        In particular, detect links pointing to "further jobs" (that are not explicit job links) 
        or subscription settings (e.g. unsubscribe) or to app stores (e.g. google play, app store) etc. 
        Format your response as a list of patterns: ["pattern1", "pattern2", ...]
        """

        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": page_content}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        analysis = json.loads(result)  # Parse JSON response
        return (analysis)
    except Exception as e:
        print(f"Error analyzing email: {str(e)}")
        return (False)

def extract_job_links_by_tag(
    content: str,
    keywords: List[str] = ['job', 'apply'],
    min_link_length: int = 10
) -> List[str]:
    """
    Extract job-related links from HTML content.

    Args:
        content: HTML content to parse
        keywords: List of keywords to match in links
        min_link_length: Minimum length for valid links

    Returns:
        List of extracted job-related links
    """
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    
    try:
        for link in soup.find_all('a'):
            href = link.get('href')
        if href and any([keyword in href.lower() for keyword in keywords]):
                links.append(href)
        
        logger.info(f"Extracted {len(links)} job-related links")
        return links
    except Exception as e:
        logger.error(f"Error extracting links: {str(e)}")
        return []


def send_email(subject:str,body:str)->bool:
    """
    Send an email using SMTP

    Args:
        subject: Email subject
        body: Email body

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def load_job_nonlinks_cache() -> dict:
    """Load the job links cache from JSON file."""
    cache_file = Path(".cache/job_nonlinks_cache.json")
    if not cache_file.exists():
        return {"version": "1.0", "cache": {}}
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading cache: {str(e)}")
        return {"version": "1.0", "cache": {}}

def save_job_nonlinks_cache(cache: dict) -> None:
    """Save the job links cache to JSON file."""
    cache_file = Path(".cache/job_nonlinks_cache.json")
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving cache: {str(e)}")

# %% Functions to be imported by pipelines
def get_unread_emails() -> List[Tuple[str, str]]:
    """
    Retrieve content and sender information of unread emails in jobs folder from Gmail.
    
    Returns:
        List of tuples containing (email_body, sender) for each unread email
    """
    
    # Get environment variables
    email_user = os.getenv('EMAIL')
    email_pass = os.getenv('EMAIL_PASSWORD')
    email_folder = os.getenv('EMAIL_JOB_FOLDER', 'INBOX')
    
    if not email_user or not email_pass:
        raise ValueError("EMAIL and EMAIL_PASSWORD environment variables must be set")
    
    try:
        # Get IMAP server from environment variables
        imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        
        # Select the specified folder
        mail.select(email_folder)
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            raise Exception(f"Failed to search for unread emails: {status}")
        
        # Get the list of email IDs
        email_ids = messages[0].split()
        
        # Fetch content of each unread email
        email_contents = []
        for msg_num in email_ids:
            status, msg_data = mail.fetch(msg_num, '(RFC822)')
            if status != 'OK':
                continue
                
            # Parse the email message
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Get email body and sender
            sender = msg['From']
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        body = part.get_payload(decode=True).decode()
                        email_contents.append((body, sender))
                        break
            else:
                body = msg.get_payload(decode=True).decode()
                email_contents.append((body, sender))
        
        # Close the connection
        mail.close()
        mail.logout()
        
        return email_contents
        
    except Exception as e:
        print(f"Error fetching unread emails: {str(e)}")
        return []

def remember_non_job_link(sender: str, link: str, remove_after: List[str] = ['&','?']) -> bool:
    """
    Add a non-job link to the cache for a specific sender.
    If the sender doesn't exist in the cache, creates a new entry.
    
    Args:
        sender: Email address of the sender
        link: The non-job link to add
    """
    try:
        # Remove query parameters from link
        for param in remove_after:
            link = link.split(param)[0]

        # Load cache
        cache = load_job_nonlinks_cache()
        
        # Get sender's links or create new list
        if sender not in cache["cache"]:
            cache["cache"][sender] = []
        
        # Add link if not already present
        if link not in cache["cache"][sender]:
            cache["cache"][sender].append(link)
            
        # Save updated cache
        save_job_nonlinks_cache(cache)
        
    except Exception as e:
        logger.error(f"Error adding non-job link to cache: {str(e)}")
        return False
    return True
    
def extract_job_links(
    content: str,
    sender: str
    )->List[str]:
    """
    Extract job links from job mails, using cache if available.
    """
    try:
        # Load cache
        cache = load_job_nonlinks_cache()
        
        # Check if sender is in cache
        if sender in cache["cache"]:
            exclude_patterns = cache["cache"][sender]
        else:   
            # If not in cache, extract links and update cache
            exclude_patterns = exclude_non_joblinks(content)
            
        links = extract_job_links_with_exceptions(content, exclude_patterns=exclude_patterns)
        
        # Update cache
        cache["cache"][sender] = exclude_patterns
        save_job_nonlinks_cache(cache)
        
        return links
        
    except Exception as e:
        logger.error(f"Error extracting job links: {str(e)}")
        return []
    
def get_page_content_with_driver(driver:webdriver.Chrome,url: str, markdown_output:bool=True) -> str:
    """
    Get page content from a URL

    Args:
        url: URL to retrieve content from

    Returns:
        Page content as a string
    """
    driver.get(url)
    time.sleep(15)  # Wait for content to load
    page_content = driver.page_source
    if markdown_output:
        os.makedirs(".cache/html", exist_ok=True)
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        with open(f".cache/html/{filename}.html", "w") as f:
            f.write(page_content)
        converter = DocumentConverter()
        return converter.convert(f".cache/html/{filename}.html").document.export_to_markdown()
    return page_content


def login_to_linkedin(driver:webdriver.Chrome)->bool:
    """
    Login to LinkedIn using provided credentials.

    Returns:
        True if login was successful, False otherwise
    """
    try:
        driver.get(LINKEDIN_LOGIN_URL)
        
        # Wait for email field and enter email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        email_field.send_keys(LINKEDIN_EMAIL)
        
        # Enter password
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys(LINKEDIN_PASSWORD)
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for successful login (e.g., check for profile page)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'profile-nav-item'))
        )
        
        logger.info("LinkedIn login successful")
        return True
    except Exception as e:
        logger.error(f"LinkedIn login failed: {str(e)}")
        return False

def login(driver:webdriver.Chrome,url:str, login_fields:Dict[str,str])->bool:
    """
    Handle login for any webpage using the provided selectors

    Args:
        url: URL to log in to
        login_fields: Dictionary of login field selectors, format: {"username_selector": "css selector for username", "password_selector": "css selector for password", "submit_selector": "css selector for submit button"}

    Returns:
        True if login was successful, False otherwise
    """
    try:
        driver.get(url)

        username = os.getenv('GENERIC_LOGIN_EMAIL')
        password = os.getenv('GENERIC_LOGIN_PASSWORD')
        
        # Wait for username field and enter username
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, login_fields["username_selector"]))
        )
        username_field.send_keys(username)
        
        # Enter password
        password_field = driver.find_element(By.CSS_SELECTOR, login_fields["password_selector"])
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, login_fields["submit_selector"])
        login_button.click()
        
        # Wait for login to complete
        time.sleep(15)
        
        # Check if login was successful by looking for common error indicators
        error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-error")
        return len(error_elements) == 0
    except Exception as e:
        print(f"Error logging into webpage: {str(e)}")
        return False

def get_mon_conns(to_location: str)->Dict:
    """
    Get transport connections for next Monday from opentransport API

    Args:
        to_location: Arrival location

    Returns:
        Dictionary containing the API response with connections
    """
    # Calculate next Monday's date
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7
    next_monday = today + timedelta(days=days_until_monday)
    next_monday_date = next_monday.strftime('%Y-%m-%d')

    # Set default time to 08:00
    time = "08:00"

    # Build API URL with parameters
    base_url = "http://transport.opendata.ch/v1/connections"
    params = {
        'from': os.getenv('HOME_ADDRESS'),
        'to': to_location,
        'date': next_monday_date,
        'time': time,
        'limit': 5  # Return up to 5 connections
    }

    # Make API request
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise exception for bad status codes
    
    return response.json()
# %%
