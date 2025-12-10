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
        else:
            self.allowed_netloc = ""
            self.base_domain = ""
            self.restrict_path_prefix = "/"

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
        self.logger.info(f"  allowed_netloc: {self.allowed_netloc}")
        self.logger.info(f"  base_domain: {self.base_domain}")
        self.logger.info(f"  restrict_path_prefix: {self.restrict_path_prefix}")

    def start_requests(self):
        """Generate initial requests for all start URLs."""
        self.logger.info(f"Generating requests for {len(self.start_urls_list)} start URLs")

        for url in self.start_urls_list:
            yield self._make_request(url, depth=0, referrer=None)

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

    def handle_error(self, failure):
        """Handle request errors."""
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")

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

            # Apply scoping rules
            if not self._is_url_allowed(next_url):
                continue

            yield self._make_request(next_url, depth=depth + 1, referrer=response.url)

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
