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
    logging.info("Funcion login_to_webpage called with url: {} and login_fields: {}".format(url, login_fields))
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
    logging.info("Funcion get_page_content called with url: {}".format(url))
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
    logging.info("Funcion get_page_source called with url: {}".format(url))
    page_content = get_page_content_with_driver(driver,url,markdown_output=False)
    return page_content

@tool(parse_docstring=True)
def get_next_monday_connections(to_location: str) -> Dict:
    """
    Get transport connections for next Monday at 8 AM from opentransport API

    Args:
        to_location: Arrival location

    Returns:
        Dictionary containing the API response with connections
    """
    logging.info("Funcion get_next_monday_connections called with to_location: {}".format(to_location))
    return get_mon_conns(to_location)
    
@tool(parse_docstring=True)
def summarize_job(company: str,
    location: str,
    work_from_home: str,
    working_hours: str,
    permanent_position: str,
    basic_education: List[str],
    professional_experience: List[str],
    address: str,
    travel_time_public_transport_api: int,
    secure_job: str,
    stress: str,
    ethical_issues: str)->bool:
    """
    Create job summary

    Args:
        company: Company name. Take it from the job posting.
        location: Location/City. Take it from the job posting.
        work_from_home: Is work from home possible? Take it from the job posting.
        working_hours: [80%, 60%] or [80%] or [60%]. Take it from the job posting.
        permanent_position: Yes/No. Take it from the job posting.
        basic_education: List of required basic education. Take it from the job posting.
        professional_experience: List of required professional experience. Take it from the job posting.
        address: City, Street and house number if available, else rough address if available. Take it from the job posting.
        travel_time_public_transport_api: Average travel time in minutes (for next Monday at 8 AM from given address).
        secure_job: Is this job secure? Explanation for the security status. Feel free to use additional info you have about this company.
        stress: Might the job be stressful? Why? Feel free to use additional info you have about this company or job role.
        ethical_issues: Potential ethical issues. Feel free to use additional info you have about this company or job role.

    Returns:
        True if job was summarized successfully, False otherwise
    """
    logging.info("Funcion summarize_job called with company: {} and location: {}".format(company, location))
    return True