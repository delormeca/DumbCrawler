"""
crawl_engine - Reusable web crawling engine extracted from DumbCrawler.

A Scrapy-based crawling engine with 4 modes (single, list, crawl, sitemap),
comprehensive data extraction pipelines, GEO (Generative Engine Optimization)
analysis, Playwright stealth browsing, and link validation.

Usage:
    from crawl_engine import run_crawler

    run_crawler(
        mode="crawl",
        start_urls="https://example.com",
        max_depth=2,
        scope="domain",
        js_mode="off",
        output_dir="output",
    )
"""

from crawl_engine.runner import run_crawler
from crawl_engine.link_validator import validate_links, validate_internal_links

__version__ = "1.0.0"
__all__ = [
    "run_crawler",
    "validate_links",
    "validate_internal_links",
]
