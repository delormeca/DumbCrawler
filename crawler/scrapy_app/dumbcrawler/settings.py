# Scrapy settings for dumbcrawler project

BOT_NAME = "dumbcrawler"

SPIDER_MODULES = ["dumbcrawler.spiders"]
NEWSPIDER_MODULE = "dumbcrawler.spiders"

# Crawl responsibly by identifying yourself (realistic Chrome user agent for stealth)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# ==============================================================================
# CONCURRENCY SETTINGS (reduced for bot protection bypass)
# ==============================================================================
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 0  # 0 means use CONCURRENT_REQUESTS_PER_DOMAIN

# ==============================================================================
# TIMEOUT SETTINGS
# ==============================================================================
DOWNLOAD_TIMEOUT = 30  # seconds

# Download delay (seconds between requests to same domain)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Auto-throttle settings (adaptive delay based on server load)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# ==============================================================================
# PLAYWRIGHT DOWNLOAD HANDLER
# ==============================================================================
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# ==============================================================================
# PLAYWRIGHT SETTINGS
# ==============================================================================
# Browser type: chromium, firefox, or webkit
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# Browser launch options with stealth settings
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,  # 30 seconds to launch browser
    "args": [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--window-position=0,0',
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        '--disable-gpu',
    ],
}

# Default navigation timeout in milliseconds (None = use Playwright default 30s)
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds

# Maximum concurrent pages per browser context
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4

# Maximum concurrent browser contexts (None = no limit)
PLAYWRIGHT_MAX_CONTEXTS = None

# Restart browser if disconnected
PLAYWRIGHT_RESTART_DISCONNECTED_BROWSER = True

# Default browser context settings with stealth
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "java_script_enabled": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "permissions": ["geolocation"],
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
        "extra_http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        },
    }
}

# ==============================================================================
# TWISTED REACTOR (required for Playwright)
# ==============================================================================
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# ==============================================================================
# PIPELINES
# ==============================================================================
ITEM_PIPELINES = {
    "dumbcrawler.pipelines.DumbCrawlerPipeline": 300,
    "dumbcrawler.pipelines.JsonFilePipeline": 400,
}

# ==============================================================================
# OUTPUT SETTINGS
# ==============================================================================
# Directory for JSON output files
CRAWL_OUTPUT_DIR = "output"

# ==============================================================================
# OTHER SETTINGS
# ==============================================================================
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"

# ==============================================================================
# MIDDLEWARES
# ==============================================================================

# Enable stealth middleware for bot protection bypass
DOWNLOADER_MIDDLEWARES = {
    'dumbcrawler.middlewares.PlaywrightStealthMiddleware': 585,
}

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Enable cookies to appear more like a real browser
COOKIES_ENABLED = True

# Default request headers (mimic real browser)
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
}

# Logging
LOG_LEVEL = "INFO"
