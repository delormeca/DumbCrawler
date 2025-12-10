# DumbCrawler Build Guide for Claude Code

> **Project**: `dumbcrawler` — A simple, API-first Scrapy + Playwright crawler  
> **Output**: JSON (stdout or file) — No database, no dashboard, no SaaS logic  
> **Execute each TASK sequentially. Do not skip ahead.**

---

## 🎯 Project Overview

### What We're Building

A stable, API-first crawler engine that:

- Uses **Scrapy + scrapy-playwright** (Chromium)
- Supports **3 crawl modes**: `single` | `list` | `crawl` (auto-discovery)
- Supports **scope restrictions**: subdomain-only, whole domain, subfolder-only, or combined
- Supports **JS rendering modes**: `off` | `auto` | `full`
- Outputs **clean JSON per URL** with: `url`, `status_code`, `depth`, `referrer_url`, `raw_html`, basic meta, headers

### Final Directory Structure

```
dumbcrawler/
├── README.md
├── requirements.txt
├── run_crawl.py                    # CLI entrypoint
└── scrapy_app/
    ├── scrapy.cfg
    └── dumbcrawler/
        ├── __init__.py
        ├── settings.py
        ├── pipelines.py
        ├── items.py
        └── spiders/
            ├── __init__.py
            └── dumb_spider.py
```

---

## 📋 Execution Order

| Phase | Tasks | Focus |
|-------|-------|-------|
| 0 | 0A | Environment & Dependencies |
| 1 | 1A, 1B | Project Skeleton |
| 2 | 2A, 2B, 2C | Scrapy + Playwright Settings |
| 3 | 3A, 3B, 3C, 3D, 3E, 3F | Core Spider Implementation |
| 4 | 4A, 4B, 4C | Extraction & JSON Output |
| 5 | 5A, 5B | Runner/CLI Interface |
| 6 | 6A, 6B | Manual Tests & QA |

---

# PHASE 0 — ENVIRONMENT & TOOLING

## TASK 0A: Set Up Python Environment and Install Dependencies

### OBJECTIVE
Create a clean Python environment with Scrapy, Playwright, and scrapy-playwright installed.

### CONTEXT
- No project code exists yet
- This establishes the foundation for dumbcrawler

### STEPS

**Step 1: Review**
```bash
# Check for existing virtual environment or dependency files
ls -la | grep -E "(venv|\.venv|requirements|pyproject)"
```

**Step 2: Create Virtual Environment**
```bash
python3 -m venv .venv
```

**Step 3: Activate Environment**
```bash
source .venv/bin/activate
```

**Step 4: Install Dependencies**
```bash
pip install scrapy scrapy-playwright playwright beautifulsoup4 lxml
```

**Step 5: Install Playwright Browser**
```bash
playwright install chromium
```

**Step 6: Create requirements.txt**
```txt
scrapy>=2.11.0
scrapy-playwright>=0.0.40
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
```

### DELIVERABLES
- [x] Working Python virtual environment (`.venv/`)
- [x] Installed packages: scrapy, scrapy-playwright, playwright, beautifulsoup4, lxml
- [x] `requirements.txt` file

### VERIFICATION
```bash
# All commands must succeed without error
python -c "import scrapy; print(f'Scrapy version: {scrapy.__version__}')"
python -c "import scrapy_playwright; print('scrapy-playwright OK')"
python -c "from bs4 import BeautifulSoup; print('BeautifulSoup OK')"
playwright --version
```

### ✅ STOP — Verify all checks pass before proceeding to TASK 1A

---

# PHASE 1 — PROJECT SKELETON

## TASK 1A: Create Base Folder Structure

### OBJECTIVE
Create the base directory layout for the dumbcrawler project.

### CONTEXT
- Environment is ready from TASK 0A
- No project structure exists yet

### STEPS

**Step 1: Review**
```bash
# Check current workspace to avoid conflicts
ls -la
```

**Step 2: Create Directory Structure**
```bash
mkdir -p dumbcrawler/scrapy_app
```

**Step 3: Create __init__.py**
```bash
touch dumbcrawler/scrapy_app/__init__.py
```

**Step 4: Create README.md**

Create file `dumbcrawler/README.md`:
```markdown
# dumbcrawler

API-first Scrapy + Playwright crawler engine.

## Features
- No database, no dashboard — pure JSON output
- Three crawl modes: single, list, crawl (auto-discovery)
- JS rendering: off, auto, full
- Scope control: subdomain, domain, subfolder

## Quick Start
```bash
python run_crawl.py --client-id 123 --mode single --start-urls https://example.com
```
```

### DELIVERABLES
```
dumbcrawler/
├── README.md
└── scrapy_app/
    └── __init__.py
```

### VERIFICATION
```bash
ls dumbcrawler/
# Expected output: README.md  scrapy_app

ls dumbcrawler/scrapy_app/
# Expected output: __init__.py
```

### ✅ STOP — Verify structure exists before proceeding to TASK 1B

---

## TASK 1B: Initialize Scrapy Project

### OBJECTIVE
Create a Scrapy project named `dumbcrawler` inside `scrapy_app/`.

### CONTEXT
- Folder structure exists from TASK 1A
- Scrapy is installed from TASK 0A

### STEPS

**Step 1: Review**
```bash
# Confirm no existing Scrapy project
ls dumbcrawler/scrapy_app/
```

**Step 2: Initialize Scrapy Project**
```bash
cd dumbcrawler/scrapy_app/
scrapy startproject dumbcrawler .
cd ../..
```

> **Note**: The `.` at the end creates the project in-place (current directory)

**Step 3: Verify Generated Files**
```bash
ls -la dumbcrawler/scrapy_app/
# Should show: scrapy.cfg, dumbcrawler/

ls -la dumbcrawler/scrapy_app/dumbcrawler/
# Should show: __init__.py, items.py, middlewares.py, pipelines.py, settings.py, spiders/
```

