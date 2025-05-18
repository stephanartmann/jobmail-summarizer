from utils import get_chrome_driver, get_page_content_with_driver, login_to_linkedin, login,get_mon_conns,remember_non_job_link
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langchain_core.tools import tool

from dotenv import load_dotenv

load_dotenv()
driver = get_chrome_driver()

@tool
def login_to_webpage(url:str, login_fields:Dict[str,str])->bool:
    """
    Handle login for any webpage using the provided selectors

    Args:
        url: URL to log in to
        login_fields: Dictionary of login field selectors, format: {"username_selector": "css selector for username", "password_selector": "css selector for password", "submit_selector": "css selector for submit button"}

    Returns:
        True if login was successful, False otherwise
    """
    if 'linkedin' in url:
        return login_to_linkedin(driver)
    return login(driver,url,login_fields)

@tool
def get_page_content(url:str)->str:
    """
    Get page content from a URL

    Args:
        url: URL to get content from

    Returns:
        Page content as a string
    """
    page_content = get_page_content_with_driver(driver,url)
    return page_content

@tool
def get_next_monday_connections(to_location: str) -> Dict:
    """
    Get transport connections for next Monday from opentransport API

    Args:
        to_location: Arrival location

    Returns:
        Dictionary containing the API response with connections
    """
    return get_mon_conns(to_location)
    
@tool
def ignore_webpage_in_future(sender:str,link:str,remove_after: List[str] = ['&','?']) -> bool:
    """
    Ignore a webpage in the future

    Args:
        sender: Email address of the sender
        link: The non-job link to add
        remove_after: List of strings before which the link will be cut before saving, e.g. ['&'] or ['&','?']
            would mean that a link like 'https://www.jobs.ch/123456789?param1=value1&param2=value2' would 
            be cut to 'https://www.jobs.ch/123456789'

    Returns:
        True if the webpage was successfully ignored, False otherwise
    """
    return remember_non_job_link(sender, link, remove_after)