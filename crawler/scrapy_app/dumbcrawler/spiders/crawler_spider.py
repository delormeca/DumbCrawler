import re
import os
import hashlib
import scrapy
from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod
from urllib.parse import urlparse, urljoin
from typing import List, Optional, Generator, Set, Dict, Any


class DumbCrawlerSpider(scrapy.Spider):
    """
    DumbCrawler Spider - API-first crawler with four modes:
    - single: crawl a single URL
    - list: crawl a list of URLs
    - crawl: auto-discovery crawl with depth control
    - sitemap: crawl URLs from XML sitemaps (supports sitemap index, gzip, robots.txt)
    """

    name = "dumbcrawler"

    # Handle ALL HTTP status codes (not just 2xx)
    # This ensures we capture 404, 500, etc. pages
    handle_httpstatus_all = True

    # Security: Sitemap DoS protection limits
    SITEMAP_REQUEST_TIMEOUT = 30  # seconds - prevent slowloris attacks
    SITEMAP_MAX_RECURSION_DEPTH = 5  # levels - prevent infinite recursion
    SITEMAP_MAX_URLS = 100000  # maximum URLs to extract from sitemaps

    # Spider arguments with defaults
    # --mode: single | list | crawl | sitemap
    # --start-urls: comma-separated URLs (for single/list/crawl modes, OR sitemap URLs for sitemap mode)
    # --max-depth: maximum crawl depth (for crawl mode)
    # --scope: subdomain | domain | subfolder | subdomain+subfolder
    # --js-mode: off | auto | full
    # --sitemap-alternate-links: include alternate language links from sitemaps (true/false)

    def __init__(
        self,
        mode: str = "single",
        start_urls: str = "",
        max_depth: int = 2,
        scope: str = "domain",
        js_mode: str = "off",
        sitemap_alternate_links: str = "false",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        # Parse and validate mode
        self.crawl_mode = mode.lower()
        if self.crawl_mode not in ("single", "list", "crawl", "sitemap"):
            raise ValueError(f"Invalid mode: {mode}. Must be: single, list, crawl, or sitemap")

        # Parse start URLs (for sitemap mode, these are sitemap URLs)
        self.start_urls = self._parse_urls(start_urls)
        if not self.start_urls:
            raise ValueError("No start URLs provided. Use --start-urls argument.")

        # Parse max depth
        self.max_depth = int(max_depth)

        # Parse and validate scope
        self.scope = scope.lower()
        if self.scope not in ("subdomain", "domain", "subfolder", "subdomain+subfolder"):
            raise ValueError(
                f"Invalid scope: {scope}. Must be: subdomain, domain, subfolder, or subdomain+subfolder"
            )

        # Parse and validate JS mode
        self.js_mode = js_mode.lower()
        if self.js_mode not in ("off", "auto", "full"):
            raise ValueError(f"Invalid js_mode: {js_mode}. Must be: off, auto, or full")

        # Parse sitemap alternate links setting
        self.sitemap_alternate_links = sitemap_alternate_links.lower() in ("true", "1", "yes")

        # Store parsed base URL info for scope checking
        self._base_urls_info = [self._parse_url_info(url) for url in self.start_urls]

        # Link extractor for crawl mode - deny non-HTML file extensions
        self.link_extractor = LinkExtractor(
            deny_extensions=[
                # Images
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'tiff', 'tif',
                # Documents
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp',
                # Archives
                'zip', 'rar', 'tar', 'gz', '7z', 'bz2',
                # Media
                'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'wav', 'ogg', 'webm',
                # Other binary
                'exe', 'dmg', 'iso', 'bin', 'dll', 'so',
                # Data files
                'json', 'xml', 'csv', 'txt',
            ],
            unique=True,
        )

        # Track visited URLs to avoid duplicates
        self._visited_urls: Set[str] = set()

        # Security: Track sitemap URL extraction count
        self._sitemap_url_count = 0  # Track total URLs extracted from sitemaps

        # Screenshot settings - get output dir from settings
        self._screenshot_enabled = self.js_mode != "off"
        self._screenshot_dir: Optional[str] = None  # Set from settings in start_requests

        self.logger.info(f"DumbCrawler initialized:")
        self.logger.info(f"  Mode: {self.crawl_mode}")
        if self.crawl_mode == "sitemap":
            self.logger.info(f"  Sitemap URLs: {self.start_urls}")
            self.logger.info(f"  Include Alternate Links: {self.sitemap_alternate_links}")
        else:
            self.logger.info(f"  Start URLs: {self.start_urls}")
        self.logger.info(f"  Max Depth: {self.max_depth}")
        self.logger.info(f"  Scope: {self.scope}")
        self.logger.info(f"  JS Mode: {self.js_mode}")

    def _parse_urls(self, urls_str: str) -> List[str]:
        """Parse comma-separated URL string into list."""
        if not urls_str:
            return []
        urls = [url.strip() for url in urls_str.split(",")]
        return [url for url in urls if url]

    def _is_private_ip(self, hostname: str) -> bool:
        """
        Check if hostname resolves to a private IP address.
        Returns True if the hostname resolves to a private/internal IP.
        Used for SSRF protection (prevents DNS rebinding attacks).
        """
        import socket
        import ipaddress

        try:
            # Resolve hostname to IP address
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)

            # Check if IP is private, loopback, or link-local
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except Exception as e:
            self.logger.error(f"Failed to resolve hostname {hostname}: {e}")
            # Fail closed - treat as private if we can't resolve
            return True

    def _validate_sitemap_url_security(self, url_string: str) -> tuple:
        """
        Validate sitemap URL for security (SSRF protection).
        Checks both URL format and DNS resolution.
        Returns (is_valid, error_message)
        """
        try:
            parsed = urlparse(url_string)

            # Must be HTTPS for security
            if parsed.scheme != 'https':
                return (False, f"Sitemap URL must use HTTPS: {url_string}")

            # Check if hostname resolves to private IP (DNS rebinding protection)
            if self._is_private_ip(parsed.hostname):
                return (False, f"Sitemap URL resolves to private/internal IP address: {url_string}")

            return (True, "")
        except Exception as e:
            return (False, f"Invalid sitemap URL: {str(e)}")

    def _parse_url_info(self, url: str) -> dict:
        """Extract URL components for scope checking."""
        parsed = urlparse(url)
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "domain": self._get_domain(parsed.netloc),
            "subdomain": self._get_subdomain(parsed.netloc),
            "path": parsed.path.rstrip("/"),
        }

    def _get_domain(self, netloc: str) -> str:
        """Extract root domain from netloc (e.g., 'www.example.com' -> 'example.com')."""
        parts = netloc.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return netloc

    def _get_subdomain(self, netloc: str) -> str:
        """Extract subdomain from netloc (e.g., 'www.example.com' -> 'www')."""
        parts = netloc.split(".")
        if len(parts) > 2:
            return ".".join(parts[:-2])
        return ""

    def _get_sitemap_body(self, response: Response) -> Optional[bytes]:
        """
        Extract sitemap body from response, handling gzip compression.

        Supports:
        - Regular XML responses
        - Gzipped sitemaps (.xml.gz)
        - Auto-decompressed responses (Content-Encoding: gzip)

        Returns None if response is not a valid sitemap.
        """
        from scrapy.http import XmlResponse
        from scrapy.utils.gz import gunzip, gzip_magic_number
        from scrapy.utils._compression import _DecompressionMaxSizeExceeded

        try:
            # If it's already an XML response, use it directly
            if isinstance(response, XmlResponse):
                return response.body

            # Check if body is gzipped
            if gzip_magic_number(response):
                try:
                    # Decompress with size limits from settings
                    max_size = getattr(self, '_max_sitemap_size', 10 * 1024 * 1024)  # 10MB default
                    return gunzip(response.body, max_size=max_size)
                except _DecompressionMaxSizeExceeded:
                    self.logger.error(f"Sitemap {response.url} exceeds maximum decompressed size")
                    return None
                except Exception as e:
                    self.logger.error(f"Failed to decompress sitemap {response.url}: {e}")
                    return None

            # Handle .xml or .xml.gz URLs (might be already decompressed by middleware)
            if response.url.endswith('.xml') or response.url.endswith('.xml.gz'):
                return response.body

            # Try to detect if it's XML content even without proper extension
            if response.body.strip().startswith(b'<?xml') or b'<urlset' in response.body[:500] or b'<sitemapindex' in response.body[:500]:
                return response.body

        except Exception as e:
            self.logger.error(f"Error getting sitemap body from {response.url}: {e}")

        return None

    def _parse_sitemap(self, response: Response) -> Generator[Request, None, None]:
        """
        Parse sitemap XML and yield requests for discovered URLs.

        Handles:
        - Regular sitemaps (urlset)
        - Sitemap index files (sitemapindex) - recursively fetches nested sitemaps
        - Gzipped sitemaps
        - Robots.txt sitemap discovery
        - Alternate language links (if enabled)
        - Malformed XML (with recovery)

        Applies scope filtering and deduplication.
        """
        from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

        # Special handling for robots.txt
        if response.url.endswith('/robots.txt'):
            self.logger.info(f"Extracting sitemaps from robots.txt: {response.url}")
            try:
                for sitemap_url in sitemap_urls_from_robots(response.text, base_url=response.url):
                    self.logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
                    yield Request(sitemap_url, callback=self._parse_sitemap)
            except Exception as e:
                self.logger.error(f"Failed to parse robots.txt {response.url}: {e}")
            return

        # Get sitemap body (handles gzip, XML detection, etc.)
        body = self._get_sitemap_body(response)
        if body is None:
            self.logger.warning(f"Ignoring invalid sitemap: {response.url}")
            return

        # Parse sitemap XML
        try:
            sitemap = Sitemap(body)
        except Exception as e:
            self.logger.error(f"Failed to parse sitemap XML {response.url}: {e}")
            return

        # Filter sitemap entries (can be overridden for custom filtering)
        sitemap_entries = self._filter_sitemap_entries(sitemap)

        # Handle sitemap index (contains links to other sitemaps)
        if sitemap.type == "sitemapindex":
            # Security: Check recursion depth to prevent infinite loops
            current_depth = response.meta.get('sitemap_depth', 0)

            if current_depth >= self.SITEMAP_MAX_RECURSION_DEPTH:
                self.logger.error(
                    f"Sitemap recursion depth limit ({self.SITEMAP_MAX_RECURSION_DEPTH}) "
                    f"reached at {response.url}. Stopping recursion."
                )
                return

            self.logger.info(f"Processing sitemap index: {response.url} (depth: {current_depth})")
            sitemap_count = 0

            for entry in sitemap_entries:
                loc = entry.get('loc')
                if not loc:
                    continue

                sitemap_count += 1
                self.logger.info(f"Following nested sitemap [{sitemap_count}]: {loc}")

                # Recursively parse nested sitemaps with incremented depth
                yield Request(
                    loc,
                    callback=self._parse_sitemap,
                    priority=10,
                    meta={'sitemap_depth': current_depth + 1}  # Security: Increment depth
                )

            self.logger.info(f"Sitemap index contains {sitemap_count} sitemaps")

        # Handle URL set (contains actual page URLs to crawl)
        elif sitemap.type == "urlset":
            self.logger.info(f"Processing sitemap urlset: {response.url}")
            url_count = 0
            skipped_scope = 0
            skipped_duplicate = 0

            for entry in sitemap_entries:
                # Extract URLs to crawl
                urls_to_crawl = [entry.get('loc')]

                # Include alternate language links if enabled
                if self.sitemap_alternate_links and 'alternate' in entry:
                    urls_to_crawl.extend(entry['alternate'])

                for url in urls_to_crawl:
                    if not url:
                        continue

                    url = url.strip()

                    # Apply scope filtering
                    if not self._is_url_in_scope(url):
                        skipped_scope += 1
                        continue

                    # Check for duplicates
                    normalized_url = self._normalize_url(url)
                    if normalized_url in self._visited_urls:
                        skipped_duplicate += 1
                        continue

                    # Security: Check if we've hit the URL limit before yielding
                    if self._sitemap_url_count >= self.SITEMAP_MAX_URLS:
                        self.logger.error(
                            f"Sitemap URL limit reached ({self.SITEMAP_MAX_URLS}). "
                            f"Stopping extraction to prevent resource exhaustion."
                        )
                        return

                    # Mark as visited
                    self._visited_urls.add(normalized_url)
                    url_count += 1
                    self._sitemap_url_count += 1

                    # Security: Progress logging every 1000 URLs
                    if self._sitemap_url_count % 1000 == 0:
                        self.logger.info(
                            f"Sitemap progress: {self._sitemap_url_count}/{self.SITEMAP_MAX_URLS} URLs extracted"
                        )

                    # Extract sitemap metadata for logging
                    lastmod = entry.get('lastmod', 'N/A')
                    priority = entry.get('priority', 'N/A')

                    # Yield request to crawl this URL
                    yield self._make_request(
                        url=url,
                        depth=0,
                        referrer=response.url,
                        dont_filter=True
                    )

            self.logger.info(
                f"Sitemap yielded {url_count} URLs "
                f"(skipped: {skipped_scope} out-of-scope, {skipped_duplicate} duplicates)"
            )

        else:
            self.logger.warning(f"Unknown sitemap type '{sitemap.type}' for {response.url}")

    def _filter_sitemap_entries(self, sitemap: Any) -> Generator[Dict[str, Any], None, None]:
        """
        Filter sitemap entries based on custom criteria.

        Override this method to implement custom filtering logic:
        - Filter by lastmod date
        - Filter by priority
        - Filter by changefreq
        - etc.

        Default implementation: yield all entries unchanged.
        """
        for entry in sitemap:
            yield entry

    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests based on mode."""
        # Set up screenshot directory from crawler settings
        if self._screenshot_enabled:
            output_dir = self.crawler.settings.get('CRAWL_OUTPUT_DIR', 'output')
            self._screenshot_dir = os.path.join(output_dir, 'screenshots')
            os.makedirs(self._screenshot_dir, exist_ok=True)
            self.logger.info(f"Screenshots enabled, saving to: {self._screenshot_dir}")

        # Handle sitemap mode: parse sitemaps to extract URLs
        if self.crawl_mode == "sitemap":
            self.logger.info(f"Starting sitemap mode with {len(self.start_urls)} sitemap URL(s)")
            self.logger.info(f"Security limits: timeout={self.SITEMAP_REQUEST_TIMEOUT}s, max_depth={self.SITEMAP_MAX_RECURSION_DEPTH}, max_urls={self.SITEMAP_MAX_URLS}")

            # Security: Configure download timeout for sitemap requests
            self.custom_settings = {
                'DOWNLOAD_TIMEOUT': self.SITEMAP_REQUEST_TIMEOUT,
            }

            for sitemap_url in self.start_urls:
                # Security: Validate sitemap URL before fetching (SSRF + DNS rebinding protection)
                is_valid, error_msg = self._validate_sitemap_url_security(sitemap_url)
                if not is_valid:
                    self.logger.error(f"Sitemap URL failed security validation: {error_msg}")
                    continue

                self.logger.info(f"Fetching sitemap: {sitemap_url}")
                # Yield request to parse the sitemap
                # The _parse_sitemap callback will handle extraction and crawling
                yield Request(
                    sitemap_url,
                    callback=self._parse_sitemap,
                    errback=self.handle_error,
                    priority=100,  # High priority for sitemap fetching
                    dont_filter=True,
                    meta={'sitemap_depth': 0}  # Security: Track recursion depth
                )

        # Handle other modes: single, list, crawl
        else:
            for url in self.start_urls:
                # Mark start URLs as visited
                normalized_url = self._normalize_url(url)
                self._visited_urls.add(normalized_url)
                yield self._make_request(url, depth=0, referrer=None, dont_filter=True)

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent duplicate detection."""
        parsed = urlparse(url)
        # Normalize: lowercase scheme and netloc, remove trailing slash from path
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    def _make_request(
        self,
        url: str,
        depth: int,
        referrer: Optional[str],
        **kwargs
    ) -> Request:
        """Create a request with appropriate meta data."""
        use_playwright = self._should_use_playwright(url)
        meta = {
            "depth": depth,
            "referrer": referrer,
            "playwright": use_playwright,
        }

        # Add Playwright page methods for screenshot and performance timing
        if use_playwright and self._screenshot_enabled and self._screenshot_dir:
            # Generate screenshot filename from URL hash
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
            screenshot_path = os.path.join(self._screenshot_dir, f"{url_hash}.png")

            meta["playwright_page_methods"] = [
                # Capture screenshot (full page)
                PageMethod("screenshot", path=screenshot_path, full_page=True),
                # Capture performance timing via JavaScript
                PageMethod(
                    "evaluate",
                    """() => {
                        const timing = performance.timing;
                        const navigation = performance.getEntriesByType('navigation')[0] || {};
                        return {
                            dns_lookup_ms: timing.domainLookupEnd - timing.domainLookupStart,
                            tcp_connect_ms: timing.connectEnd - timing.connectStart,
                            ttfb_ms: timing.responseStart - timing.requestStart,
                            dom_load_ms: timing.domContentLoadedEventEnd - timing.navigationStart,
                            full_load_ms: timing.loadEventEnd - timing.navigationStart,
                            dom_interactive_ms: timing.domInteractive - timing.navigationStart,
                            transfer_size: navigation.transferSize || 0,
                            encoded_body_size: navigation.encodedBodySize || 0,
                            decoded_body_size: navigation.decodedBodySize || 0,
                        };
                    }"""
                ),
            ]
            meta["_screenshot_path"] = screenshot_path

        return Request(
            url=url,
            callback=self.parse,
            meta=meta,
            errback=self.handle_error,
            **kwargs
        )

    def _should_use_playwright(self, url: str) -> bool:
        """
        Determine if Playwright should be used for this request.

        JS Modes:
        - off: Never use Playwright (fastest, for static HTML sites)
        - full: Always use Playwright (slowest, for JS-heavy sites)
        - auto: Use Playwright for initial requests, detect if needed for others
        """
        if self.js_mode == "full":
            return True
        elif self.js_mode == "off":
            return False
        else:  # auto mode
            # In auto mode, use Playwright by default for initial requests
            # This ensures we get JS-rendered content on first load
            return True

    def _detect_js_requirement(self, response: Response) -> bool:
        """
        Detect if a page requires JavaScript rendering.
        Used in auto mode to decide if Playwright is needed.

        Returns True if the page likely needs JS rendering.
        """
        body = response.text.lower() if hasattr(response, 'text') else ""

        # Check for common JS framework indicators
        js_indicators = [
            # React
            "react", "__react", "data-reactroot", "data-reactid",
            # Vue
            "vue", "__vue__", "data-v-",
            # Angular
            "ng-app", "ng-controller", "angular",
            # Generic SPA indicators
            "app-root", "__next", "__nuxt",
            # Loading states that suggest client-side rendering
            "loading...", "please wait", "javascript required",
        ]

        for indicator in js_indicators:
            if indicator in body:
                return True

        # Check if body content is suspiciously minimal (might be client-rendered)
        # Remove script/style tags and check remaining content
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]+>', '', text_content)
        text_content = text_content.strip()

        # If there's very little text content, might need JS
        if len(text_content) < 100:
            return True

        return False

    def _is_text_response(self, response: Response) -> bool:
        """Check if response contains text content (HTML, XML, etc.)."""
        # Check content-type header
        content_type = response.headers.get(b'Content-Type', b'').decode('utf-8', errors='ignore').lower()
        text_types = ['text/', 'application/xhtml', 'application/xml', 'application/json']
        return any(t in content_type for t in text_types)

    def parse(self, response: Response) -> Generator:
        """Main parse method - extract data and discover links."""
        current_depth = response.meta.get("depth", 0)
        referrer = response.meta.get("referrer")

        # Mark URL as visited (normalized for consistent deduplication)
        self._visited_urls.add(self._normalize_url(response.url))

        # Skip non-text responses (images, PDFs, etc.) - don't save them
        if not self._is_text_response(response):
            self.logger.debug(f"Skipping non-text response: {response.url}")
            return

        # Extract page data
        item = self._extract_page_data(response, current_depth, referrer)
        yield item

        # In crawl mode, follow links if within depth limit (only for successful responses)
        if self.crawl_mode == "crawl" and current_depth < self.max_depth and response.status == 200:
            yield from self._follow_links(response, current_depth)

    def _extract_page_data(self, response: Response, depth: int, referrer: Optional[str]) -> dict:
        """Extract all relevant data from a page response."""
        # Get raw HTML/text content safely
        try:
            raw_html = response.text
        except AttributeError:
            try:
                raw_html = response.body.decode('utf-8', errors='replace')
            except Exception:
                raw_html = ""

        # Extract metadata
        title = self._extract_title(response)
        meta_description = self._extract_meta_description(response)
        h1 = self._extract_h1(response)

        # Extract headers
        request_headers = self._extract_request_headers(response)
        response_headers = self._extract_response_headers(response)

        # Extract screenshot path and performance timing from Playwright page methods
        screenshot_path = response.meta.get("_screenshot_path")
        performance_timing = None
        page_methods = response.meta.get("playwright_page_methods", [])
        if page_methods and len(page_methods) >= 2:
            # The second page method is the evaluate call for timing
            timing_method = page_methods[1] if len(page_methods) > 1 else None
            if timing_method and hasattr(timing_method, 'result') and timing_method.result:
                performance_timing = timing_method.result

        # Get download latency from scrapy-playwright
        download_latency = response.meta.get("download_latency")

        # Extract link locations (nav, header, footer, main)
        link_locations = self._extract_link_locations(response)

        return {
            "url": response.url,
            "status_code": response.status,
            "depth": depth,
            "referrer": referrer,
            "raw_html": raw_html,
            "metadata": {
                "title": title,
                "meta_description": meta_description,
                "h1": h1,
            },
            "request_headers": request_headers,
            "response_headers": response_headers,
            # Performance data
            "performance": {
                "download_latency_s": download_latency,
                "timing": performance_timing,
            },
            # Screenshot (path if captured)
            "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
            # Link locations analysis
            "link_locations": link_locations,
        }

    def _extract_request_headers(self, response: Response) -> dict:
        """Extract request headers from the response's request."""
        headers = {}
        if hasattr(response, 'request') and response.request:
            for key, values in response.request.headers.items():
                # Headers are stored as bytes, decode them
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if values:
                    # Join multiple values with comma (HTTP standard)
                    val_str = b', '.join(values).decode('utf-8') if isinstance(values[0], bytes) else ', '.join(values)
                    headers[key_str] = val_str
        return headers

    def _extract_response_headers(self, response: Response) -> dict:
        """Extract response headers."""
        headers = {}
        for key, values in response.headers.items():
            # Headers are stored as bytes, decode them
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if values:
                # Join multiple values with comma (HTTP standard)
                val_str = b', '.join(values).decode('utf-8') if isinstance(values[0], bytes) else ', '.join(values)
                headers[key_str] = val_str
        return headers

    def _extract_title(self, response: Response) -> Optional[str]:
        """Extract page title from response."""
        try:
            title = response.css("title::text").get()
            if title:
                return title.strip()
        except Exception:
            pass
        return None

    def _extract_meta_description(self, response: Response) -> Optional[str]:
        """Extract meta description from response."""
        try:
            # Try standard meta description
            description = response.css('meta[name="description"]::attr(content)').get()
            if description:
                return description.strip()

            # Try og:description as fallback
            description = response.css('meta[property="og:description"]::attr(content)').get()
            if description:
                return description.strip()
        except Exception:
            pass
        return None

    def _extract_h1(self, response: Response) -> Optional[str]:
        """Extract first h1 from response."""
        try:
            h1 = response.css("h1::text").get()
            if h1:
                return h1.strip()

            # Try getting text from h1 with nested elements
            h1_element = response.css("h1")
            if h1_element:
                h1_text = h1_element.css("*::text").getall()
                if h1_text:
                    return " ".join(t.strip() for t in h1_text if t.strip())
        except Exception:
            pass
        return None

    def _extract_link_locations(self, response: Response) -> Dict[str, Any]:
        """
        Extract links categorized by their location in the page structure.
        Detects: nav, header, footer, aside, main/article/body.

        Returns dict with counts and sample links per location.
        """
        try:
            locations = {
                "nav": {"count": 0, "links": []},
                "header": {"count": 0, "links": []},
                "footer": {"count": 0, "links": []},
                "aside": {"count": 0, "links": []},
                "main": {"count": 0, "links": []},
            }

            # Helper to extract link data
            def get_link_data(a):
                href = a.css("::attr(href)").get()
                text = a.css("::text").get() or ""
                return {"url": href, "anchor": text.strip()[:100] if text else ""}

            # Nav links - <nav> element
            nav_links = response.css("nav a[href]")
            for a in nav_links[:50]:  # Limit to first 50 per category
                locations["nav"]["links"].append(get_link_data(a))
            locations["nav"]["count"] = len(nav_links)

            # Header links - <header> element (excluding nav inside header)
            header_links = response.css("header a[href]:not(nav a)")
            for a in header_links[:20]:
                locations["header"]["links"].append(get_link_data(a))
            locations["header"]["count"] = len(header_links)

            # Footer links - <footer> element
            footer_links = response.css("footer a[href]")
            for a in footer_links[:30]:
                locations["footer"]["links"].append(get_link_data(a))
            locations["footer"]["count"] = len(footer_links)

            # Aside/sidebar links
            aside_links = response.css("aside a[href]")
            for a in aside_links[:20]:
                locations["aside"]["links"].append(get_link_data(a))
            locations["aside"]["count"] = len(aside_links)

            # Main content links - <main>, <article>, or body excluding nav/header/footer/aside
            # Try main first, then article, then fallback
            main_links = response.css("main a[href]")
            if not main_links:
                main_links = response.css("article a[href]")
            if not main_links:
                # Fallback: get all links not in nav/header/footer/aside
                all_links = response.css("a[href]")
                # Filter out structural elements (approximate)
                main_links = response.css(
                    "body a[href]:not(nav a):not(header a):not(footer a):not(aside a)"
                )
            for a in main_links[:50]:
                locations["main"]["links"].append(get_link_data(a))
            locations["main"]["count"] = len(main_links)

            return locations

        except Exception as e:
            self.logger.debug(f"Error extracting link locations: {e}")
            return {
                "nav": {"count": 0, "links": []},
                "header": {"count": 0, "links": []},
                "footer": {"count": 0, "links": []},
                "aside": {"count": 0, "links": []},
                "main": {"count": 0, "links": []},
            }

    def _follow_links(self, response: Response, current_depth: int) -> Generator[Request, None, None]:
        """Extract and follow links from the response."""
        try:
            links = self.link_extractor.extract_links(response)
        except Exception as e:
            self.logger.warning(f"Failed to extract links from {response.url}: {e}")
            return

        for link in links:
            url = link.url
            normalized_url = self._normalize_url(url)

            # Skip already visited URLs
            if normalized_url in self._visited_urls:
                continue

            # Check if URL is within scope
            if not self._is_url_in_scope(url):
                continue

            # Mark as visited to prevent duplicate requests
            self._visited_urls.add(normalized_url)

            yield self._make_request(
                url=url,
                depth=current_depth + 1,
                referrer=response.url,
            )

    def _is_url_in_scope(self, url: str) -> bool:
        """
        Check if URL is within the configured scope.

        Scope types:
        - subdomain: URL must have same full netloc (e.g., www.example.com)
        - domain: URL must have same root domain (e.g., *.example.com)
        - subfolder: URL must be under same path prefix
        - subdomain+subfolder: URL must match both subdomain AND subfolder
        """
        target_info = self._parse_url_info(url)

        # Check against all base URLs - URL is in scope if it matches ANY base URL
        for base_info in self._base_urls_info:
            if self._matches_scope(target_info, base_info):
                return True

        return False

    def _matches_scope(self, target_info: dict, base_info: dict) -> bool:
        """Check if target URL matches the scope criteria against a base URL."""
        if self.scope == "subdomain":
            # Must match exact netloc (full subdomain)
            return target_info["netloc"] == base_info["netloc"]

        elif self.scope == "domain":
            # Must match root domain (allows any subdomain)
            return target_info["domain"] == base_info["domain"]

        elif self.scope == "subfolder":
            # Must be under the same path prefix AND same netloc
            if target_info["netloc"] != base_info["netloc"]:
                return False
            return self._is_under_path(target_info["path"], base_info["path"])

        elif self.scope == "subdomain+subfolder":
            # Must match exact netloc AND be under same path prefix
            if target_info["netloc"] != base_info["netloc"]:
                return False
            return self._is_under_path(target_info["path"], base_info["path"])

        return False

    def _is_under_path(self, target_path: str, base_path: str) -> bool:
        """Check if target path is under (or equal to) base path."""
        # Normalize paths
        target = target_path.rstrip("/")
        base = base_path.rstrip("/")

        # Empty base path means root - everything is under it
        if not base:
            return True

        # Target must start with base path
        if not target.startswith(base):
            return False

        # Make sure it's a proper path boundary (not just prefix match)
        # e.g., /blog should match /blog/post but not /blogger
        if len(target) > len(base):
            return target[len(base)] == "/"

        return True

    def handle_error(self, failure):
        """Handle request errors and still capture failed responses."""
        request = failure.request
        self.logger.warning(f"Request error for {request.url}: {failure.value}")

        # Default empty structures for error responses
        empty_link_locations = {
            "nav": {"count": 0, "links": []},
            "header": {"count": 0, "links": []},
            "footer": {"count": 0, "links": []},
            "aside": {"count": 0, "links": []},
            "main": {"count": 0, "links": []},
        }

        # Try to extract response if available (e.g., for HTTP errors)
        response = getattr(failure.value, 'response', None)
        if response is not None:
            # We have a response - yield it as an item
            current_depth = request.meta.get("depth", 0)
            referrer = request.meta.get("referrer")

            # Check if it's a text response
            if self._is_text_response(response):
                item = self._extract_page_data(response, current_depth, referrer)
                item["error"] = str(failure.value)
                return item
            else:
                # For non-text error responses, create minimal item
                return {
                    "url": response.url,
                    "status_code": response.status,
                    "depth": current_depth,
                    "referrer": referrer,
                    "raw_html": "",
                    "metadata": {
                        "title": None,
                        "meta_description": None,
                        "h1": None,
                    },
                    "request_headers": {},
                    "response_headers": {},
                    "performance": {"download_latency_s": None, "timing": None},
                    "screenshot_path": None,
                    "link_locations": empty_link_locations,
                    "error": str(failure.value),
                }
        else:
            # No response available (connection error, DNS error, etc.)
            # Create a minimal error item
            current_depth = request.meta.get("depth", 0)
            referrer = request.meta.get("referrer")
            return {
                "url": request.url,
                "status_code": None,
                "depth": current_depth,
                "referrer": referrer,
                "raw_html": "",
                "metadata": {
                    "title": None,
                    "meta_description": None,
                    "h1": None,
                },
                "request_headers": {},
                "response_headers": {},
                "performance": {"download_latency_s": None, "timing": None},
                "screenshot_path": None,
                "link_locations": empty_link_locations,
                "error": str(failure.value),
            }