### DELIVERABLES
```
dumbcrawler/
├── README.md
└── scrapy_app/
    ├── scrapy.cfg
    └── dumbcrawler/
        ├── __init__.py
        ├── items.py
        ├── middlewares.py
        ├── pipelines.py
        ├── settings.py
        └── spiders/
            └── __init__.py
```

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/
scrapy list
# Should run without error (empty list is OK)
cd ../..
```

### ✅ STOP — `scrapy list` must succeed before proceeding to TASK 2A

---

# PHASE 2 — SCRAPY + PLAYWRIGHT SETTINGS

## TASK 2A: Configure Core Scrapy Settings

### OBJECTIVE
Configure basic Scrapy settings: bot name, concurrency, timeout, robots behavior.

### CONTEXT
- Scrapy project exists with default settings
- File: `dumbcrawler/scrapy_app/dumbcrawler/settings.py`

### STEPS

**Step 1: Review**
```bash
cat dumbcrawler/scrapy_app/dumbcrawler/settings.py
```

**Step 2: Update settings.py**

Replace/update `dumbcrawler/scrapy_app/dumbcrawler/settings.py` with these settings:

```python
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
```

### DELIVERABLES
- [x] Updated `settings.py` with core configuration

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/
scrapy settings --get BOT_NAME
# Expected: dumbcrawler

scrapy settings --get CONCURRENT_REQUESTS
# Expected: 16

scrapy list
# Should run without error
cd ../..
```

### ✅ STOP — All settings commands must return expected values before proceeding to TASK 2B

---

## TASK 2B: Integrate scrapy-playwright

### OBJECTIVE
Wire Playwright into Scrapy for JS page rendering.

### CONTEXT
- Basic Scrapy settings configured in TASK 2A
- scrapy-playwright installed in TASK 0A

### STEPS

**Step 1: Review Current Settings**
```bash
grep -E "(DOWNLOAD_HANDLERS|DOWNLOADER_MIDDLEWARES)" dumbcrawler/scrapy_app/dumbcrawler/settings.py
```

**Step 2: Add Playwright Configuration**

Append to `dumbcrawler/scrapy_app/dumbcrawler/settings.py`:

```python
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
```

### DELIVERABLES
- [x] Playwright download handlers configured
- [x] Playwright browser settings defined
- [x] Default context with viewport configured

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/
scrapy check
# Should complete without Playwright-related errors
cd ../..
```

### ✅ STOP — `scrapy check` must pass before proceeding to TASK 2C

---

## TASK 2C: Configure Logging Defaults

### OBJECTIVE
Set sensible logging format and level for debugging.

### CONTEXT
- Scrapy + Playwright integration complete

### STEPS

**Step 1: Review Existing Logging**
```bash
grep -i "log" dumbcrawler/scrapy_app/dumbcrawler/settings.py
```

**Step 2: Add Logging Configuration**

Append to `dumbcrawler/scrapy_app/dumbcrawler/settings.py`:

```python
# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# Uncomment to log to file instead of stdout:
# LOG_FILE = "dumbcrawler.log"
```

### DELIVERABLES
- [x] Logging level set to INFO
- [x] Custom log format with timestamps
- [x] Optional file logging commented out

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/
scrapy settings --get LOG_LEVEL
# Expected: INFO
cd ../..
```

### ✅ STOP — Logging configured, proceed to PHASE 3

---

# PHASE 3 — CORE SPIDER IMPLEMENTATION

## TASK 3A: Create Base Spider with Argument Parsing

### OBJECTIVE
Create `dumb_spider.py` that accepts runtime arguments but doesn't crawl yet.

### CONTEXT
- Scrapy project configured
- No spider exists yet

### STEPS

**Step 1: Review Spiders Directory**
```bash
ls dumbcrawler/scrapy_app/dumbcrawler/spiders/
```

**Step 2: Create dumb_spider.py**

Create file `dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py`:

```python
"""
DumbSpider - Core spider for dumbcrawler
Supports: single URL, list of URLs, and auto-discovery crawl modes
"""
import scrapy
from urllib.parse import urlparse


class DumbSpider(scrapy.Spider):
    name = "dumb_spider"
    
    def __init__(
        self,
        client_id: str = "default",
        crawl_job_id: str = "job_001",
        mode: str = "single",
        start_urls: str = "",
        max_depth: int = 0,
        js_mode: str = "auto",
        restrict_to_subdomain: str = "true",
        restrict_to_path: str = "false",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        
        # Store raw arguments
        self.client_id = client_id
        self.crawl_job_id = crawl_job_id
        self.mode = mode.lower()
        self.max_depth = int(max_depth)
        self.js_mode = js_mode.lower()
        
        # Parse boolean flags
        self.restrict_to_subdomain = restrict_to_subdomain.lower() == "true"
        self.restrict_to_path = restrict_to_path.lower() == "true"
        
        # Parse start URLs (comma-separated string to list)
        self.start_urls_list = [
            url.strip() 
            for url in start_urls.split(",") 
            if url.strip()
        ]
        
        # Log parsed configuration
        self.logger.info(f"=== DumbSpider Configuration ===")
        self.logger.info(f"  client_id: {self.client_id}")
        self.logger.info(f"  crawl_job_id: {self.crawl_job_id}")
        self.logger.info(f"  mode: {self.mode}")
        self.logger.info(f"  start_urls: {self.start_urls_list}")
        self.logger.info(f"  max_depth: {self.max_depth}")
        self.logger.info(f"  js_mode: {self.js_mode}")
        self.logger.info(f"  restrict_to_subdomain: {self.restrict_to_subdomain}")
        self.logger.info(f"  restrict_to_path: {self.restrict_to_path}")
    
    def start_requests(self):
        """Generate initial requests - placeholder for now."""
        self.logger.info(f"start_requests called with {len(self.start_urls_list)} URLs")
        # Will be implemented in TASK 3B
        return []
    
    def parse(self, response):
        """Parse response - placeholder for now."""
        self.logger.info(f"parse called for: {response.url}")
        # Will be implemented in TASK 3C
        pass
```

### DELIVERABLES
- [x] `dumb_spider.py` with argument parsing
- [x] Logging of all configuration parameters
- [x] Placeholder methods for `start_requests` and `parse`

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/
scrapy list
# Expected output: dumb_spider

scrapy crawl dumb_spider \
    -a client_id=123 \
    -a crawl_job_id=test \
    -a mode=single \
    -a start_urls=https://example.com

