#!/usr/bin/env python3
"""
CrawlEngine - Run crawler programmatically or via command line.

Usage:
    # As a library
    from crawl_engine import run_crawler
    run_crawler(mode="crawl", start_urls="https://example.com", max_depth=2)

    # From command line
    python -m crawl_engine --mode crawl --start-urls "https://example.com" --max-depth 2
"""

import argparse
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_crawler(
    mode: str = "single",
    start_urls: str = "",
    max_depth: int = 2,
    scope: str = "domain",
    js_mode: str = "off",
    output_dir: str = "output",
    log_level: str = "INFO",
    settings_override: dict = None,
):
    """
    Run the CrawlEngine spider programmatically.

    Args:
        mode: Crawl mode - 'single', 'list', 'crawl', or 'sitemap'
        start_urls: Comma-separated URLs to crawl
        max_depth: Maximum depth for auto-discovery crawl
        scope: URL scope restriction
        js_mode: JavaScript rendering mode
        output_dir: Directory for JSON output
        log_level: Logging verbosity
        settings_override: Additional Scrapy settings to override

    Returns:
        None (results are saved to output directory)
    """
    # Build settings from the crawl_engine defaults
    original_dir = os.getcwd()
    settings_module_dir = os.path.dirname(__file__)

    # Set the settings module so Scrapy finds our settings
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'crawl_engine.settings'

    try:
        settings = get_project_settings()

        # Override settings
        settings.set('LOG_LEVEL', log_level)
        settings.set('CRAWL_OUTPUT_DIR', os.path.join(original_dir, output_dir))

        # Apply any additional settings
        if settings_override:
            for key, value in settings_override.items():
                settings.set(key, value)

        # Create crawler process
        process = CrawlerProcess(settings)

        # Add the spider with arguments
        process.crawl(
            'crawl_engine',
            mode=mode,
            start_urls=start_urls,
            max_depth=max_depth,
            scope=scope,
            js_mode=js_mode,
        )

        # Start the crawl
        process.start()

    finally:
        # Clean up env var
        if 'SCRAPY_SETTINGS_MODULE' in os.environ:
            del os.environ['SCRAPY_SETTINGS_MODULE']


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CrawlEngine - Reusable web crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single URL crawl
  python -m crawl_engine --mode single --start-urls "https://example.com"

  # Multiple URLs
  python -m crawl_engine --mode list --start-urls "https://a.com,https://b.com"

  # Auto-discovery crawl with depth 3
  python -m crawl_engine --mode crawl --start-urls "https://example.com" --max-depth 3

  # JS-rendered crawl with subdomain scope
  python -m crawl_engine --mode crawl --start-urls "https://spa.example.com" --js-mode full --scope subdomain

  # Sitemap crawl
  python -m crawl_engine --mode sitemap --start-urls "https://example.com/sitemap.xml"
        """
    )

    parser.add_argument(
        '--mode',
        choices=['single', 'list', 'crawl', 'sitemap'],
        default='single',
        help='Crawl mode (default: single)'
    )

    parser.add_argument(
        '--start-urls',
        required=True,
        help='Comma-separated URLs to crawl'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=2,
        help='Maximum crawl depth for crawl mode (default: 2)'
    )

    parser.add_argument(
        '--scope',
        choices=['subdomain', 'domain', 'subfolder', 'subdomain+subfolder'],
        default='domain',
        help='URL scope restriction (default: domain)'
    )

    parser.add_argument(
        '--js-mode',
        choices=['off', 'auto', 'full'],
        default='off',
        help='JavaScript rendering mode (default: off)'
    )

    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for JSON files (default: output)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    print(f"CrawlEngine starting...")
    print(f"  Mode: {args.mode}")
    print(f"  URLs: {args.start_urls}")
    print(f"  Max Depth: {args.max_depth}")
    print(f"  Scope: {args.scope}")
    print(f"  JS Mode: {args.js_mode}")
    print(f"  Output: {args.output_dir}")
    print()

    run_crawler(
        mode=args.mode,
        start_urls=args.start_urls,
        max_depth=args.max_depth,
        scope=args.scope,
        js_mode=args.js_mode,
        output_dir=args.output_dir,
        log_level=args.log_level,
    )


if __name__ == '__main__':
    main()
