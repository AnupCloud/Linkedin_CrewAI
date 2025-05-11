from bs4 import BeautifulSoup
import re
import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


def parse_html_content(page_source: str, is_activity_page: bool = False):
    """
    Parses the HTML from the LinkedIn's profile and returns featured posts or recent activity.

    Args:
        page_source: The HTML content
        is_activity_page: Whether we're parsing activity page (recent posts) instead of featured section

    Returns:
        A list of containers representing LinkedIn posts
    """
    linkedin_soup = BeautifulSoup(page_source.encode("utf-8"), "lxml")
    
    if is_activity_page:
        # For recent activity page
        containers = linkedin_soup.find_all("div", {"class": "feed-shared-update-v2"})
        containers = [container for container in containers if 'activity' in container.get('data-urn', '')]
    else:
        # Try to find featured posts first
        featured_section = linkedin_soup.find("section", {"class": re.compile("featured")})
        
        if featured_section:
            # Find post containers within the featured section
            containers = featured_section.find_all("div", {"class": re.compile("occludable-update|feed-shared-update-v2")})
        else:
            # Fallback to looking for post containers throughout the page
            containers = linkedin_soup.find_all("div", {"class": re.compile("occludable-update|feed-shared-update-v2")})
    
    return containers


def get_post_content(container, selector=None, attributes=None):
    """
    Gets the content of a LinkedIn post container
    Args:
        container: The div container
        selector: The selector (optional)
        attributes: Attributes to be fetched (optional)

    Returns:
        The post content
    """
    try:
        if selector and attributes:
            element = container.find(selector, attributes)
            if element:
                return element.text.strip()
        else:
            # Try different selectors for post content
            content_selectors = [
                ("div", {"class": re.compile("update-components-text|feed-shared-update-v2__description-wrapper")}),
                ("span", {"class": re.compile("break-words")}),
                ("div", {"class": re.compile("feed-shared-text|feed-shared-inline-show-more-text")}),
                ("div", {"class": re.compile("display-flex feed-shared-update-v2__commentary")})
            ]
            
            for sel, attr in content_selectors:
                element = container.find(sel, attr)
                if element and element.text.strip():
                    return element.text.strip()
            
            # If none of the above worked, try to get any text content
            all_text = container.get_text(separator=' ', strip=True)
            if all_text:
                return all_text
                
    except Exception as e:
        print(f"Error extracting post content: {e}")
    
    return ""


def get_linkedin_posts(page_source: str):
    containers = parse_html_content(page_source, is_activity_page=True)
    posts = []

    for container in containers:
        post_content = get_post_content(container, "div", {"class": "update-components-text"})
        posts.append(post_content)

    return posts


def get_linkedin_featured_posts(page_source: str, is_activity_page: bool = False, is_company_page: bool = False):
    """
    Gets LinkedIn featured posts or recent posts
    
    Args:
        page_source: HTML content of the page
        is_activity_page: Whether we're parsing the activity page
        is_company_page: Whether we're parsing a company page
        
    Returns:
        A list of post contents
    """
    linkedin_soup = BeautifulSoup(page_source.encode("utf-8"), "lxml")
    posts = []
    
    # Debug: print page title to see what we're looking at
    page_title = linkedin_soup.find('title')
    print(f"Page title: {page_title.text if page_title else 'No title found'}")
    
    if is_company_page:
        # Company pages have different structure
        post_containers = linkedin_soup.find_all("div", {"class": re.compile("ember-view occludable-update|feed-shared-update-v2")})
        print(f"Found {len(post_containers)} potential post containers on company page")
    else:
        # Use the existing logic for other pages
        containers = parse_html_content(page_source, is_activity_page)
        post_containers = containers
        print(f"Found {len(post_containers)} potential post containers on regular page")
    
    for container in post_containers:
        post_content = get_post_content(container)
        if post_content and len(post_content) > 20:  # Ensure we have substantial content
            posts.append(post_content)
    
    print(f"Extracted {len(posts)} posts with substantial content")
    return posts


def scrape_linkedin_posts_fn() -> str:
    """
    A tool that can be used to scrape LinkedIn posts
    """
    linkedin_username = os.environ.get("LINKEDIN_EMAIL")
    linkedin_password = os.environ.get("LINKEDIN_PASSWORD")
    linkedin_profile_name = os.environ.get("LINKEDIN_PROFILE_NAME", "meta")  # Default to Meta's profile
    
    print(f"Scraping profile: {linkedin_profile_name}")
    
    if not (linkedin_username and linkedin_password):
        print("LinkedIn credentials not found in environment variables")
        return str(["No LinkedIn credentials found. Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables."])

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    # Uncomment if you need headless mode
    # chrome_options.add_argument("--headless")
    
    browser = webdriver.Chrome(options=chrome_options)
    
    try:
        # Login to LinkedIn
        print("Logging in to LinkedIn...")
        browser.get("https://www.linkedin.com/login")
        
        username_input = browser.find_element("id", "username")
        password_input = browser.find_element("id", "password")
        username_input.send_keys(linkedin_username)
        password_input.send_keys(linkedin_password)
        password_input.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        print("Waiting for login to complete...")
        time.sleep(5)
        
        # Check if login was successful
        if "feed" in browser.current_url or "checkpoint" in browser.current_url:
            print("Login successful")
        else:
            print(f"Current URL after login attempt: {browser.current_url}")
            
        # Navigate to company page first (more reliable public content)
        print(f"Navigating to profile: {linkedin_profile_name}")
        browser.get(f"https://www.linkedin.com/company/{linkedin_profile_name}/posts/")
        time.sleep(5)
        
        # Scroll down to load posts
        print("Scrolling to load posts...")
        for i in range(3):
            browser.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
            print(f"Scroll {i+1} complete")
        
        # Try to get posts from the company page
        print("Extracting posts...")
        page_source = browser.page_source
        posts = get_linkedin_featured_posts(page_source, is_company_page=True)
        
        if not posts:
            print("No posts found on company page, trying alternative approach...")
            # Try a different page format for user profiles
            browser.get(f"https://www.linkedin.com/in/{linkedin_profile_name}/recent-activity/")
            time.sleep(5)
            
            for i in range(3):
                browser.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)
            
            posts = get_linkedin_featured_posts(browser.page_source, is_activity_page=True)
        
        browser.quit()
        
        if posts:
            print(f"Found {len(posts)} posts")
            # Return just a few posts for analysis
            return str(posts[:3])
        else:
            print("No posts found on either page")
            return str(["Could not find any posts. Try using a company profile like 'meta' or 'google' by setting the LINKEDIN_PROFILE_NAME environment variable."])
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        browser.quit()
        return str([f"Error occurred during scraping: {str(e)}"])
