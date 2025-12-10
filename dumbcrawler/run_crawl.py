#!/usr/bin/env python3
"""
Programmatic runner for dumbcrawler.
Usage: python run_crawl.py [arguments]
"""
import argparse
import os
import sys
import uuid

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