# Should run without error and log configuration
cd ../..
```

### ✅ STOP — Spider must appear in list and run without error before proceeding to TASK 3B

---

## TASK 3B: Implement Mode-Specific start_requests

### OBJECTIVE
Implement `start_requests` to generate requests for all start URLs.

### CONTEXT
- DumbSpider exists and parses arguments
- `start_requests` is placeholder

### STEPS

**Step 1: Review Current Implementation**
```bash
grep -A 10 "def start_requests" dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py
```

**Step 2: Update dumb_spider.py**

Replace the `start_requests` method and add `_make_request`:

```python
def start_requests(self):
    """Generate initial requests for all start URLs."""
    self.logger.info(f"Generating requests for {len(self.start_urls_list)} start URLs")
    
    for url in self.start_urls_list:
        yield self._make_request(url, depth=0, referrer=None)

def _make_request(self, url: str, depth: int, referrer: str = None):
    """
    Create a Scrapy Request with appropriate metadata.
    
    Args:
        url: Target URL to request
        depth: Current crawl depth
        referrer: URL that linked to this page
    
    Returns:
        scrapy.Request configured with metadata
    """
    meta = {
        "depth": depth,
        "client_id": self.client_id,
        "crawl_job_id": self.crawl_job_id,
        "referrer_url": referrer,
    }
    
    self.logger.debug(f"Creating request: {url} (depth={depth})")
    
    return scrapy.Request(
        url=url,
        callback=self.parse,
        meta=meta,
        errback=self.handle_error,
        dont_filter=False,
    )

def handle_error(self, failure):
    """Handle request errors."""
    self.logger.error(f"Request failed: {failure.request.url}")
    self.logger.error(f"Error: {failure.value}")
```

**Step 3: Update parse to log received response**

```python
def parse(self, response):
    """Parse response and extract data."""
    depth = response.meta.get("depth", 0)
    referrer = response.meta.get("referrer_url")
    
    self.logger.info(
        f"Received response: {response.url} "
        f"(status={response.status}, depth={depth})"
    )
    
    # Will yield items and follow links in TASK 3C
    pass
```

### DELIVERABLES
- [x] `start_requests` iterates over all start URLs
- [x] `_make_request` creates requests with proper metadata
- [x] `handle_error` logs failed requests
- [x] `parse` logs received responses

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a crawl_job_id=test \
    -a mode=single \
    -a start_urls=https://httpbin.org/html

# Should fetch the URL and log "Received response"
cd ../..
```

### ✅ STOP — Requests must be generated and responses logged before proceeding to TASK 3C

---

## TASK 3C: Implement Depth-Based Auto-Discovery for Crawl Mode

### OBJECTIVE
Add link-following logic for `mode=crawl` while respecting `max_depth`.

### CONTEXT
- Spider can make requests and receive responses
- Need to implement item yielding and link following

### STEPS

**Step 1: Review Current parse Method**
```bash
grep -A 20 "def parse" dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py
```

**Step 2: Replace parse Method**

Update the `parse` method in `dumb_spider.py`:

```python
def parse(self, response):
    """
    Parse response: extract data and optionally follow links.
    
    - Always yields an item with page data
    - In 'crawl' mode, follows internal links up to max_depth
    - In 'single' and 'list' modes, does not follow links
    """
    depth = response.meta.get("depth", 0)
    referrer = response.meta.get("referrer_url")
    
    self.logger.info(
        f"Parsing: {response.url} (status={response.status}, depth={depth})"
    )
    
    # Yield item for this page (structure defined in TASK 4A)
    item = {
        "client_id": self.client_id,
        "crawl_job_id": self.crawl_job_id,
        "url": response.url,
        "status_code": response.status,
        "depth": depth,
        "referrer_url": referrer,
        "raw_html": response.text if hasattr(response, 'text') else response.body.decode('utf-8', errors='replace'),
        "response_headers": self._headers_to_dict(response.headers),
    }
    yield item
    
    # Only follow links in 'crawl' mode
    if self.mode != "crawl":
        self.logger.debug(f"Mode is '{self.mode}', not following links")
        return
    
    # Check depth limit
    if depth >= self.max_depth:
        self.logger.debug(f"Max depth ({self.max_depth}) reached, not following links")
        return
    
    # Extract and follow links
    links = response.css("a::attr(href)").getall()
    self.logger.info(f"Found {len(links)} links on {response.url}")
    
    for href in links:
        # Resolve relative URLs
        next_url = response.urljoin(href)
        
        # Skip non-HTTP(S) URLs
        if not next_url.startswith(('http://', 'https://')):
            continue
        
        # Scoping checks will be added in TASK 3D and 3E
        # For now, follow all HTTP(S) links
        yield self._make_request(next_url, depth=depth + 1, referrer=response.url)

def _headers_to_dict(self, headers) -> dict:
    """Convert Scrapy Headers object to a plain dict."""
    result = {}
    for key, values in headers.items():
        # Decode bytes to string
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        # Headers can have multiple values
        decoded_values = [
            v.decode('utf-8') if isinstance(v, bytes) else v 
            for v in values
        ]
        result[key_str] = decoded_values[0] if len(decoded_values) == 1 else decoded_values
    return result
```

### DELIVERABLES
- [x] `parse` yields item dict for each page
- [x] `parse` follows links only in `crawl` mode
- [x] Depth limit enforced via `max_depth`
- [x] `_headers_to_dict` helper for response headers

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

# Test single mode (should NOT follow links)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=single \
    -a start_urls=https://httpbin.org/links/3/0

# Test crawl mode with depth=1 (should follow links)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=crawl \
    -a max_depth=1 \
    -a start_urls=https://httpbin.org/links/3/0

