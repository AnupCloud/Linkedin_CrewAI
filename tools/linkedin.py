import os
import time
import warnings
import random
import traceback

from crewai.tools import tool
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from tools.constant import (
    DEFAULT_MIN_DELAY, DEFAULT_MAX_DELAY,
    KEYSTROKE_MIN_DELAY, KEYSTROKE_MAX_DELAY,
    SCROLL_MIN_DELAY, SCROLL_MAX_DELAY,
    SHORT_PAGE_LOAD_WAIT, MEDIUM_PAGE_LOAD_WAIT, LONG_PAGE_LOAD_WAIT,
    SECURITY_CHECK_WAIT, MAX_FEATURED_ITEMS, MAX_ARTICLES, MAX_POSTS,
    BROWSER_OPTIONS
)


# Suppress warnings
warnings.filterwarnings("ignore", message="<built-in function callable> is not a Python type")
warnings.filterwarnings("ignore", category=DeprecationWarning, module='websockets')


class LinkedinToolException(Exception):
    def __init__(self):
        super().__init__("You need to set the LINKEDIN_EMAIL and LINKEDIN_PASSWORD env variables")


def random_delay(min_seconds=DEFAULT_MIN_DELAY, max_seconds=DEFAULT_MAX_DELAY):
    """
    Add a random delay between operations to mimic human behavior
    and avoid detection as a bot.

    Args:
        min_seconds: Minimum delay time in seconds
        max_seconds: Maximum delay time in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def extract_post_url(post_element):
    """
    Extract the URL from a LinkedIn post element

    Args:
        post_element: The Selenium WebElement representing a LinkedIn post

    Returns:
        The URL if found, otherwise None
    """
    try:
        # First look for "article" links which are more reliable
        article_link = post_element.find_element(By.XPATH,
                                                 ".//a[contains(@href, '/posts/') or contains(@href, '/pulse/')]")
        if article_link:
            return article_link.get_attribute('href')

        # Then look for general post links
        post_link = post_element.find_element(By.XPATH,
                                              ".//a[contains(@href, '/activity/') or contains(@href, '/feed/update/')]")
        if post_link:
            return post_link.get_attribute('href')

        # Look for any link with substantial href
        links = post_element.find_elements(By.XPATH, ".//a[contains(@href, 'linkedin.com/')]")
        for link in links:
            href = link.get_attribute('href')
            if href and len(href) > 30 and ('linkedin.com' in href):
                return href

    except Exception as e:
        print(f"Error extracting URL: {str(e)}")

    return None


def scrape_linkedin_posts_fn() -> str:
    """
    A tool that dynamically scrapes all featured posts from a LinkedIn profile
    """
    linkedin_username = os.environ.get("LINKEDIN_EMAIL")
    linkedin_password = os.environ.get("LINKEDIN_PASSWORD")
    profile_name = os.environ.get("LINKEDIN_PROFILE_NAME")

    print(f"Scraping all featured posts from profile: {profile_name}")

    if not (linkedin_username and linkedin_password):
        print("LinkedIn credentials not found in environment variables")
        return "[]"

    # Initialize posts list
    posts = []
    seen_content = set()  # Track unique content to avoid duplicates

    # Set up Chrome options with more human-like behavior
    chrome_options = uc.ChromeOptions()
    for option in BROWSER_OPTIONS:
        chrome_options.add_argument(option)

    # Create browser with undetected-chromedriver instead of regular selenium
    browser = uc.Chrome(options=chrome_options)

    try:
        # Login to LinkedIn
        print("Logging in to LinkedIn...")
        browser.get("https://www.linkedin.com/login")
        random_delay()

        # Check if security check is present
        if "security check" in browser.page_source.lower() or "security verification" in browser.page_source.lower():
            print("Security check detected during initial page load!")
            # browser.save_screenshot("security_check_initial.png")
            # print("Security check screenshot saved (security_check_initial.png)")
            # Give user a chance to solve manually
            print("Please check the browser window and solve the security check manually.")
            print(f"You have {SECURITY_CHECK_WAIT} seconds to solve it before the script continues...")
            time.sleep(SECURITY_CHECK_WAIT)  # Wait for user to potentially solve it

        # Enter username and password with human-like delays
        username_input = browser.find_element("id", "username")
        for char in linkedin_username:
            username_input.send_keys(char)
            time.sleep(random.uniform(KEYSTROKE_MIN_DELAY, KEYSTROKE_MAX_DELAY))  # Random delay between keystrokes

        random_delay(SCROLL_MIN_DELAY, SCROLL_MAX_DELAY)

        password_input = browser.find_element("id", "password")
        for char in linkedin_password:
            password_input.send_keys(char)
            time.sleep(random.uniform(KEYSTROKE_MIN_DELAY, KEYSTROKE_MAX_DELAY))

        random_delay()
        password_input.send_keys(Keys.RETURN)

        # Wait for login to complete with longer timeout
        print("Waiting for login to complete...")
        time.sleep(LONG_PAGE_LOAD_WAIT)  # Longer initial wait

        # Check for security verification after login
        if "security verification" in browser.page_source.lower() or "security check" in browser.page_source.lower():
            print("Security check detected after login!")
            # browser.save_screenshot("security_check_post_login.png")
            # print("Security check screenshot saved (security_check_post_login.png)")
            print("Please check the browser window and solve the security check manually.")
            print(f"You have {SECURITY_CHECK_WAIT} seconds to solve it before the script continues...")
            time.sleep(SECURITY_CHECK_WAIT)  # Wait for user to potentially solve it

        # Navigate to the profile with random delay
        print(f"Navigating to profile: {profile_name}")
        browser.get(f"https://www.linkedin.com/in/{profile_name}/")
        time.sleep(MEDIUM_PAGE_LOAD_WAIT)  # Longer wait for profile to load

        # Check for security verification again
        if "security verification" in browser.page_source.lower() or "security check" in browser.page_source.lower():
            print("Security check detected while accessing profile!")
            # browser.save_screenshot("security_check_profile.png")
            # print("Security check screenshot saved (security_check_profile.png)")
            print("Please check the browser window and solve the security check manually.")
            print(f"You have {SECURITY_CHECK_WAIT} seconds to solve it before the script continues...")
            time.sleep(SECURITY_CHECK_WAIT)

        # Scroll with human-like behavior to see more content
        print("Scrolling to see more content...")
        # Scroll down in smaller increments with random pauses to load more content
        for _ in range(5):
            browser.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            random_delay(SCROLL_MIN_DELAY, SCROLL_MAX_DELAY)

        # Try multiple approaches to find different types of content

        # 1. First check if profile has Articles
        print("Checking for Articles...")
        try:
            # Try to find the Articles section
            articles_tab = browser.find_element(By.XPATH, "//a[contains(@href, '/detail/recent-activity/posts/')]")
            if articles_tab:
                print("Found Articles tab, clicking to see articles...")
                articles_tab.click()
                time.sleep(SHORT_PAGE_LOAD_WAIT)  # Wait for articles to load

                article_items = browser.find_elements(By.XPATH, "//div[contains(@class, 'ember-view artdeco-card')]")
                # print(f"Found {len(article_items)} article items")

                for i, article in enumerate(article_items[:MAX_ARTICLES]):  # Limit to maximum articles
                    try:
                        article_text = article.text

                        # Skip if too short or seems like UI element
                        if len(article_text) < 50 or "Loading" in article_text:
                            continue

                        # Extract title and content
                        lines = article_text.split('\n')
                        title = lines[0] if lines else "LinkedIn Article"
                        content = '\n'.join(lines[1:]) if len(lines) > 1 else ""

                        # Use content fingerprint to avoid duplicates
                        content_fingerprint = title + content[:100]
                        if content_fingerprint in seen_content:
                            continue

                        seen_content.add(content_fingerprint)
                        posts.append({
                            "index": len(posts) + 1,
                            "title": title,
                            "content": content
                        })
                        print(f"Added article: {title[:30]}...")
                    except Exception as e:
                        print(f"Error processing article {i}: {str(e)}")

                # Go back to main profile
                browser.get(f"https://www.linkedin.com/in/{profile_name}/")
                time.sleep(SHORT_PAGE_LOAD_WAIT)
        except Exception as e:
            print(f"Error checking articles: {str(e)}")

        # 2. Look for Featured section
        print("Looking for Featured section...")
        featured_header = None
        try:
            featured_header = browser.find_element(By.XPATH, "//section[.//span[text()='Featured']]")
            print("Found Featured section")

            # Scroll to and screenshot the featured section
            browser.execute_script("arguments[0].scrollIntoView();", featured_header)
            random_delay()

            # Try to get all featured items using various selectors
            featured_items = featured_header.find_elements(By.XPATH, ".//li")
            if not featured_items:
                featured_items = featured_header.find_elements(By.XPATH, ".//div[contains(@class, 'artdeco-card')]")

            print(f"Found {len(featured_items)} featured items")

            for i, item in enumerate(featured_items[:MAX_FEATURED_ITEMS]):
                try:
                    # Get the raw text from the item
                    item_text = item.text.strip()

                    # Skip if too short or seems like UI element
                    if len(item_text) < 30:
                        continue

                    # Extract title and content from text
                    lines = item_text.split('\n')
                    title = lines[0] if lines else "Featured Item"
                    content = '\n'.join(lines[1:]) if len(lines) > 1 else ""

                    # Use content fingerprint to avoid duplicates
                    content_fingerprint = title + content[:100]
                    if content_fingerprint in seen_content:
                        continue

                    seen_content.add(content_fingerprint)
                    posts.append({
                        "index": len(posts) + 1,
                        "title": title,
                        "content": content
                    })
                    print(f"Added featured item: {title[:30]}...")
                except Exception as e:
                    print(f"Error processing featured item {i}: {str(e)}")
        except NoSuchElementException:
            print("Featured section not found")
        except Exception as e:
            print(f"Error processing featured section: {str(e)}")

        # 3. Look for Activity section and get posts from there
        print("Looking for posts in Activity section...")
        try:
            # First, try to click "see all activity" to get to the activity page
            try:
                activity_link = browser.find_element(By.XPATH, "//a[contains(@href, '/detail/recent-activity/')]")
                if activity_link:
                    print("Found Activity link, clicking to see more activity...")
                    activity_link.click()
                    time.sleep(SHORT_PAGE_LOAD_WAIT)  # Wait for activity to load
            except:
                print("No activity link found, continuing with current page")

            # Look for posts on the current page (either activity page or main profile)
            post_elements = browser.find_elements(By.XPATH, "//div[contains(@class, 'feed-shared-update-v2')]")
            if not post_elements:
                post_elements = browser.find_elements(By.XPATH, "//div[contains(@class, 'occludable-update')]")

            print(f"Found {len(post_elements)} post elements")

            for i, post_element in enumerate(post_elements[:MAX_POSTS]):  # Limit to maximum posts
                try:
                    # Get the whole post text
                    post_text = post_element.text.strip()

                    # Skip if too short or seems like UI element
                    if len(post_text) < 30:
                        continue

                    # Split into title and content
                    lines = post_text.split('\n')

                    # Find the actual post content by skipping header elements
                    content_start = 0
                    for j, line in enumerate(lines):
                        if "likes" in line.lower() or "comments" in line.lower() or "reactions" in line.lower():
                            content_start = j + 1
                            break

                    # Use the first substantive line as title
                    title_candidates = lines[content_start:content_start + 3]
                    title = next((line for line in title_candidates if len(line.strip()) > 5), "LinkedIn Post")

                    # Rest is content
                    content = '\n'.join(lines[content_start:]).replace(title, "", 1).strip()
                    if not content and content_start > 0:
                        # If no content after title, use everything
                        content = post_text

                    # Extract URL
                    post_url = extract_post_url(post_element)

                    # Use content fingerprint to avoid duplicates
                    content_fingerprint = title + content[:100]
                    if content_fingerprint in seen_content:
                        continue

                    seen_content.add(content_fingerprint)
                    posts.append({
                        "index": len(posts) + 1,
                        "title": title[:50] + ("..." if len(title) > 50 else ""),
                        "content": content,
                        "url": post_url
                    })
                    print(f"Added post: {title[:30]}... {' with URL' if post_url else ''}")
                except Exception as post_err:
                    print(f"Error extracting post {i + 1}: {str(post_err)}")
                    continue
        except Exception as e:
            print(f"Error processing activity posts: {str(e)}")

        # 4. Try to get information from About section if we have few posts
        if len(posts) < 2:
            print("Attempting to get content from About section...")
            try:
                about_section = browser.find_element(By.XPATH, "//section[.//span[text()='About']]")
                browser.execute_script("arguments[0].scrollIntoView();", about_section)
                random_delay()

                about_text = about_section.text.replace("About", "", 1).strip()
                if about_text and len(about_text) > 30:
                    # Use content fingerprint to avoid duplicates
                    content_fingerprint = "About" + about_text[:100]
                    if content_fingerprint not in seen_content:
                        seen_content.add(content_fingerprint)
                        posts.append({
                            "index": len(posts) + 1,
                            "title": "Profile Summary",
                            "content": about_text
                        })
                        print("Added profile summary as additional content")
            except Exception as about_err:
                print(f"Error getting About section: {str(about_err)}")

        # Take screenshot for debugging
        # browser.save_screenshot("linkedin_featured_posts.png")
        # print("Screenshot saved for debugging (linkedin_featured_posts.png)")

        browser.quit()

        # Format the output for the agent
        if posts:
            # Sort posts by index to maintain the order we found them
            posts.sort(key=lambda x: x.get('index', 999))

            # Format posts in a more readable way for agent consumption
            formatted_posts = []
            for i, post in enumerate(posts):
                formatted_posts.append(f"{i + 1}. {post.get('title', 'LinkedIn Post')}\n{post.get('content', '')}")

            return "\n\n".join(formatted_posts)
        else:
            print("No posts found using any approach")
            return "There are no LinkedIn posts available to display from the target profile."
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Full error traceback: {traceback_str}")

        if 'browser' in locals():
            # Take screenshot of the error state
            try:
                browser.save_screenshot("img/linkedin_error.png")
                # print("Error state screenshot saved (linkedin_error.png)")
            except:
                pass
            browser.quit()
        return "There was an error scraping the LinkedIn profile: " + str(e)


def extract_key_post_data(raw_posts):
    """
    Process raw scraped LinkedIn posts to extract only relevant featured posts
    and clean up the data format
    """
    # Initialize list for cleaned posts
    cleaned_posts = []

    for post in raw_posts:
        # Skip "Open to work" and "Share that you're hiring" items as they're not actual posts
        if post.get('title') in ["Open to work", "Share that you're hiring and attract qualified candidates"]:
            continue

        # Skip entries that are likely profile metadata or duplicates
        if 'Premium • You' in post.get('content', '') or 'Visible to anyone' in post.get('content', ''):
            continue

        # Check if this is an actual post (contains meaningful content)
        if 'Post' in post.get('title', '') or 'Post' in post.get('content', ''):
            # Clean up the data
            title = post.get('title', '').replace('Post', '').strip()
            content = post.get('content', '').replace('Post', '', 1).strip()

            # If title is empty or just "Post", extract a title from content
            if not title or title == "Post":
                # Split content by newlines and use first non-empty line as title
                content_lines = content.split('\n')
                for line in content_lines:
                    line = line.strip()
                    if line and len(line) > 5:  # Reasonable title length
                        title = line
                        # Remove the title from content to avoid duplication
                        content = content.replace(line, '', 1).strip()
                        break

            # Add to cleaned posts if we have meaningful content
            if title or content:
                cleaned_posts.append({
                    "title": title,
                    "content": content
                })

    return cleaned_posts


@tool("ScrapeLinkedinPosts")
def scrape_linkedin_posts_tool() -> str:
    """
    Scrape LinkedIn posts from a profile to understand writing style and content types.

    This tool navigates to a LinkedIn profile and extracts posts, articles, and featured content.
    The content is returned in a formatted way that can be used for analysis or mimicking the writing style.

    Returns:
        A formatted string containing LinkedIn posts with titles and content.
    """
    try:
        return scrape_linkedin_posts_fn()
    except Exception as e:
        print(f"Error in LinkedIn scraping tool: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Tool error traceback: {traceback_str}")
        return f"An error occurred while scraping LinkedIn: {str(e)}"
