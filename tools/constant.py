# Timing constants for scraping
DEFAULT_MIN_DELAY = 1.0  # Default minimum delay between actions in seconds
DEFAULT_MAX_DELAY = 3.0  # Default maximum delay between actions in seconds

# Keystroke timing
KEYSTROKE_MIN_DELAY = 0.05  # Minimum delay between keystrokes
KEYSTROKE_MAX_DELAY = 0.15  # Maximum delay between keystrokes

# Scroll timing
SCROLL_MIN_DELAY = 0.8  # Minimum delay between scrolls
SCROLL_MAX_DELAY = 1.5  # Maximum delay between scrolls

# Page load timing
SHORT_PAGE_LOAD_WAIT = 5  # Short wait for page elements to load (seconds)
MEDIUM_PAGE_LOAD_WAIT = 7  # Medium wait for pages to load (seconds)
LONG_PAGE_LOAD_WAIT = 8    # Longer wait for login/complex pages (seconds)

# Security check timing
SECURITY_CHECK_WAIT = 5  # Time to wait for human to solve security check (seconds)

# Scraping limits
MAX_FEATURED_ITEMS = 10    # Maximum number of featured items to scrape
MAX_ARTICLES = 5           # Maximum number of articles to scrape
MAX_POSTS = 7              # Maximum number of posts to scrape from activity feed

# Browser options
BROWSER_OPTIONS = [
    "--disable-notifications",
    "--disable-popup-blocking"
]