cd ../..
```

### ✅ STOP — Single mode must NOT follow links, crawl mode must follow links before proceeding to TASK 3D

---

## TASK 3D: Implement Domain/Subdomain Scoping

### OBJECTIVE
Restrict link following to same domain or same subdomain.

### CONTEXT
- Link following works but follows all domains
- Need to add domain/subdomain restrictions

### STEPS

**Step 1: Review __init__ Method**
```bash
grep -A 30 "def __init__" dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py
```

**Step 2: Add Scoping Logic to __init__**

Add after the `self.start_urls_list` assignment in `__init__`:

```python
# Initialize scoping variables from first start URL
if self.start_urls_list:
    first_url = self.start_urls_list[0]
    parsed = urlparse(first_url)
    
    # Full netloc (e.g., "blog.example.com")
    self.allowed_netloc = parsed.netloc
    
    # Base domain (e.g., "example.com" from "blog.example.com")
    # Handle cases like "example.com" (no subdomain)
    parts = parsed.netloc.split(".")
    if len(parts) >= 2:
        self.base_domain = ".".join(parts[-2:])
    else:
        self.base_domain = parsed.netloc
    
    # Path prefix for subfolder scoping (TASK 3E)
    self.restrict_path_prefix = parsed.path.rstrip("/") + "/" if parsed.path else "/"
    
    self.logger.info(f"  allowed_netloc: {self.allowed_netloc}")
    self.logger.info(f"  base_domain: {self.base_domain}")
    self.logger.info(f"  restrict_path_prefix: {self.restrict_path_prefix}")
else:
    self.allowed_netloc = ""
    self.base_domain = ""
    self.restrict_path_prefix = "/"
```

**Step 3: Add URL Filtering Method**

Add new method to the spider:

```python
def _is_url_allowed(self, url: str) -> bool:
    """
    Check if URL is within allowed scope.
    
    Args:
        url: URL to check
    
    Returns:
        True if URL is allowed, False otherwise
    """
    parsed = urlparse(url)
    target_netloc = parsed.netloc
    
    # Domain/subdomain check
    if self.restrict_to_subdomain:
        # Exact subdomain match required
        if target_netloc != self.allowed_netloc:
            self.logger.debug(f"Rejected (subdomain mismatch): {url}")
            return False
    else:
        # Same base domain required
        if not target_netloc.endswith(self.base_domain):
            self.logger.debug(f"Rejected (domain mismatch): {url}")
            return False
    
    # Path prefix check (TASK 3E) - placeholder
    # Will be implemented in next task
    
    return True
```

**Step 4: Update parse to Use Scoping**

In the `parse` method, update the link-following loop:

```python
for href in links:
    # Resolve relative URLs
    next_url = response.urljoin(href)
    
    # Skip non-HTTP(S) URLs
    if not next_url.startswith(('http://', 'https://')):
        continue
    
    # Apply scoping rules
    if not self._is_url_allowed(next_url):
        continue
    
    yield self._make_request(next_url, depth=depth + 1, referrer=response.url)
```

### DELIVERABLES
- [x] `allowed_netloc` and `base_domain` computed from first start URL
- [x] `_is_url_allowed` method for scoping checks
- [x] `restrict_to_subdomain` enforces exact subdomain match
- [x] Without `restrict_to_subdomain`, allows same base domain

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

# Test subdomain restriction (should only crawl same subdomain)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=crawl \
    -a max_depth=1 \
    -a restrict_to_subdomain=true \
    -a start_urls=https://docs.python.org/3/

# Should log "Rejected (subdomain mismatch)" for www.python.org links

cd ../..
```

### ✅ STOP — Subdomain filtering must work before proceeding to TASK 3E

---

## TASK 3E: Implement Subfolder (Path Prefix) Scoping

### OBJECTIVE
Restrict crawling to URLs whose path begins with the starting path.

### CONTEXT
- Domain/subdomain scoping works
- Need to add path prefix filtering

### STEPS

**Step 1: Review _is_url_allowed**
```bash
grep -A 30 "_is_url_allowed" dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py
```

**Step 2: Update _is_url_allowed for Path Scoping**

Add path prefix check to `_is_url_allowed` method:

```python
def _is_url_allowed(self, url: str) -> bool:
    """
    Check if URL is within allowed scope.
    
    Args:
        url: URL to check
    
    Returns:
        True if URL is allowed, False otherwise
    """
    parsed = urlparse(url)
    target_netloc = parsed.netloc
    target_path = parsed.path or "/"
    
    # Domain/subdomain check
    if self.restrict_to_subdomain:
        # Exact subdomain match required
        if target_netloc != self.allowed_netloc:
            self.logger.debug(f"Rejected (subdomain mismatch): {url}")
            return False
    else:
        # Same base domain required
        if not target_netloc.endswith(self.base_domain):
            self.logger.debug(f"Rejected (domain mismatch): {url}")
            return False
    
    # Path prefix check
    if self.restrict_to_path:
        if not target_path.startswith(self.restrict_path_prefix.rstrip("/")):
            self.logger.debug(f"Rejected (path mismatch): {url}")
            return False
    
    return True
```

### DELIVERABLES
- [x] Path prefix filtering in `_is_url_allowed`
- [x] `restrict_to_path` flag controls path filtering
- [x] Uses `restrict_path_prefix` from `__init__`

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

# Test path restriction (should only crawl /3/ paths)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=crawl \
    -a max_depth=1 \
    -a restrict_to_path=true \
    -a restrict_to_subdomain=true \
    -a start_urls=https://docs.python.org/3/library/

# Should log "Rejected (path mismatch)" for /3/tutorial/ etc.

cd ../..
```

### ✅ STOP — Path filtering must work before proceeding to TASK 3F

---

## TASK 3F: Implement js_mode Logic (off, auto, full)

### OBJECTIVE
Control when Playwright is used per request via `js_mode` argument.

### CONTEXT
- Playwright is integrated in settings
- Need to control per-request Playwright usage

### STEPS

**Step 1: Review _make_request**
```bash
grep -A 20 "_make_request" dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py
```

**Step 2: Add _should_use_playwright Method**

Add new method to the spider:

```python
def _should_use_playwright(self, url: str, depth: int) -> bool:
    """
    Determine if Playwright should be used for this request.
    
    Args:
        url: Target URL
        depth: Current crawl depth
    
    Returns:
        True if Playwright should be used, False otherwise
    """
    if self.js_mode == "off":
        return False
    
    if self.js_mode == "full":
        return True
    
    # 'auto' mode: use Playwright for depth 0 (start URLs), plain HTTP for deeper
    if self.js_mode == "auto":
        return depth == 0
    
    # Default to no Playwright for unknown modes
    self.logger.warning(f"Unknown js_mode '{self.js_mode}', defaulting to no Playwright")
    return False
