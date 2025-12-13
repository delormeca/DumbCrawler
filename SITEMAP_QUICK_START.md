# Sitemap Mode - Quick Start Guide

## Basic Usage

```bash
scrapy crawl dumbcrawler -a mode=sitemap -a start_urls="https://example.com/sitemap.xml"
```

## Common Scenarios

### 1. Basic Sitemap Crawl
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml"
```

### 2. Sitemap Index (Auto-Recursive)
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap_index.xml"
```

### 3. Robots.txt Discovery
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/robots.txt"
```

### 4. Multiple Sitemaps
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap1.xml,https://example.com/sitemap2.xml"
```

### 5. With JavaScript Rendering
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -a js_mode=full
```

### 6. Limit to Subfolder
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/blog/,https://example.com/sitemap.xml" \
  -a scope=subfolder
```

### 7. Include Alternate Languages
```bash
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://example.com/sitemap.xml" \
  -a sitemap_alternate_links=true
```

## Parameters

| Parameter | Required | Values | Default | Example |
|-----------|----------|--------|---------|---------|
| `mode` | Yes | `sitemap` | - | `sitemap` |
| `start_urls` | Yes | URL(s) | - | `https://example.com/sitemap.xml` |
| `sitemap_alternate_links` | No | `true`/`false` | `false` | `true` |
| `scope` | No | `domain`/`subdomain`/`subfolder` | `domain` | `subfolder` |
| `js_mode` | No | `off`/`auto`/`full` | `off` | `full` |

## What Gets Crawled?

✅ **Crawled:**
- URLs listed in `<url><loc>` tags
- Nested sitemaps in `<sitemap><loc>` tags
- Alternate language URLs (if enabled)

❌ **NOT Crawled:**
- Links discovered on pages
- URLs not in sitemap
- Out-of-scope URLs

## Supported Sitemap Formats

✅ Regular XML sitemaps (`.xml`)
✅ Gzipped sitemaps (`.xml.gz`)
✅ Sitemap index files
✅ Robots.txt sitemap references
✅ Google sitemap extensions (news, images, video)

## Output

Same as other modes:
- JSON/JSONL files
- Screenshots (if js_mode enabled)
- Performance metrics
- Status codes
- Metadata (title, description, h1)

## Troubleshooting

### No URLs crawled?
1. Check sitemap URL is accessible: `curl https://example.com/sitemap.xml`
2. Verify it's valid XML with `<urlset>` or `<sitemapindex>`
3. Check logs for "out-of-scope" or "duplicate" messages

### URLs skipped?
- Check `scope` parameter matches your URLs
- Look for "skipped: X out-of-scope" in logs

### Sitemap too large?
- Default limit: 10MB decompressed
- Split into multiple sitemaps or use sitemap index

## Next Steps

📖 **Full documentation:** See `SITEMAP_MODE.md`
🔧 **Implementation details:** See `SITEMAP_IMPLEMENTATION_SUMMARY.md`
❓ **Issues?** Check crawler logs for detailed error messages

---

**Quick Test:**
```bash
# Test with a public sitemap
scrapy crawl dumbcrawler \
  -a mode=sitemap \
  -a start_urls="https://www.sitemaps.org/sitemap.xml" \
  -s CLOSESPIDER_PAGECOUNT=5
```
