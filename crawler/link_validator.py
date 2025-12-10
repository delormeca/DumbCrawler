"""
Link Validator - Check internal links for 404s and 301 redirects.

Usage:
    from crawler.link_validator import validate_internal_links

    results = validate_internal_links(crawl_json_path, timeout=5)
    # or
    results = validate_links(list_of_urls, timeout=5)
"""

import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
import time


def validate_links(
    urls: List[str],
    timeout: int = 5,
    max_workers: int = 10,
    user_agent: str = "DumbCrawler LinkValidator/1.0"
) -> Dict[str, Any]:
    """
    Validate a list of URLs by making HEAD requests.

    Args:
        urls: List of URLs to validate
        timeout: Request timeout in seconds
        max_workers: Max concurrent requests
        user_agent: User agent string

    Returns:
        Dict with validation results
    """
    results = {
        "total": len(urls),
        "ok": [],           # 200 OK
        "redirects": [],    # 301, 302, 307, 308
        "broken": [],       # 404, 410, etc.
        "errors": [],       # Connection errors, timeouts
        "summary": {}
    }

    if not urls:
        return results

    headers = {"User-Agent": user_agent}

    def check_url(url: str) -> Dict:
        """Check single URL status."""
        try:
            # Use HEAD request (faster, less bandwidth)
            # allow_redirects=False to detect redirects
            response = requests.head(
                url,
                timeout=timeout,
                headers=headers,
                allow_redirects=False
            )

            status = response.status_code
            result = {
                "url": url,
                "status_code": status,
            }

            # If redirect, capture the target
            if status in (301, 302, 303, 307, 308):
                result["redirect_to"] = response.headers.get("Location", "")
                result["redirect_type"] = "permanent" if status == 301 else "temporary"

            return result

        except requests.exceptions.Timeout:
            return {"url": url, "status_code": None, "error": "timeout"}
        except requests.exceptions.ConnectionError as e:
            return {"url": url, "status_code": None, "error": f"connection_error: {str(e)[:100]}"}
        except requests.exceptions.RequestException as e:
            return {"url": url, "status_code": None, "error": str(e)[:100]}

    # Run concurrent requests
    print(f"Validating {len(urls)} URLs...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}

        for i, future in enumerate(as_completed(future_to_url)):
            result = future.result()
            status = result.get("status_code")

            if status is None:
                results["errors"].append(result)
            elif status == 200:
                results["ok"].append(result)
            elif status in (301, 302, 303, 307, 308):
                results["redirects"].append(result)
            elif status in (404, 410, 451):
                results["broken"].append(result)
            else:
                # Other status codes (403, 500, etc.)
                results["errors"].append(result)

            # Progress indicator
            if (i + 1) % 20 == 0 or i == len(urls) - 1:
                print(f"  Checked {i + 1}/{len(urls)} URLs...")

    elapsed = time.time() - start_time

    # Build summary
    results["summary"] = {
        "ok_count": len(results["ok"]),
        "redirect_count": len(results["redirects"]),
        "broken_count": len(results["broken"]),
        "error_count": len(results["errors"]),
        "elapsed_seconds": round(elapsed, 2),
        "ok_percent": round(len(results["ok"]) / len(urls) * 100, 1) if urls else 0,
        "redirect_percent": round(len(results["redirects"]) / len(urls) * 100, 1) if urls else 0,
        "broken_percent": round(len(results["broken"]) / len(urls) * 100, 1) if urls else 0,
    }

    return results


def validate_internal_links(
    crawl_json_path: str,
    timeout: int = 5,
    max_workers: int = 10
) -> Dict[str, Any]:
    """
    Validate internal links from a crawl output JSON file.

    Args:
        crawl_json_path: Path to the crawl output JSON file
        timeout: Request timeout in seconds
        max_workers: Max concurrent requests

    Returns:
        Dict with validation results including the source URL
    """
    with open(crawl_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    source_url = data.get("url", "")
    internal_links = data.get("internal_links", [])

    # Extract unique URLs
    urls = list(set(link.get("url") for link in internal_links if link.get("url")))

    print(f"Source: {source_url}")
    print(f"Found {len(internal_links)} internal links ({len(urls)} unique)")

    results = validate_links(urls, timeout=timeout, max_workers=max_workers)
    results["source_url"] = source_url

    return results


def print_validation_report(results: Dict[str, Any]):
    """Print a formatted validation report."""
    summary = results.get("summary", {})

    print("\n" + "=" * 60)
    print(" LINK VALIDATION REPORT")
    print("=" * 60)

    if results.get("source_url"):
        print(f"\nSource: {results['source_url']}")

    print(f"\nTotal Links Checked: {results.get('total', 0)}")
    print(f"Time Elapsed: {summary.get('elapsed_seconds', 0)}s")

    print("\n--- SUMMARY ---")
    print(f"  OK (200):      {summary.get('ok_count', 0):4d} ({summary.get('ok_percent', 0):.1f}%)")
    print(f"  Redirects:     {summary.get('redirect_count', 0):4d} ({summary.get('redirect_percent', 0):.1f}%)")
    print(f"  Broken (404):  {summary.get('broken_count', 0):4d} ({summary.get('broken_percent', 0):.1f}%)")
    print(f"  Errors:        {summary.get('error_count', 0):4d}")

    # Show broken links
    if results.get("broken"):
        print("\n--- BROKEN LINKS (404) ---")
        for link in results["broken"][:20]:
            print(f"  {link['status_code']}: {link['url']}")

    # Show redirects
    if results.get("redirects"):
        print("\n--- REDIRECTS (301/302) ---")
        for link in results["redirects"][:20]:
            rtype = link.get("redirect_type", "")
            target = link.get("redirect_to", "")[:60]
            print(f"  {link['status_code']} ({rtype}): {link['url'][:50]}")
            print(f"       -> {target}")

    # Show errors
    if results.get("errors"):
        print("\n--- ERRORS ---")
        for link in results["errors"][:10]:
            print(f"  {link.get('error', 'unknown')}: {link['url'][:60]}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate internal links from crawl output")
    parser.add_argument("json_file", help="Path to crawl output JSON file")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout (default: 5s)")
    parser.add_argument("--workers", type=int, default=10, help="Max concurrent requests (default: 10)")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    results = validate_internal_links(
        args.json_file,
        timeout=args.timeout,
        max_workers=args.workers
    )

    print_validation_report(results)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")