```

**Step 3: Update _make_request to Use Playwright Decision**

Update `_make_request` method:

```python
def _make_request(self, url: str, depth: int, referrer: str = None):
    """
    Create a Scrapy Request with appropriate metadata.
    
    Args:
        url: Target URL to request
        depth: Current crawl depth
        referrer: URL that linked to this page
    
    Returns:
        scrapy.Request configured with metadata
    """
    meta = {
        "depth": depth,
        "client_id": self.client_id,
        "crawl_job_id": self.crawl_job_id,
        "referrer_url": referrer,
    }
    
    # Decide whether to use Playwright
    use_playwright = self._should_use_playwright(url, depth)
    
    if use_playwright:
        meta["playwright"] = True
        meta["playwright_context"] = "default"
        meta["playwright_include_page"] = False
        self.logger.debug(f"Request with Playwright: {url} (depth={depth})")
    else:
        self.logger.debug(f"Request without Playwright: {url} (depth={depth})")
    
    return scrapy.Request(
        url=url,
        callback=self.parse,
        meta=meta,
        errback=self.handle_error,
        dont_filter=False,
    )
```

### DELIVERABLES
- [x] `_should_use_playwright` method for JS mode decisions
- [x] `_make_request` conditionally adds Playwright metadata
- [x] `off` = never use Playwright
- [x] `full` = always use Playwright
- [x] `auto` = Playwright for depth 0 only

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

# Test js_mode=off (no Playwright logs)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=single \
    -a js_mode=off \
    -a start_urls=https://example.com

# Test js_mode=full (Playwright logs should appear)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=single \
    -a js_mode=full \
    -a start_urls=https://example.com

# Test js_mode=auto with crawl mode (only depth 0 uses Playwright)
scrapy crawl dumb_spider \
    -a client_id=123 \
    -a mode=crawl \
    -a max_depth=1 \
    -a js_mode=auto \
    -a start_urls=https://httpbin.org/links/2/0

cd ../..
```

### ✅ STOP — All js_mode options must work before proceeding to PHASE 4

---

# PHASE 4 — EXTRACTION & JSON OUTPUT

## TASK 4A: Define Raw Item Structure

### OBJECTIVE
Standardize the raw item dict yielded by DumbSpider.

### CONTEXT
- Spider yields items but structure may be inconsistent
- Need to ensure all fields are present and typed correctly

### STEPS

**Step 1: Review Current Item Structure**
```bash
grep -A 20 "yield item" dumbcrawler/scrapy_app/dumbcrawler/spiders/dumb_spider.py
```

**Step 2: Verify Item Structure in parse**

The item dict in `parse` should have this structure:

```python
item = {
    # Identifiers
    "client_id": self.client_id,          # str
    "crawl_job_id": self.crawl_job_id,    # str
    
    # Request/Response data
    "url": response.url,                   # str
    "status_code": response.status,        # int
    "depth": depth,                        # int
    "referrer_url": referrer,              # str or None
    
    # Content
    "raw_html": response.text if hasattr(response, 'text') else response.body.decode('utf-8', errors='replace'),  # str
    
    # Headers
    "response_headers": self._headers_to_dict(response.headers),  # dict
}
```

**Step 3: Optional - Create Scrapy Item Class**

Create/update `dumbcrawler/scrapy_app/dumbcrawler/items.py`:

```python
"""
Scrapy Items for dumbcrawler.
While we use dicts for flexibility, this documents the expected structure.
"""
import scrapy


class CrawledPageItem(scrapy.Item):
    """
    Item representing a crawled page.
    All fields are strings unless noted.
    """
    # Identifiers
    client_id = scrapy.Field()
    crawl_job_id = scrapy.Field()
    
    # Request/Response data
    url = scrapy.Field()
    status_code = scrapy.Field()  # int
    depth = scrapy.Field()  # int
    referrer_url = scrapy.Field()  # str or None
    
    # Content
    raw_html = scrapy.Field()
    
    # Headers
    response_headers = scrapy.Field()  # dict
    
    # Metadata (added by pipeline)
    meta_title = scrapy.Field()
    h1 = scrapy.Field()
    meta_description = scrapy.Field()
```

### DELIVERABLES
- [x] Item structure documented and consistent
- [x] All fields properly typed
- [x] Optional `items.py` for documentation

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

# Crawl and inspect logged items
scrapy crawl dumb_spider \
    -a client_id=test \
    -a mode=single \
    -a js_mode=off \
    -a start_urls=https://httpbin.org/html \
    -L DEBUG 2>&1 | grep -A 5 "Scraped from"

cd ../..
```

### ✅ STOP — Item structure must be consistent before proceeding to TASK 4B

---

## TASK 4B: Create Metadata Extraction Pipeline

### OBJECTIVE
Implement a pipeline that extracts `title`, `h1`, and `meta_description` from `raw_html`.

### CONTEXT
- Spider yields raw items
- BeautifulSoup installed in TASK 0A

### STEPS

**Step 1: Review Current Pipelines**
```bash
cat dumbcrawler/scrapy_app/dumbcrawler/pipelines.py
```

**Step 2: Update pipelines.py**

Replace content of `dumbcrawler/scrapy_app/dumbcrawler/pipelines.py`:

```python
"""
Pipelines for dumbcrawler.
"""
from bs4 import BeautifulSoup


class MetadataExtractionPipeline:
    """
    Extract basic metadata from raw_html:
    - meta_title: <title> content
    - h1: First <h1> content
    - meta_description: <meta name="description"> content
    """
    
    def process_item(self, item, spider):
        raw_html = item.get("raw_html", "")
        
        if not raw_html:
            item["meta_title"] = None
            item["h1"] = None
            item["meta_description"] = None
            return item
        
        try:
            soup = BeautifulSoup(raw_html, "lxml")
            
            # Extract <title>
            title_tag = soup.find("title")
            item["meta_title"] = title_tag.get_text(strip=True) if title_tag else None
            
            # Extract first <h1>
            h1_tag = soup.find("h1")
            item["h1"] = h1_tag.get_text(strip=True) if h1_tag else None
            
            # Extract <meta name="description">
            meta_desc = soup.find("meta", attrs={"name": "description"})
            item["meta_description"] = meta_desc.get("content", "").strip() if meta_desc else None
            
        except Exception as e:
            spider.logger.warning(f"Metadata extraction failed for {item.get('url')}: {e}")
            item["meta_title"] = None
            item["h1"] = None
            item["meta_description"] = None
        
        return item
