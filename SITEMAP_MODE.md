# Sitemap Crawling Mode

## Overview

DumbCrawler now supports a robust **sitemap mode** that crawls URLs discovered from XML sitemaps. This mode is highly resilient and handles all sitemap formats and edge cases.

## Features

### Core Capabilities
- ✅ **Regular Sitemaps** - Standard `<urlset>` sitemaps
- ✅ **Sitemap Index Files** - Recursive parsing of `<sitemapindex>` files
- ✅ **Gzipped Sitemaps** - Automatic decompression of `.xml.gz` files
- ✅ **Robots.txt Discovery** - Extract sitemap URLs from `robots.txt`
- ✅ **Alternate Language Links** - Optional support for `hreflang` alternate URLs
- ✅ **Malformed XML Recovery** - Graceful handling of invalid XML
- ✅ **Scope Filtering** - Apply domain/subdomain/subfolder scope rules
- ✅ **Deduplication** - Automatic URL deduplication
- ✅ **Size Limits** - Protection against oversized sitemaps (10MB default)

### Sitemap Metadata Support
- `<loc>` - URL location (required) ✅
- `<lastmod>` - Last modification date (logged)
- `<priority>` - URL priority (logged)
- `<changefreq>` - Change frequency (logged)
- `<xhtml:link rel="alternate">` - Alternate language URLs (optional)

## Usage

### Basic Sitemap Crawl

```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml"
```

### Multiple Sitemaps

```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml,https://example.com/sitemap-news.xml"
```

### Sitemap Index (Auto-Recursive)

```bash
# Automatically follows nested sitemaps
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap_index.xml"
```

### Robots.txt Discovery

```bash
# Extracts sitemap URLs from robots.txt
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/robots.txt"
```

### With Alternate Language Links

```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -a sitemap_alternate_links=true
```

### With Scope Filtering

```bash
# Only crawl blog section
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -a scope=subfolder \
  -a start_urls="https://example.com/blog/"
```

**Note:** When using `scope=subfolder`, the `start_urls` should also include the base URL for scope checking.

### With JavaScript Rendering

```bash
# Render JS for all sitemap URLs
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -a js_mode=full
```

## Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `mode` | `sitemap` | required | Enable sitemap mode |
| `start_urls` | Comma-separated URLs | required | Sitemap URLs to fetch |
| `sitemap_alternate_links` | `true`/`false` | `false` | Include alternate language links |
| `scope` | `subdomain`/`domain`/`subfolder`/`subdomain+subfolder` | `domain` | URL filtering scope |
| `js_mode` | `off`/`auto`/`full` | `off` | JavaScript rendering mode |
| `max_depth` | integer | `2` | Not used in sitemap mode |

## How It Works

### 1. Sitemap Fetching
```
start_requests()
  → Request sitemap URL
  → _parse_sitemap()
```

### 2. Sitemap Type Detection
```
_get_sitemap_body()
  → Detect gzip compression
  → Extract XML body
  → Validate format
```

### 3. Sitemap Index Handling
```
_parse_sitemap()
  → Detect <sitemapindex>
  → Recursively fetch nested sitemaps
  → Process each <sitemap><loc>
```

### 4. URL Extraction & Filtering
```
_parse_sitemap()
  → Extract <url><loc> entries
  → Apply scope filtering
  → Check for duplicates
  → Yield crawl requests
```

### 5. Page Crawling
```
parse()
  → Extract page data
  → Save to output
  → NO link following (sitemap mode only crawls listed URLs)
```

## Edge Cases Handled

### Compression
- ✅ Gzipped sitemaps (`.xml.gz`)
- ✅ Auto-decompressed by middleware (Content-Encoding: gzip)
- ✅ Mixed compressed/uncompressed sitemap indexes

### XML Issues
- ✅ Malformed XML (recovery parser)
- ✅ Missing namespaces
- ✅ Invalid characters
- ✅ Large files (10MB limit)

### URL Issues
- ✅ Relative URLs (converted to absolute)
- ✅ Duplicate URLs (deduplicated)
- ✅ Out-of-scope URLs (filtered)
- ✅ Invalid URLs (logged and skipped)

### Network Issues
- ✅ Timeout errors (handled by errback)
- ✅ 404/500 errors (logged)
- ✅ Connection failures (logged)

### Sitemap Formats
- ✅ Standard sitemap namespace
- ✅ Google sitemap extensions
- ✅ News sitemaps
- ✅ Image sitemaps
- ✅ Video sitemaps

