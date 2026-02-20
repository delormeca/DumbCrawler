import re
import os
import hashlib
import scrapy
from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod
from urllib.parse import urlparse, urljoin
from typing import List, Optional, Generator, Set, Dict, Any


class CrawlEngineSpider(scrapy.Spider):
    """
    CrawlEngine Spider - Reusable crawler with four modes:
    - single: crawl a single URL
    - list: crawl a list of URLs
    - crawl: auto-discovery crawl with depth control
    - sitemap: crawl URLs from XML sitemaps (supports sitemap index, gzip, robots.txt)
    """

    name = "crawl_engine"

    # Handle specific HTTP status codes (errors) while allowing redirects to be followed automatically
    handle_httpstatus_list = [400, 403, 404, 410, 500, 502, 503, 504]

    # Security: Sitemap DoS protection limits
    SITEMAP_REQUEST_TIMEOUT = 30
    SITEMAP_MAX_RECURSION_DEPTH = 5
    SITEMAP_MAX_URLS = 100000

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
        self._sitemap_url_count = 0

        # Screenshot settings
        self._screenshot_enabled = self.js_mode != "off"
        self._screenshot_dir: Optional[str] = None

        self.logger.info(f"CrawlEngine initialized:")
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
        Used for SSRF protection (prevents DNS rebinding attacks).
        """
        import socket
        import ipaddress

        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except Exception as e:
            self.logger.error(f"Failed to resolve hostname {hostname}: {e}")
            return True

    def _validate_sitemap_url_security(self, url_string: str) -> tuple:
        """
        Validate sitemap URL for security (SSRF protection).
        Returns (is_valid, error_message)
        """
        try:
            parsed = urlparse(url_string)
            if parsed.scheme != 'https':
                return (False, f"Sitemap URL must use HTTPS: {url_string}")
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
        """
        from scrapy.http import XmlResponse
        from scrapy.utils.gz import gunzip, gzip_magic_number
        from scrapy.utils._compression import _DecompressionMaxSizeExceeded

        try:
            if isinstance(response, XmlResponse):
                return response.body

            if gzip_magic_number(response):
                try:
                    max_size = getattr(self, '_max_sitemap_size', 10 * 1024 * 1024)
                    return gunzip(response.body, max_size=max_size)
                except _DecompressionMaxSizeExceeded:
                    self.logger.error(f"Sitemap {response.url} exceeds maximum decompressed size")
                    return None
                except Exception as e:
                    self.logger.error(f"Failed to decompress sitemap {response.url}: {e}")
                    return None

            if response.url.endswith('.xml') or response.url.endswith('.xml.gz'):
                return response.body

            if response.body.strip().startswith(b'<?xml') or b'<urlset' in response.body[:500] or b'<sitemapindex' in response.body[:500]:
                return response.body

        except Exception as e:
            self.logger.error(f"Error getting sitemap body from {response.url}: {e}")

        return None

    def _parse_sitemap(self, response: Response) -> Generator[Request, None, None]:
        """Parse sitemap XML and yield requests for discovered URLs."""
        from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

        if response.url.endswith('/robots.txt'):
            self.logger.info(f"Extracting sitemaps from robots.txt: {response.url}")
            try:
                for sitemap_url in sitemap_urls_from_robots(response.text, base_url=response.url):
                    self.logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
                    yield Request(sitemap_url, callback=self._parse_sitemap)
            except Exception as e:
                self.logger.error(f"Failed to parse robots.txt {response.url}: {e}")
            return

        body = self._get_sitemap_body(response)
        if body is None:
            self.logger.warning(f"Ignoring invalid sitemap: {response.url}")
            return

        try:
            sitemap = Sitemap(body)
        except Exception as e:
            self.logger.error(f"Failed to parse sitemap XML {response.url}: {e}")
            return

        sitemap_entries = self._filter_sitemap_entries(sitemap)

        if sitemap.type == "sitemapindex":
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

                yield Request(
                    loc,
                    callback=self._parse_sitemap,
                    priority=10,
                    meta={'sitemap_depth': current_depth + 1}
                )

            self.logger.info(f"Sitemap index contains {sitemap_count} sitemaps")

        elif sitemap.type == "urlset":
            self.logger.info(f"Processing sitemap urlset: {response.url}")
            url_count = 0
            skipped_scope = 0
            skipped_duplicate = 0

            for entry in sitemap_entries:
                urls_to_crawl = [entry.get('loc')]

                if self.sitemap_alternate_links and 'alternate' in entry:
                    urls_to_crawl.extend(entry['alternate'])

                for url in urls_to_crawl:
                    if not url:
                        continue

                    url = url.strip()

                    if not self._is_url_in_scope(url):
                        skipped_scope += 1
                        continue

                    normalized_url = self._normalize_url(url)
                    if normalized_url in self._visited_urls:
                        skipped_duplicate += 1
                        continue

                    if self._sitemap_url_count >= self.SITEMAP_MAX_URLS:
                        self.logger.error(
                            f"Sitemap URL limit reached ({self.SITEMAP_MAX_URLS}). "
                            f"Stopping extraction to prevent resource exhaustion."
                        )
                        return

                    self._visited_urls.add(normalized_url)
                    url_count += 1
                    self._sitemap_url_count += 1

                    if self._sitemap_url_count % 1000 == 0:
                        self.logger.info(
                            f"Sitemap progress: {self._sitemap_url_count}/{self.SITEMAP_MAX_URLS} URLs extracted"
                        )

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
        Filter sitemap entries. Override for custom filtering logic.
        Default: yield all entries unchanged.
        """
        for entry in sitemap:
            yield entry

    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests based on mode."""
        if self._screenshot_enabled:
            output_dir = self.crawler.settings.get('CRAWL_OUTPUT_DIR', 'output')
            self._screenshot_dir = os.path.join(output_dir, 'screenshots')
            os.makedirs(self._screenshot_dir, exist_ok=True)
            self.logger.info(f"Screenshots enabled, saving to: {self._screenshot_dir}")

        if self.crawl_mode == "sitemap":
            self.logger.info(f"Starting sitemap mode with {len(self.start_urls)} sitemap URL(s)")
            self.logger.info(f"Security limits: timeout={self.SITEMAP_REQUEST_TIMEOUT}s, max_depth={self.SITEMAP_MAX_RECURSION_DEPTH}, max_urls={self.SITEMAP_MAX_URLS}")

            self.custom_settings = {
                'DOWNLOAD_TIMEOUT': self.SITEMAP_REQUEST_TIMEOUT,
            }

            for sitemap_url in self.start_urls:
                is_valid, error_msg = self._validate_sitemap_url_security(sitemap_url)
                if not is_valid:
                    self.logger.error(f"Sitemap URL failed security validation: {error_msg}")
                    continue

                self.logger.info(f"Fetching sitemap: {sitemap_url}")
                yield Request(
                    sitemap_url,
                    callback=self._parse_sitemap,
                    errback=self.handle_error,
                    priority=100,
                    dont_filter=True,
                    meta={'sitemap_depth': 0}
                )

        else:
            for url in self.start_urls:
                normalized_url = self._normalize_url(url)
                self._visited_urls.add(normalized_url)
                yield self._make_request(url, depth=0, referrer=None, dont_filter=True)

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent duplicate detection."""
        parsed = urlparse(url)
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

        if use_playwright and self._screenshot_enabled and self._screenshot_dir:
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
            screenshot_path = os.path.join(self._screenshot_dir, f"{url_hash}.png")

            meta["playwright_page_methods"] = [
                PageMethod("screenshot", path=screenshot_path, full_page=True),
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
        """Determine if Playwright should be used for this request."""
        if self.js_mode == "full":
            return True
        elif self.js_mode == "off":
            return False
        else:  # auto mode
            return True

    def _detect_js_requirement(self, response: Response) -> bool:
        """Detect if a page requires JavaScript rendering."""
        body = response.text.lower() if hasattr(response, 'text') else ""

        js_indicators = [
            "react", "__react", "data-reactroot", "data-reactid",
            "vue", "__vue__", "data-v-",
            "ng-app", "ng-controller", "angular",
            "app-root", "__next", "__nuxt",
            "loading...", "please wait", "javascript required",
        ]

        for indicator in js_indicators:
            if indicator in body:
                return True

        text_content = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]+>', '', text_content)
        text_content = text_content.strip()

        if len(text_content) < 100:
            return True

        return False

    def _is_text_response(self, response: Response) -> bool:
        """Check if response contains text content (HTML, XML, etc.)."""
        content_type = response.headers.get(b'Content-Type', b'').decode('utf-8', errors='ignore').lower()
        text_types = ['text/', 'application/xhtml', 'application/xml', 'application/json']
        return any(t in content_type for t in text_types)

    def parse(self, response: Response) -> Generator:
        """Main parse method - extract data and discover links."""
        current_depth = response.meta.get("depth", 0)
        referrer = response.meta.get("referrer")

        self._visited_urls.add(self._normalize_url(response.url))

        if not self._is_text_response(response):
            self.logger.debug(f"Skipping non-text response: {response.url}")
            return

        item = self._extract_page_data(response, current_depth, referrer)
        yield item

        if self.crawl_mode == "crawl" and current_depth < self.max_depth and response.status == 200:
            yield from self._follow_links(response, current_depth)

    def _extract_page_data(self, response: Response, depth: int, referrer: Optional[str]) -> dict:
        """Extract all relevant data from a page response."""
        try:
            raw_html = response.text
        except AttributeError:
            try:
                raw_html = response.body.decode('utf-8', errors='replace')
            except Exception:
                raw_html = ""

        title = self._extract_title(response)
        meta_description = self._extract_meta_description(response)
        h1 = self._extract_h1(response)

        request_headers = self._extract_request_headers(response)
        response_headers = self._extract_response_headers(response)

        screenshot_path = response.meta.get("_screenshot_path")
        performance_timing = None
        page_methods = response.meta.get("playwright_page_methods", [])
        if page_methods and len(page_methods) >= 2:
            timing_method = page_methods[1] if len(page_methods) > 1 else None
            if timing_method and hasattr(timing_method, 'result') and timing_method.result:
                performance_timing = timing_method.result

        download_latency = response.meta.get("download_latency")
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
            "performance": {
                "download_latency_s": download_latency,
                "timing": performance_timing,
            },
            "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
            "link_locations": link_locations,
        }

    def _extract_request_headers(self, response: Response) -> dict:
        """Extract request headers from the response's request."""
        headers = {}
        if hasattr(response, 'request') and response.request:
            for key, values in response.request.headers.items():
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if values:
                    val_str = b', '.join(values).decode('utf-8') if isinstance(values[0], bytes) else ', '.join(values)
                    headers[key_str] = val_str
        return headers

    def _extract_response_headers(self, response: Response) -> dict:
        """Extract response headers."""
        headers = {}
        for key, values in response.headers.items():
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if values:
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
            description = response.css('meta[name="description"]::attr(content)').get()
            if description:
                return description.strip()
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
            h1_element = response.css("h1")
            if h1_element:
                h1_text = h1_element.css("*::text").getall()
                if h1_text:
                    return " ".join(t.strip() for t in h1_text if t.strip())
        except Exception:
            pass
        return None

    def _extract_link_locations(self, response: Response) -> Dict[str, Any]:
        """Extract links categorized by their location in the page structure."""
        try:
            locations = {
                "nav": {"count": 0, "links": []},
                "header": {"count": 0, "links": []},
                "footer": {"count": 0, "links": []},
                "aside": {"count": 0, "links": []},
                "main": {"count": 0, "links": []},
            }

            def get_link_data(a):
                href = a.css("::attr(href)").get()
                text = a.css("::text").get() or ""
                return {"url": href, "anchor": text.strip()[:100] if text else ""}

            nav_links = response.css("nav a[href]")
            for a in nav_links[:50]:
                locations["nav"]["links"].append(get_link_data(a))
            locations["nav"]["count"] = len(nav_links)

            header_links = response.css("header a[href]:not(nav a)")
            for a in header_links[:20]:
                locations["header"]["links"].append(get_link_data(a))
            locations["header"]["count"] = len(header_links)

            footer_links = response.css("footer a[href]")
            for a in footer_links[:30]:
                locations["footer"]["links"].append(get_link_data(a))
            locations["footer"]["count"] = len(footer_links)

            aside_links = response.css("aside a[href]")
            for a in aside_links[:20]:
                locations["aside"]["links"].append(get_link_data(a))
            locations["aside"]["count"] = len(aside_links)

            main_links = response.css("main a[href]")
            if not main_links:
                main_links = response.css("article a[href]")
            if not main_links:
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

            if normalized_url in self._visited_urls:
                continue

            if not self._is_url_in_scope(url):
                continue

            self._visited_urls.add(normalized_url)

            yield self._make_request(
                url=url,
                depth=current_depth + 1,
                referrer=response.url,
            )

    def _is_url_in_scope(self, url: str) -> bool:
        """Check if URL is within the configured scope."""
        target_info = self._parse_url_info(url)

        for base_info in self._base_urls_info:
            if self._matches_scope(target_info, base_info):
                return True

        return False

    def _matches_scope(self, target_info: dict, base_info: dict) -> bool:
        """Check if target URL matches the scope criteria against a base URL."""
        if self.scope == "subdomain":
            return target_info["netloc"] == base_info["netloc"]

        elif self.scope == "domain":
            return target_info["domain"] == base_info["domain"]

        elif self.scope == "subfolder":
            if target_info["netloc"] != base_info["netloc"]:
                return False
            return self._is_under_path(target_info["path"], base_info["path"])

        elif self.scope == "subdomain+subfolder":
            if target_info["netloc"] != base_info["netloc"]:
                return False
            return self._is_under_path(target_info["path"], base_info["path"])

        return False

    def _is_under_path(self, target_path: str, base_path: str) -> bool:
        """Check if target path is under (or equal to) base path."""
        target = target_path.rstrip("/")
        base = base_path.rstrip("/")

        if not base:
            return True

        if not target.startswith(base):
            return False

        if len(target) > len(base):
            return target[len(base)] == "/"

        return True

    def handle_error(self, failure):
        """Handle request errors and still capture failed responses."""
        request = failure.request
        self.logger.warning(f"Request error for {request.url}: {failure.value}")

        empty_link_locations = {
            "nav": {"count": 0, "links": []},
            "header": {"count": 0, "links": []},
            "footer": {"count": 0, "links": []},
            "aside": {"count": 0, "links": []},
            "main": {"count": 0, "links": []},
        }

        response = getattr(failure.value, 'response', None)
        if response is not None:
            current_depth = request.meta.get("depth", 0)
            referrer = request.meta.get("referrer")

            if self._is_text_response(response):
                item = self._extract_page_data(response, current_depth, referrer)
                item["error"] = str(failure.value)
                return item
            else:
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