```

**Step 3: Enable Pipeline in Settings**

Add to `dumbcrawler/scrapy_app/dumbcrawler/settings.py`:

```python
# =============================================================================
# ITEM PIPELINES
# =============================================================================

ITEM_PIPELINES = {
    "dumbcrawler.pipelines.MetadataExtractionPipeline": 300,
}
```

### DELIVERABLES
- [x] `MetadataExtractionPipeline` extracts title, h1, meta_description
- [x] Pipeline enabled in settings with priority 300
- [x] Error handling for malformed HTML

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

scrapy crawl dumb_spider \
    -a client_id=test \
    -a mode=single \
    -a js_mode=off \
    -a start_urls=https://httpbin.org/html \
    -L DEBUG 2>&1 | grep -E "(meta_title|h1|meta_description)"

# Should show extracted metadata fields

cd ../..
```

### ✅ STOP — Metadata extraction must work before proceeding to TASK 4C

---

## TASK 4C: Implement JSON Output Pipeline

### OBJECTIVE
Create a pipeline that outputs enriched items as JSONL (one JSON per line).

### CONTEXT
- Items have raw data and metadata
- Need to write to file in JSON Lines format

### STEPS

**Step 1: Review Current Pipelines**
```bash
grep -A 20 "class.*Pipeline" dumbcrawler/scrapy_app/dumbcrawler/pipelines.py
```

**Step 2: Add JsonOutputPipeline to pipelines.py**

Append to `dumbcrawler/scrapy_app/dumbcrawler/pipelines.py`:

```python
import json
from pathlib import Path


class JsonOutputPipeline:
    """
    Output items as JSON Lines (one JSON object per line).
    Output file: dumbcrawler_output.jsonl
    """
    
    def __init__(self):
        self.file = None
        self.output_path = None
    
    def open_spider(self, spider):
        """Open output file when spider starts."""
        # Get crawl_job_id for unique filename
        job_id = getattr(spider, "crawl_job_id", "default")
        self.output_path = Path(f"output_{job_id}.jsonl")
        
        spider.logger.info(f"Opening output file: {self.output_path}")
        self.file = open(self.output_path, "w", encoding="utf-8")
    
    def close_spider(self, spider):
        """Close output file when spider finishes."""
        if self.file:
            self.file.close()
            spider.logger.info(f"Closed output file: {self.output_path}")
    
    def process_item(self, item, spider):
        """Write item as JSON line."""
        # Convert item to dict if needed
        item_dict = dict(item) if hasattr(item, "items") else item
        
        # Write JSON line
        line = json.dumps(item_dict, ensure_ascii=False, default=str)
        self.file.write(line + "\n")
        self.file.flush()
        
        return item
```

**Step 3: Update Pipeline Settings**

Update `ITEM_PIPELINES` in settings.py:

```python
ITEM_PIPELINES = {
    "dumbcrawler.pipelines.MetadataExtractionPipeline": 300,
    "dumbcrawler.pipelines.JsonOutputPipeline": 800,
}
```

### DELIVERABLES
- [x] `JsonOutputPipeline` writes JSONL output
- [x] File named with `crawl_job_id`
- [x] Pipeline runs after metadata extraction (priority 800)

### VERIFICATION
```bash
cd dumbcrawler/scrapy_app/

scrapy crawl dumb_spider \
    -a client_id=test \
    -a crawl_job_id=test001 \
    -a mode=single \
    -a js_mode=off \
    -a start_urls=https://httpbin.org/html

# Check output file
cat output_test001.jsonl

# Validate JSON
python -c "import json; [json.loads(l) for l in open('output_test001.jsonl')]"

cd ../..
```

### ✅ STOP — JSONL output must be valid before proceeding to PHASE 5

---

# PHASE 5 — EXECUTION INTERFACE (RUNNER/CLI)

## TASK 5A: Create run_crawl.py Programmatic Runner

### OBJECTIVE
Provide a Python entrypoint for running DumbSpider without scrapy CLI.

### CONTEXT
- Crawler works via `scrapy crawl dumb_spider`
- Need API-like programmatic interface

### STEPS

**Step 1: Review Project Structure**
```bash
ls dumbcrawler/
```

**Step 2: Create run_crawl.py**

Create file `dumbcrawler/run_crawl.py`:

```python
#!/usr/bin/env python3
"""
Programmatic runner for dumbcrawler.
Usage: python run_crawl.py [arguments]
"""
import sys
import os

# Add scrapy_app to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapy_app"))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_dumb_crawl(
    client_id: str,
    crawl_job_id: str,
    mode: str = "single",
    start_urls: str = "",
    max_depth: int = 0,
    js_mode: str = "auto",
    restrict_to_subdomain: bool = True,
    restrict_to_path: bool = False,
) -> None:
    """
    Run DumbSpider with the specified configuration.
    
    Args:
        client_id: Client identifier
        crawl_job_id: Unique job identifier
        mode: Crawl mode - 'single', 'list', or 'crawl'
        start_urls: Comma-separated URLs to start from
        max_depth: Maximum crawl depth (for 'crawl' mode)
        js_mode: JavaScript mode - 'off', 'auto', or 'full'
        restrict_to_subdomain: Only crawl same subdomain
        restrict_to_path: Only crawl same path prefix
    """
    # Change to scrapy_app directory for settings
    os.chdir(os.path.join(os.path.dirname(__file__), "scrapy_app"))
    
    # Get Scrapy settings
    settings = get_project_settings()
    
    # Create and configure crawler process
    process = CrawlerProcess(settings)
    
    # Import spider (must be after settings are loaded)
    from dumbcrawler.spiders.dumb_spider import DumbSpider
    
    # Start the crawl
    process.crawl(
        DumbSpider,
        client_id=client_id,
        crawl_job_id=crawl_job_id,
        mode=mode,
        start_urls=start_urls,
        max_depth=max_depth,
        js_mode=js_mode,
        restrict_to_subdomain=str(restrict_to_subdomain).lower(),
        restrict_to_path=str(restrict_to_path).lower(),
    )
    
    # Block until crawl is complete
    process.start()


if __name__ == "__main__":
    # Quick test with hardcoded values
    run_dumb_crawl(
        client_id="test_client",
        crawl_job_id="test_job_001",
        mode="single",
        start_urls="https://httpbin.org/html",
        js_mode="off",
    )
```