## Logging Output

### Sitemap Index Example
```
2024-01-15 10:30:00 [dumbcrawler] INFO: Starting sitemap mode with 1 sitemap URL(s)
2024-01-15 10:30:00 [dumbcrawler] INFO: Fetching sitemap: https://example.com/sitemap_index.xml
2024-01-15 10:30:01 [dumbcrawler] INFO: Processing sitemap index: https://example.com/sitemap_index.xml
2024-01-15 10:30:01 [dumbcrawler] INFO: Following nested sitemap [1]: https://example.com/sitemap-blog.xml
2024-01-15 10:30:01 [dumbcrawler] INFO: Following nested sitemap [2]: https://example.com/sitemap-products.xml
2024-01-15 10:30:01 [dumbcrawler] INFO: Sitemap index contains 2 sitemaps
```

### URL Extraction Example
```
2024-01-15 10:30:02 [dumbcrawler] INFO: Processing sitemap urlset: https://example.com/sitemap-blog.xml
2024-01-15 10:30:02 [dumbcrawler] INFO: Sitemap yielded 150 URLs (skipped: 5 out-of-scope, 3 duplicates)
```

## Advanced: Custom Filtering

You can extend the spider to add custom sitemap filtering logic:

```python
def _filter_sitemap_entries(self, sitemap):
    """Filter sitemap entries by lastmod date."""
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=30)

    for entry in sitemap:
        # Only crawl URLs modified in last 30 days
        lastmod = entry.get('lastmod')
        if lastmod:
            try:
                mod_date = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
                if mod_date < cutoff_date:
                    continue  # Skip old URLs
            except:
                pass  # Include URLs with invalid dates

        yield entry
```

## Performance Tips

### 1. Limit Crawl Size
```bash
# Stop after 1000 pages
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -s CLOSESPIDER_PAGECOUNT=1000
```

### 2. Increase Concurrency
```bash
# Crawl faster with more concurrent requests
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -s CONCURRENT_REQUESTS=32
```

### 3. Disable JS for Speed
```bash
# Skip JavaScript rendering for static sites
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -a js_mode=off
```

## Troubleshooting

### No URLs Found
```
# Check sitemap format
curl https://example.com/sitemap.xml | head -20

# Expected: <urlset> or <sitemapindex>
```

### Out of Scope Errors
```
# Verify scope setting matches URLs
# For https://example.com/blog/post1:
-a scope=subfolder
-a start_urls="https://example.com/blog/"
```

### Gzip Errors
```
# Test decompression
curl -s https://example.com/sitemap.xml.gz | gunzip | head -20
```

### Large Sitemap Timeout
```
# Increase timeout
-s DOWNLOAD_TIMEOUT=120
```

## API Integration

When calling from the API:

```python
{
    "mode": "sitemap",
    "start_urls": "https://example.com/sitemap.xml",
    "sitemap_alternate_links": false,
    "scope": "domain",
    "js_mode": "off"
}
```

## Examples

### E-commerce Site
```bash
# Crawl product pages from sitemap
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://shop.example.com/product-sitemap.xml" \
  -a scope=subfolder \
  -a js_mode=auto
```

### News Site
```bash
# Crawl news articles with alternate languages
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://news.example.com/sitemap-news.xml" \
  -a sitemap_alternate_links=true
```

### Multi-domain Company
```bash
# Crawl from robots.txt, strict subdomain scope
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://www.example.com/robots.txt" \
  -a scope=subdomain
```

## Benefits Over Crawl Mode

| Feature | Crawl Mode | Sitemap Mode |
|---------|-----------|--------------|
| URL Discovery | Link following | Sitemap parsing |
| Completeness | May miss pages | Crawls all sitemap URLs |
| Efficiency | Explores site | Direct URL access |
| Duplicates | More likely | Pre-filtered |
| Depth Control | Required | Not needed |
| Pagination Issues | Common | None |
| Low-quality Pages | Often included | Publisher-curated |

## Limitations

- Does not follow links on pages (by design)
- Does not discover URLs not in sitemap
- Relies on sitemap being up-to-date
- Limited by sitemap quality and completeness

For comprehensive crawling, consider combining sitemap mode with crawl mode:
1. Use sitemap mode for bulk crawling
2. Use crawl mode for specific sections needing link discovery

---

**Questions?** Check the main DumbCrawler documentation or submit an issue.
