#!/usr/bin/env python3
"""
Test script for sitemap mode implementation.

This script validates that sitemap crawling works correctly with various
sitemap formats and edge cases.

Usage:
    python test_sitemap_mode.py
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the scrapy_app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crawler', 'scrapy_app'))

def test_spider_imports():
    """Test that spider and utilities can be imported."""
    print("=" * 60)
    print("TEST 1: Import Spider and Dependencies")
    print("=" * 60)

    try:
        from dumbcrawler.spiders.crawler_spider import DumbCrawlerSpider
        print("✓ Spider import successful")
    except ImportError as e:
        print(f"✗ Spider import failed: {e}")
        return False

    try:
        from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
        print("✓ Scrapy sitemap utilities import successful")
    except ImportError as e:
        print(f"✗ Scrapy utilities import failed: {e}")
        return False

    print("\n✓ All imports successful\n")
    return True


def test_sitemap_mode_initialization():
    """Test spider initialization with sitemap mode."""
    print("=" * 60)
    print("TEST 2: Sitemap Mode Initialization")
    print("=" * 60)

    from dumbcrawler.spiders.crawler_spider import DumbCrawlerSpider

    # Test 1: Basic sitemap initialization
    try:
        spider = DumbCrawlerSpider(
            mode='sitemap',
            start_urls='https://www.sitemaps.org/sitemap.xml'
        )
        assert spider.crawl_mode == 'sitemap'
        assert spider.start_urls == ['https://www.sitemaps.org/sitemap.xml']
        print("✓ Basic sitemap initialization successful")
    except Exception as e:
        print(f"✗ Basic initialization failed: {e}")
        return False

    # Test 2: Multiple sitemaps
    try:
        spider = DumbCrawlerSpider(
            mode='sitemap',
            start_urls='https://example.com/sitemap1.xml,https://example.com/sitemap2.xml'
        )
        assert len(spider.start_urls) == 2
        print("✓ Multiple sitemaps initialization successful")
    except Exception as e:
        print(f"✗ Multiple sitemaps failed: {e}")
        return False

    # Test 3: Sitemap with alternate links
    try:
        spider = DumbCrawlerSpider(
            mode='sitemap',
            start_urls='https://example.com/sitemap.xml',
            sitemap_alternate_links='true'
        )
        assert spider.sitemap_alternate_links == True
        print("✓ Alternate links parameter successful")
    except Exception as e:
        print(f"✗ Alternate links failed: {e}")
        return False

    # Test 4: Sitemap with JS mode
    try:
        spider = DumbCrawlerSpider(
            mode='sitemap',
            start_urls='https://example.com/sitemap.xml',
            js_mode='full'
        )
        assert spider.js_mode == 'full'
        print("✓ JS mode parameter successful")
    except Exception as e:
        print(f"✗ JS mode failed: {e}")
        return False

    print("\n✓ All initialization tests passed\n")
    return True


def test_sitemap_methods_exist():
    """Test that required sitemap methods exist."""
    print("=" * 60)
    print("TEST 3: Sitemap Methods Existence")
    print("=" * 60)

    from dumbcrawler.spiders.crawler_spider import DumbCrawlerSpider

    spider = DumbCrawlerSpider(
        mode='sitemap',
        start_urls='https://example.com/sitemap.xml'
    )

    required_methods = [
        '_get_sitemap_body',
        '_parse_sitemap',
        '_filter_sitemap_entries',
    ]

    for method_name in required_methods:
        if not hasattr(spider, method_name):
            print(f"✗ Missing method: {method_name}")
            return False

        method = getattr(spider, method_name)
        if not callable(method):
            print(f"✗ {method_name} is not callable")
            return False

        print(f"✓ {method_name} exists and is callable")

    print("\n✓ All required methods exist\n")
    return True


def test_sitemap_xml_parsing():
    """Test XML sitemap parsing."""
    print("=" * 60)
    print("TEST 4: Sitemap XML Parsing")
    print("=" * 60)

    from scrapy.utils.sitemap import Sitemap

    # Test 1: Regular sitemap
    sitemap_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page1</loc>
    <lastmod>2024-01-01</lastmod>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://example.com/page2</loc>
    <lastmod>2024-01-02</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>"""

    try:
        sitemap = Sitemap(sitemap_xml)
        assert sitemap.type == 'urlset'

        urls = list(sitemap)
        assert len(urls) == 2
        assert urls[0]['loc'] == 'https://example.com/page1'
        assert urls[0]['lastmod'] == '2024-01-01'
        assert urls[0]['priority'] == '1.0'
        assert urls[1]['loc'] == 'https://example.com/page2'

        print("✓ Regular sitemap parsing successful")
    except Exception as e:
        print(f"✗ Regular sitemap parsing failed: {e}")
        return False

    # Test 2: Sitemap index
    index_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap1.xml</loc>
    <lastmod>2024-01-01</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap2.xml</loc>
    <lastmod>2024-01-02</lastmod>
  </sitemap>