### DELIVERABLES
- [x] `run_crawl.py` at `dumbcrawler/run_crawl.py`
- [x] `run_dumb_crawl` function with all parameters
- [x] Test mode in `__main__` block

### VERIFICATION
```bash
cd dumbcrawler/
python run_crawl.py

# Should crawl httpbin.org/html and create output file
ls scrapy_app/output_*.jsonl

cd ..
```

### ✅ STOP — Programmatic runner must work before proceeding to TASK 5B

---

## TASK 5B: Add CLI Argument Parsing

### OBJECTIVE
Allow running dumbcrawler via command-line arguments.

### CONTEXT
- `run_crawl.py` works with hardcoded values
- Need proper CLI interface

### STEPS

**Step 1: Review Current run_crawl.py**
```bash
cat dumbcrawler/run_crawl.py
```

**Step 2: Update run_crawl.py with argparse**

Replace the `if __name__ == "__main__":` block in `run_crawl.py`:

```python
import argparse
import uuid


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="dumbcrawler - API-first Scrapy+Playwright crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single URL, no JS
  python run_crawl.py --client-id 123 --mode single --start-urls https://example.com --js-mode off

  # Multiple URLs
  python run_crawl.py --client-id 123 --mode list --start-urls "https://a.com,https://b.com"

  # Auto-discovery crawl with depth 2
  python run_crawl.py --client-id 123 --mode crawl --max-depth 2 --start-urls https://example.com

  # Crawl with JS rendering
  python run_crawl.py --client-id 123 --mode crawl --js-mode full --start-urls https://spa-site.com
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--client-id",
        required=True,
        help="Client identifier"
    )
    
    parser.add_argument(
        "--start-urls",
        required=True,
        help="Comma-separated list of URLs to crawl"
    )
    
    # Optional arguments
    parser.add_argument(
        "--crawl-job-id",
        default=None,
        help="Unique job ID (default: auto-generated UUID)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["single", "list", "crawl"],
        default="single",
        help="Crawl mode (default: single)"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=0,
        help="Maximum crawl depth for 'crawl' mode (default: 0)"
    )
    
    parser.add_argument(
        "--js-mode",
        choices=["off", "auto", "full"],
        default="auto",
        help="JavaScript rendering mode (default: auto)"
    )
    
    parser.add_argument(
        "--restrict-to-subdomain",
        action="store_true",
        default=True,
        help="Only crawl same subdomain (default: True)"
    )
    
    parser.add_argument(
        "--no-restrict-to-subdomain",
        action="store_false",
        dest="restrict_to_subdomain",
        help="Allow crawling entire domain"
    )
    
    parser.add_argument(
        "--restrict-to-path",
        action="store_true",
        default=False,
        help="Only crawl same path prefix (default: False)"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Generate job ID if not provided
    crawl_job_id = args.crawl_job_id or f"job_{uuid.uuid4().hex[:8]}"
    
    # Log configuration
    print("=" * 60)
    print("dumbcrawler - Starting crawl")
    print("=" * 60)
    print(f"  client_id:             {args.client_id}")
    print(f"  crawl_job_id:          {crawl_job_id}")
    print(f"  mode:                  {args.mode}")
    print(f"  start_urls:            {args.start_urls}")
    print(f"  max_depth:             {args.max_depth}")
    print(f"  js_mode:               {args.js_mode}")
    print(f"  restrict_to_subdomain: {args.restrict_to_subdomain}")
    print(f"  restrict_to_path:      {args.restrict_to_path}")
    print("=" * 60)
    
    run_dumb_crawl(
        client_id=args.client_id,
        crawl_job_id=crawl_job_id,
        mode=args.mode,
        start_urls=args.start_urls,
        max_depth=args.max_depth,
        js_mode=args.js_mode,
        restrict_to_subdomain=args.restrict_to_subdomain,
        restrict_to_path=args.restrict_to_path,
    )
    
    print("=" * 60)
    print("dumbcrawler - Crawl complete")
    print("=" * 60)
```

### DELIVERABLES
- [x] Full argparse CLI with all options
- [x] Help text with examples
- [x] Auto-generated job ID if not provided
- [x] Configuration summary printed at start

### VERIFICATION
```bash
cd dumbcrawler/

# Show help
python run_crawl.py --help

# Test single mode
python run_crawl.py \
    --client-id test123 \
    --mode single \
    --start-urls https://httpbin.org/html \
    --js-mode off

# Test crawl mode with depth
python run_crawl.py \
    --client-id test456 \
    --mode crawl \
    --max-depth 1 \
    --start-urls https://httpbin.org/links/3/0 \
    --js-mode off

cd ..
```

### ✅ STOP — CLI must work with all options before proceeding to PHASE 6

---

# PHASE 6 — MANUAL TESTS & QA

## TASK 6A: Create Test Checklist and Sample Commands

### OBJECTIVE
Document manual test commands to verify dumbcrawler behavior.

### CONTEXT
- All features implemented
- Need systematic verification

### STEPS

**Step 1: Review Features**
```
- Three modes: single, list, crawl
- JS modes: off, auto, full
- Scoping: subdomain, path
- Depth control
```

**Step 2: Update README.md with Test Section**

Add to `dumbcrawler/README.md`:

```markdown
## Manual Test Commands

### Test 1: Single HTML-only URL (js_mode=off)
```bash
python run_crawl.py \
    --client-id test \
    --mode single \
    --start-urls https://httpbin.org/html \
    --js-mode off
```
**Expected**: Crawls exactly 1 URL, outputs 1 JSON line.

### Test 2: Single JS-heavy URL (js_mode=full)
```bash
python run_crawl.py \
    --client-id test \
    --mode single \
    --start-urls https://quotes.toscrape.com/js/ \
    --js-mode full
