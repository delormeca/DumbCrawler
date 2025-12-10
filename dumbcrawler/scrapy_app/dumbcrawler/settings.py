# Scrapy settings for dumbcrawler project

BOT_NAME = "dumbcrawler"

SPIDER_MODULES = ["dumbcrawler.spiders"]
NEWSPIDER_MODULE = "dumbcrawler.spiders"

# Crawl responsibly - disabled for dumb crawler
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Download timeout in seconds
DOWNLOAD_TIMEOUT = 30

# Retry configuration
RETRY_ENABLED = True
RETRY_TIMES = 2

# Disable cookies for simplicity
COOKIES_ENABLED = False

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# =============================================================================
# PLAYWRIGHT CONFIGURATION
# =============================================================================

# Download handlers for Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Browser configuration
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds

# Launch options
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}

# Default context configuration
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# Uncomment to log to file instead of stdout:
# LOG_FILE = "dumbcrawler.log"

# =============================================================================
# ITEM PIPELINES
# =============================================================================

ITEM_PIPELINES = {
    "dumbcrawler.pipelines.GEOAuditPipeline": 300,
    "dumbcrawler.pipelines.JsonOutputPipeline": 800,
}
