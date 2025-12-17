#!/usr/bin/env python3
"""
DumbCrawler - Run a crawl job with API integration.

This script fetches crawl job details from the SaaS API and runs the crawler,
sending results back to the API as they are crawled.

Supports pause/resume via signals:
- SIGSTOP/CTRL+BREAK: Pause crawling
- SIGCONT: Resume crawling
- SIGTERM: Graceful shutdown

Usage:
    python run_crawl_job.py --job-id <crawl_job_id> --api-url <api_base_url>

Example:
    python run_crawl_job.py --job-id "abc123" --api-url "http://localhost:3000"
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error
import signal
import threading
import time
from datetime import datetime, timezone

# Add the scrapy_app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapy_app'))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class CrawlJobController:
    """Controls the crawl job state for pause/resume functionality."""

    def __init__(self, job_id: str, api_url: str):
        self.job_id = job_id
        self.api_url = api_url
        self.paused = False
        self.should_stop = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Not paused initially
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for pause/resume/stop."""
        if os.name != 'nt':
            # Unix signals
            signal.signal(signal.SIGTERM, self._handle_stop)
            signal.signal(signal.SIGINT, self._handle_stop)
            # Note: SIGSTOP cannot be caught, but SIGUSR1/SIGUSR2 can be used
            signal.signal(signal.SIGUSR1, self._handle_pause)
            signal.signal(signal.SIGUSR2, self._handle_resume)
        else:
            # Windows: CTRL+C and CTRL+BREAK
            signal.signal(signal.SIGINT, self._handle_stop)
            signal.signal(signal.SIGBREAK, self._handle_pause)

    def _handle_pause(self, signum, frame):
        """Handle pause signal."""
        if not self.paused:
            print(f"\n[PAUSE] Crawl job {self.job_id} pausing...")
            self.paused = True
            self.pause_event.clear()
            self._update_status("paused")

    def _handle_resume(self, signum, frame):
        """Handle resume signal."""
        if self.paused:
            print(f"\n[RESUME] Crawl job {self.job_id} resuming...")
            self.paused = False
            self.pause_event.set()
            self._update_status("running")

    def _handle_stop(self, signum, frame):
        """Handle stop signal."""
        print(f"\n[STOP] Crawl job {self.job_id} stopping gracefully...")
        self.should_stop = True
        if self.paused:
            self.pause_event.set()  # Unblock if paused

    def _update_status(self, status: str):
        """Update job status in database via API."""
        try:
            payload = {
                "crawl_job_id": self.job_id,
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.api_url.rstrip('/')}/api/crawl/status",
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'DumbCrawler/2.0',
                },
                method='POST'
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            print(f"Warning: Could not update status to '{status}': {e}")

    def wait_if_paused(self):
        """Block execution if paused. Returns True if should continue, False if should stop."""
        self.pause_event.wait()
        return not self.should_stop


# Global controller instance
_controller: CrawlJobController = None


def fetch_job_details(api_base_url: str, job_id: str) -> dict:
    """
    Fetch crawl job details from the API.

    Returns dict with:
    - id: crawl job ID
    - project_id: project ID
    - domain: domain to crawl
    - settings: project settings (scope, jsMode, maxPages)
    """
    url = f"{api_base_url.rstrip('/')}/api/crawl/job/{job_id}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'DumbCrawler/2.0',
                'Accept': 'application/json',
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        print(f"Failed to fetch job details: HTTP {e.code} - {error_body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Failed to connect to API: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching job details: {e}")
        sys.exit(1)