```
**Expected**: Crawls with Playwright, raw_html contains rendered content.

### Test 3: List Mode with Multiple URLs
```bash
python run_crawl.py \
    --client-id test \
    --mode list \
    --start-urls "https://httpbin.org/html,https://httpbin.org/robots.txt,https://httpbin.org/ip" \
    --js-mode off
```
**Expected**: Crawls exactly 3 URLs, outputs 3 JSON lines, no link following.

### Test 4: Crawl Mode with Depth (subdomain restricted)
```bash
python run_crawl.py \
    --client-id test \
    --mode crawl \
    --max-depth 1 \
    --start-urls https://httpbin.org/links/3/0 \
    --js-mode off \
    --restrict-to-subdomain
```
**Expected**: Crawls start URL + discovered links (depth 1), stays on same subdomain.

### Test 5: Crawl Mode with Path Restriction
```bash
python run_crawl.py \
    --client-id test \
    --mode crawl \
    --max-depth 2 \
    --start-urls https://docs.python.org/3/library/ \
    --js-mode off \
    --restrict-to-path
```
**Expected**: Only crawls URLs starting with `/3/library/`.

### Test 6: Verify Output JSON Structure
```bash
# After any crawl:
cat scrapy_app/output_*.jsonl | python -m json.tool | head -50

# Check required fields exist:
cat scrapy_app/output_*.jsonl | python -c "
import json, sys
for line in sys.stdin:
    item = json.loads(line)
    required = ['client_id', 'crawl_job_id', 'url', 'status_code', 'depth', 
                'referrer_url', 'raw_html', 'response_headers', 
                'meta_title', 'h1', 'meta_description']
    missing = [f for f in required if f not in item]
    if missing:
        print(f'MISSING: {missing}')
    else:
        print(f'OK: {item[\"url\"][:60]}...')
"
```

### Cleanup Test Files
```bash
rm -f scrapy_app/output_*.jsonl
```
```

### DELIVERABLES
- [x] Test commands in README.md
- [x] Expected outcomes documented
- [x] Output validation commands

### VERIFICATION
- Manually run each test command
- Verify expected outcomes match actual results

### ✅ STOP — Document test results before proceeding to TASK 6B

---

## TASK 6B: Smoke Test JS Rendering

### OBJECTIVE
Verify that Playwright properly renders JavaScript-heavy pages.

### CONTEXT
- All tests passing for static pages
- Need to verify JS rendering works

### STEPS

**Step 1: Identify JS-Heavy Test Page**

Use: `https://quotes.toscrape.com/js/` (a known JS-rendered page)

**Step 2: Run JS Crawl**
```bash
cd dumbcrawler/

python run_crawl.py \
    --client-id js_test \
    --crawl-job-id js_smoke_test \
    --mode single \
    --start-urls https://quotes.toscrape.com/js/ \
    --js-mode full
```

**Step 3: Verify Rendered Content**
```bash
# Check that raw_html contains actual quote content (not just skeleton)
cat scrapy_app/output_js_smoke_test.jsonl | python -c "
import json, sys
for line in sys.stdin:
    item = json.loads(line)
    html = item.get('raw_html', '')
    
    # Look for content that only appears after JS renders
    if 'Albert Einstein' in html or 'class=\"quote\"' in html:
        print('✅ SUCCESS: JS content rendered correctly')
        print(f'   Found quote content in {len(html)} chars of HTML')
    else:
        print('❌ FAILURE: JS content not rendered')
        print(f'   HTML preview: {html[:500]}...')
"
```

**Step 4: Compare with js_mode=off**
```bash
python run_crawl.py \
    --client-id js_test_off \
    --crawl-job-id js_off_test \
    --mode single \
    --start-urls https://quotes.toscrape.com/js/ \
    --js-mode off

cat scrapy_app/output_js_off_test.jsonl | python -c "
import json, sys
for line in sys.stdin:
    item = json.loads(line)
    html = item.get('raw_html', '')
    
    if 'Albert Einstein' not in html:
        print('✅ EXPECTED: js_mode=off does NOT render JS content')
    else:
        print('⚠️  UNEXPECTED: Content found even with js_mode=off')
"
```

### DELIVERABLES
- [x] Verified JS rendering works with Playwright
- [x] Documented proof in logs/output
- [x] Comparison showing difference between js_mode on/off

### VERIFICATION
- `js_mode=full` output contains JavaScript-rendered content
- `js_mode=off` output does NOT contain JavaScript-rendered content
- No Playwright errors in logs

### ✅ COMPLETE — dumbcrawler is ready for use!

---

# 📊 Summary Checklist

| Task | Description | Status |
|------|-------------|--------|
| 0A | Python environment setup | ⬜ |
| 1A | Base folder structure | ⬜ |
| 1B | Scrapy project initialization | ⬜ |
| 2A | Core Scrapy settings | ⬜ |
| 2B | Playwright integration | ⬜ |
| 2C | Logging configuration | ⬜ |
| 3A | Spider argument parsing | ⬜ |
| 3B | start_requests implementation | ⬜ |
| 3C | Depth-based crawling | ⬜ |
| 3D | Domain/subdomain scoping | ⬜ |
| 3E | Path prefix scoping | ⬜ |
| 3F | js_mode logic | ⬜ |
| 4A | Item structure | ⬜ |
| 4B | Metadata extraction pipeline | ⬜ |
| 4C | JSON output pipeline | ⬜ |
| 5A | Programmatic runner | ⬜ |
| 5B | CLI argument parsing | ⬜ |
| 6A | Test documentation | ⬜ |
| 6B | JS rendering smoke test | ⬜ |

---

# 🚨 Troubleshooting

## Common Issues

### Playwright Browser Not Found
```bash
playwright install chromium
```

### Import Errors
```bash
# Ensure you're in the right directory
cd dumbcrawler/scrapy_app/
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Twisted Reactor Error
Ensure `TWISTED_REACTOR` is set in settings.py BEFORE any Scrapy imports:
```python
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
```

### Invalid JSON Output
- Check `_headers_to_dict` properly converts bytes to strings
- Ensure `default=str` in `json.dumps()` call

---

# 🔄 Retry Instructions

If any task fails, use this prompt:
```
Retry TASK [X]. Fix errors from the previous attempt. Follow the steps exactly as documented.
```

Do NOT proceed to the next task until all verification steps pass.
