# Scrapy settings for dumbcrawler project

BOT_NAME = "dumbcrawler"

SPIDER_MODULES = ["dumbcrawler.spiders"]
NEWSPIDER_MODULE = "dumbcrawler.spiders"

# Crawl responsibly by identifying yourself
USER_AGENT = "DumbCrawler/1.0"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# ==============================================================================
# CONCURRENCY SETTINGS
# ==============================================================================
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 0  # 0 means use CONCURRENT_REQUESTS_PER_DOMAIN

# ==============================================================================
# TIMEOUT SETTINGS
# ==============================================================================
DOWNLOAD_TIMEOUT = 30  # seconds
DOWNLOAD_DELAY = 0  # seconds between requests to same domain

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

# Browser launch options
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,  # 30 seconds to launch browser
}

# Default navigation timeout in milliseconds (None = use Playwright default 30s)
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds

# Maximum concurrent pages per browser context
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4

# Maximum concurrent browser contexts (None = no limit)
PLAYWRIGHT_MAX_CONTEXTS = None

# Restart browser if disconnected
PLAYWRIGHT_RESTART_DISCONNECTED_BROWSER = True

# Default browser context settings
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "ignore_https_errors": True,
        "java_script_enabled": True,
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

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Logging
LOG_LEVEL = "INFO"