def run_crawl_job(
    job_id: str,
    project_id: str,
    domain: str,
    api_url: str,
    scope: str = "domain",
    js_mode: str = "off",
    max_pages: int = 500,
    max_depth: int = 10,
    log_level: str = "INFO",
    urls: list = None,  # Specific URLs to crawl (for targeted re-crawls)
    crawl_mode: str = "full",  # "full" | "urls_only" | "sitemap"
    sitemap_url: str = None,  # Sitemap URL for sitemap mode
):
    """
    Run a crawl job with API integration.

    Results are sent to the API endpoint as they are crawled.

    If urls is provided and crawl_mode is "urls_only", only those specific
    URLs will be crawled (no link following). Otherwise, a full site crawl
    is performed starting from the domain.
    """
    # Change to the scrapy_app directory so settings are found
    original_dir = os.getcwd()
    scrapy_app_dir = os.path.join(os.path.dirname(__file__), 'scrapy_app')
    os.chdir(scrapy_app_dir)

    try:
        # Get project settings
        settings = get_project_settings()

        # Override settings
        settings.set('LOG_LEVEL', log_level)

        # API settings for ApiPipeline
        settings.set('API_URL', f"{api_url.rstrip('/')}/api/crawl/results")
        settings.set('CRAWL_JOB_ID', job_id)
        settings.set('PROJECT_ID', project_id)
        settings.set('API_KEY', job_id)  # Using job_id as API key for MVP

        # Enable API pipeline, disable JSON file output for API mode
        settings.set('ITEM_PIPELINES', {
            "dumbcrawler.pipelines.DumbCrawlerPipeline": 300,
            "dumbcrawler.pipelines.ApiPipeline": 500,
        })

        # Limit max pages via CLOSESPIDER_PAGECOUNT
        if max_pages:
            settings.set('CLOSESPIDER_PAGECOUNT', max_pages)

        # Create crawler process
        process = CrawlerProcess(settings)

        # Determine start URLs and spider arguments based on crawl mode
        if crawl_mode == "sitemap":
            # Sitemap crawl: fetch URLs from sitemap
            if not sitemap_url:
                raise ValueError("sitemap_url is required for sitemap crawl mode")

            start_urls = sitemap_url
            spider_mode = 'sitemap'
            effective_max_depth = 0  # Not applicable for sitemap mode

            print(f"Starting SITEMAP crawl job: {job_id}")
            print(f"  Sitemap URL: {sitemap_url}")
            print(f"  Domain: {domain}")
            print(f"  Scope: {scope}")
            print(f"  JS Mode: {js_mode}")
            print(f"  API URL: {api_url}")
            print()

            # Add the spider with sitemap mode arguments
            process.crawl(
                'dumbcrawler',
                mode='sitemap',
                start_urls=start_urls,
                scope=scope,
                js_mode=js_mode,
            )

        elif urls and crawl_mode == "urls_only":
            # Targeted re-crawl: use specific URLs, no link following
            start_urls = ",".join(urls)
            effective_max_depth = 0  # Don't follow links
            print(f"Starting TARGETED crawl job: {job_id}")
            print(f"  URLs to crawl: {len(urls)}")
            for url in urls[:5]:  # Show first 5
                print(f"    - {url}")
            if len(urls) > 5:
                print(f"    ... and {len(urls) - 5} more")
            print(f"  Scope: {scope}")
            print(f"  JS Mode: {js_mode}")
            print(f"  Max Pages: {max_pages}")
            print(f"  Max Depth: {effective_max_depth}")
            print(f"  API URL: {api_url}")
            print()

            # Add the spider with arguments
            # Use mode='list' to prevent link following (not 'crawl')
            process.crawl(
                'dumbcrawler',
                mode='list',
                start_urls=start_urls,
                max_depth=effective_max_depth,
                scope=scope,
                js_mode=js_mode,
            )

        else:
            # Full site crawl: start from domain
            start_urls = f"https://{domain}"
            if not domain.startswith(('http://', 'https://')):
                start_urls = f"https://{domain}"
            else:
                start_urls = domain
            effective_max_depth = max_depth
            print(f"Starting FULL crawl job: {job_id}")
            print(f"  Domain: {domain}")
            print(f"  Scope: {scope}")
            print(f"  JS Mode: {js_mode}")
            print(f"  Max Pages: {max_pages}")
            print(f"  Max Depth: {effective_max_depth}")
            print(f"  API URL: {api_url}")
            print()

            # Add the spider with arguments
            process.crawl(
                'dumbcrawler',
                mode='crawl',
                start_urls=start_urls,
                max_depth=effective_max_depth,
                scope=scope,
                js_mode=js_mode,
            )

        # Start the crawl
        process.start()

        print(f"Crawl job {job_id} completed!")

    except Exception as e:
        print(f"Crawl error: {e}")
        # Try to send failure status
        try:
            send_failure_status(api_url, job_id, project_id, str(e))
        except Exception:
            pass
        raise

    finally:
        os.chdir(original_dir)


