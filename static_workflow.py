# %%
import os
import time
import logging
from datetime import datetime
import openai
from dotenv import load_dotenv
from typing import Callable,Optional
import json

from utils import extract_job_links, get_chrome_driver, get_page_content_with_driver
from selenium import webdriver

# %% Load environment variables
load_dotenv()

# %% Internal functions
def summarize_content(content:str,driver:webdriver.Chrome):
    # Prompt for job summarization
    definition_prompt = """
    You are a job listing summarizer. The user provides a webpage content, extract and summarize the following information.
    You must respond in JSON format with the following structure:
    {
    "firma*": "Company name",
    "ort*": "Location/City",
    "home_office_moeglich*": "Yes/No",
    "pensum_moeglich*": "[80%, 60%] or [80%] or [60%]",
    "festanstellung*": "Yes/No",
    "grundausbildung*": ["List of required basic education"],
    "berufserfahrung*": ["List of required professional experience"],
    "strasse_hausnummer*": "City, Street and house number if available, else rough address if available",
    "sichere_anstellung": "Explanation for the security status",
    "stress": "Might the job be stressful? Why?",
    "ethische_probleme": "Potential ethical issues"
    }

    If the site is not a job posting (e.g. an unsubscribe link), return "FALSE" (without quotation marks)
    """
    # Download page content
    page_content = get_page_content_with_driver(url, driver)

    # Summarize page content
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": definition_prompt},
                {"role": "user", "content": page_content}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        if result == "FALSE":
            ignore_webpage_in_future(SENDER_EMAIL, url)
            return {}
        analysis = json.loads(result)  # Parse JSON response
        return analysis
    except Exception as e:
        print(f"Error analyzing email: {str(e)}")
        return {}



def check_if_login(url, page_content):
    """
    Use GPT-3.5 to analyze the webpage and determine if it's a job page or login page
    Returns: (is_job_page: bool, is_login_page: bool, login_fields: dict)
    """
    try:
        definition_prompt = f"""
        You are a web page analyzer. The user provides an URL and page content for you to determine:
        1. If this is a job listing page
        2. If this is a login page
        3. If it's a login page, identify the username and password field selectors
                
        Format your response as JSON:
        {{
            "is_job_page": true/false,
            "is_login_page": true/false,
            "login_fields": {{
                "username_selector": "CSS selector",
                "password_selector": "CSS selector",
                "submit_selector": "CSS selector"
            }}
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": definition_prompt},
                {"role": "user", "content": f"URL: {url}\nPage content:\n{page_content}"}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        analysis = json.loads(result)  # Parse JSON response
        return (analysis["is_job_page"], analysis["is_login_page"], analysis["login_fields"])
    except Exception as e:
        print(f"Error analyzing webpage: {str(e)}")
        return (False, False, {})


# %% Functions to be called by other scripts
def summarize_website(url:str,sender:str):
    driver = get_chrome_driver()
    page_content = get_page_content_with_driver(url, driver,markdown_output=False)
    is_job_page, is_login_page, login_fields = check_if_login(url, page_content)
    if is_login_page:
        if not login_to_webpage(url, login_fields):
            return {}
        page_content = get_page_content_with_driver(url, driver,markdown_output=False)
        is_job_page, is_login_page, login_fields = check_if_login(url, page_content)
    if is_job_page:
        return summarize_content(get_page_content_with_driver(url, driver), driver)
    return {}


# %%