</sitemapindex>"""

    try:
        sitemap_index = Sitemap(index_xml)
        assert sitemap_index.type == 'sitemapindex'

        sitemaps = list(sitemap_index)
        assert len(sitemaps) == 2
        assert sitemaps[0]['loc'] == 'https://example.com/sitemap1.xml'
        assert sitemaps[1]['loc'] == 'https://example.com/sitemap2.xml'

        print("✓ Sitemap index parsing successful")
    except Exception as e:
        print(f"✗ Sitemap index parsing failed: {e}")
        return False

    # Test 3: Sitemap with alternate links
    alt_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://example.com/page</loc>
    <xhtml:link rel="alternate" hreflang="es" href="https://example.com/es/page"/>
    <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/page"/>
  </url>
</urlset>"""

    try:
        sitemap_alt = Sitemap(alt_xml)
        urls = list(sitemap_alt)
        assert len(urls) == 1
        assert 'alternate' in urls[0]
        assert len(urls[0]['alternate']) == 2

        print("✓ Alternate links parsing successful")
    except Exception as e:
        print(f"✗ Alternate links parsing failed: {e}")
        return False

    print("\n✓ All XML parsing tests passed\n")
    return True


def test_mode_validation():
    """Test mode validation."""
    print("=" * 60)
    print("TEST 5: Mode Validation")
    print("=" * 60)

    from dumbcrawler.spiders.crawler_spider import DumbCrawlerSpider

    # Test 1: Valid modes
    valid_modes = ['single', 'list', 'crawl', 'sitemap']
    for mode in valid_modes:
        try:
            spider = DumbCrawlerSpider(
                mode=mode,
                start_urls='https://example.com/'
            )
            print(f"✓ Mode '{mode}' accepted")
        except ValueError:
            print(f"✗ Mode '{mode}' rejected (should be valid)")
            return False

    # Test 2: Invalid mode
    try:
        spider = DumbCrawlerSpider(
            mode='invalid_mode',
            start_urls='https://example.com/'
        )
        print("✗ Invalid mode accepted (should be rejected)")
        return False
    except ValueError:
        print("✓ Invalid mode rejected correctly")

    print("\n✓ All validation tests passed\n")
    return True


def test_scope_filtering():
    """Test that scope filtering works with sitemap mode."""
    print("=" * 60)
    print("TEST 6: Scope Filtering")
    print("=" * 60)

    from dumbcrawler.spiders.crawler_spider import DumbCrawlerSpider

    # Create spider with domain scope
    spider = DumbCrawlerSpider(
        mode='sitemap',
        start_urls='https://example.com/sitemap.xml',
        scope='domain'
    )

    # Test various URLs
    test_cases = [
        ('https://example.com/page', True, 'Same domain'),
        ('https://www.example.com/page', True, 'WWW subdomain'),
        ('https://subdomain.example.com/page', True, 'Subdomain (domain scope)'),
        ('https://other.com/page', False, 'Different domain'),
    ]

    for url, should_match, description in test_cases:
        result = spider._is_url_in_scope(url)
        if result == should_match:
            print(f"✓ {description}: {url} → {result}")
        else:
            print(f"✗ {description}: {url} → {result} (expected {should_match})")
            return False

    print("\n✓ All scope filtering tests passed\n")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("SITEMAP MODE TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("Import Test", test_spider_imports),
        ("Initialization Test", test_sitemap_mode_initialization),
        ("Methods Test", test_sitemap_methods_exist),
        ("XML Parsing Test", test_sitemap_xml_parsing),
        ("Mode Validation Test", test_mode_validation),
        ("Scope Filtering Test", test_scope_filtering),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"FAILED: {test_name}\n")
        except Exception as e:
            failed += 1
            print(f"ERROR in {test_name}: {e}\n")

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED! Sitemap mode is ready.")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED. Fix before deployment.")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
