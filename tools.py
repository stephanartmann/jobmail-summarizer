# %%
from utils import get_chrome_driver, get_page_content_with_driver, login_to_linkedin, login,get_mon_conns,remember_non_job_link
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langchain_core.tools import tool
import logging
from dotenv import load_dotenv

# %%
load_dotenv()
driver = get_chrome_driver()

# %%
@tool(parse_docstring=True)
def login_to_webpage(url:str, login_fields:Dict[str,str])->bool:
    """
    Handle login for any webpage using the provided selectors

    Args:
        url: URL to log in to
        login_fields: Dictionary of login field selectors, format: {"username_selector": "css selector for username", "password_selector": "css selector for password", "submit_selector": "css selector for submit button"}

    Returns:
        True if login was successful, False otherwise
    """
    logging.info("Funciont login_to_webpage called with url: {} and login_fields: {}".format(url, login_fields))
    if 'linkedin' in url:
        return login_to_linkedin(driver)
    return login(driver,url,login_fields)

@tool(parse_docstring=True)
def get_page_content(url:str)->str:
    """
    Get page content from a URL in markdown format

    Args:
        url: URL to get content from

    Returns:
        Page content as a string in markdown format
    """
    logging.info("Funciont get_page_content called with url: {}".format(url))
    page_content = get_page_content_with_driver(driver,url)
    return page_content

@tool(parse_docstring=True)
def get_page_source(url:str)->str:
    """
    Get page content from a URL in html source code format

    Args:
        url: URL to get content from

    Returns:
        Page content as a string in html source code format
    """
    logging.info("Funciont get_page_source called with url: {}".format(url))
    page_content = get_page_content_with_driver(driver,url,markdown_output=False)
    return page_content

@tool(parse_docstring=True)
def get_next_monday_connections(to_location: str) -> Dict:
    """
    Get transport connections for next Monday from opentransport API

    Args:
        to_location: Arrival location

    Returns:
        Dictionary containing the API response with connections
    """
    logging.info("Funciont get_next_monday_connections called with to_location: {}".format(to_location))
    return get_mon_conns(to_location)
    
