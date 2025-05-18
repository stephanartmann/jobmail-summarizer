# %%
import os
import time
import logging
from datetime import datetime
from tools import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
from typing import Callable,Optional
import json

from utils import get_unread_emails, extract_job_links, summarize_job_listing, send_email


# Load environment variables
load_dotenv()



def summary(page_content):
    # Prompt for job summarization
    definition_prompt = """
    You are a job listing summarizer. For each job listing, extract and summarize the following information:
    1. Job Title
    2. Company Name
    3. Location
    4. Job Type (Full-time, Part-time, etc.)
    5. Key Responsibilities (top 3)
    6. Required Skills (top 3)
    7. Salary Range (if available)

    Format the output as a markdown table with these columns:
    | Job Title | Company | Location | Type | Key Responsibilities | Required Skills | Salary |

    For each job, provide a concise summary of 1-2 sentences.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": definition_prompt},
                {"role": "user", "content": page_content}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        analysis = json.loads(result)  # Parse JSON response
        return (analysis)
    except Exception as e:
        print(f"Error analyzing email: {str(e)}")
        return (False)

def check_if_login(url, page_content):
    """
    Use GPT-4 to analyze the webpage and determine if it's a job page or login page
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

def is_job_email(email_content):
    """
    Use OpenAI to determine if an email is job-related.

    Deprecated: instead, we focus on a jobmail folder in gmail where we assume that all mails
    are job-related.
    """
    try:
        definition_prompt = f"""
        You are an email classifier. Analyze the email content that the user provides
        and determine if it is a job-related email.
        An email is considered job-related if it contains:
        1. Job listings or job opportunities
        2. Recruiting or hiring information
        3. Job application instructions
        4. Career opportunities
        
        Respond ONLY with 'yes' if it's job-related, or 'no' if it's not.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": definition_prompt},
                {"role": "user", "content": email_content}
            ]
        )
        
        answer = response.choices[0].message.content.strip().lower()
        return answer == 'yes'
    except Exception as e:
        print(f"Error classifying email: {str(e)}")
        return False



# %%