def send_failure_status(api_url: str, job_id: str, project_id: str, error: str):
    """Send a failure status to the API if crawl fails before starting."""
    payload = {
        "crawl_job_id": job_id,
        "project_id": project_id,
        "api_key": job_id,
        "status": "failed",
        "pages": [],
        "stats": {
            "pages_queued": 0,
            "pages_crawled": 0,
            "pages_errored": 0,
        },
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{api_url.rstrip('/')}/api/crawl/results",
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'DumbCrawler/2.0',
            },
            method='POST'
        )
        urllib.request.urlopen(req, timeout=30)
    except Exception:
        pass  # Best effort


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DumbCrawler - Run a crawl job with API integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a crawl job fetching details from API
  python run_crawl_job.py --job-id "abc123" --api-url "http://localhost:3000"

  # Run with specific settings (without fetching from API)
  python run_crawl_job.py --job-id "abc123" --project-id "proj456" --domain "example.com" --api-url "http://localhost:3000"
        """
    )

    parser.add_argument(
        '--job-id',
        required=True,
        help='Crawl job ID'
    )

    parser.add_argument(
        '--api-url',
        required=True,
        help='Base URL of the SaaS API (e.g., http://localhost:3000)'
    )

    parser.add_argument(
        '--project-id',
        help='Project ID (optional, fetched from API if not provided)'
    )

    parser.add_argument(
        '--domain',
        help='Domain to crawl (optional, fetched from API if not provided)'
    )

    parser.add_argument(
        '--scope',
        choices=['subdomain', 'domain', 'subfolder', 'subdomain+subfolder'],
        help='URL scope restriction (optional, uses project settings if not provided)'
    )

    parser.add_argument(
        '--js-mode',
        choices=['off', 'auto', 'full'],
        help='JavaScript rendering mode (optional, uses project settings if not provided)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum pages to crawl (optional, uses project settings if not provided)'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=10,
        help='Maximum crawl depth (default: 10)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # If domain or project_id not provided, fetch from API
    urls = None
    crawl_mode = "full"
    sitemap_url = None

    if not args.domain or not args.project_id:
        print(f"Fetching job details from API...")
        job_details = fetch_job_details(args.api_url, args.job_id)

        project_id = args.project_id or job_details.get('project_id')
        domain = args.domain or job_details.get('domain')
        settings = job_details.get('settings', {})

        # Use settings from API if not overridden
        scope = args.scope or settings.get('scope', 'domain')
        js_mode = args.js_mode or settings.get('jsMode', 'off')
        max_pages = args.max_pages or settings.get('maxPages', 500)

        # Get specific URLs and crawl mode from job details (top-level fields, not in settings)
        urls = job_details.get('urls')
        crawl_mode = job_details.get('crawlMode', 'full')
        sitemap_url = settings.get('sitemapUrl')

        # Get maxDepth from API settings (smart defaults based on crawl mode)
        max_depth_from_api = settings.get('maxDepth')
    else:
        project_id = args.project_id
        domain = args.domain
        scope = args.scope or 'domain'
        js_mode = args.js_mode or 'off'
        max_pages = args.max_pages or 500
        max_depth_from_api = None

    # Determine effective max_depth
    # Priority: command-line arg > API setting > smart default based on mode
    if args.max_depth != 10:  # 10 is the default, so user explicitly set a value
        effective_max_depth = args.max_depth
    elif max_depth_from_api is not None:
        effective_max_depth = max_depth_from_api
    else:
        # Smart defaults: 0 for URL-only/sitemap, 10 for full crawl
        if crawl_mode in ('urls_only', 'sitemap', 'all_existing'):
            effective_max_depth = 0
        else:
            effective_max_depth = 10

    if not domain:
        print("Error: Domain is required. Provide --domain or ensure API returns domain.")
        sys.exit(1)

    if not project_id:
        print("Error: Project ID is required. Provide --project-id or ensure API returns project_id.")
        sys.exit(1)

    # Debug: Show effective max_depth
    print(f"Max depth: {effective_max_depth} (from API: {max_depth_from_api}, arg: {args.max_depth}, mode: {crawl_mode})")

    run_crawl_job(
        job_id=args.job_id,
        project_id=project_id,
        domain=domain,
        api_url=args.api_url,
        scope=scope,
        js_mode=js_mode,
        max_pages=max_pages,
        max_depth=effective_max_depth,
        log_level=args.log_level,
        urls=urls,
        crawl_mode=crawl_mode,
        sitemap_url=sitemap_url,
    )


if __name__ == '__main__':
    main()
