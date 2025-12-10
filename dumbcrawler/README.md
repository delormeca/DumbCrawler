# dumbcrawler

API-first Scrapy + Playwright crawler engine.

## Features
- No database, no dashboard — pure JSON output
- Three crawl modes: single, list, crawl (auto-discovery)
- JS rendering: off, auto, full
- Scope control: subdomain, domain, subfolder

## Quick Start
```bash
python run_crawl.py --client-id 123 --mode single --start-urls https://example.com
```

## Manual Test Commands

### Test 1: Single HTML-only URL (js_mode=off)
```bash
python run_crawl.py \
    --client-id test \
    --mode single \
    --start-urls https://httpbin.org/html \
    --js-mode off
```
**Expected**: Crawls exactly 1 URL, outputs 1 JSON line.

### Test 2: Single JS-heavy URL (js_mode=full)
```bash
python run_crawl.py \
    --client-id test \
    --mode single \
    --start-urls https://quotes.toscrape.com/js/ \
    --js-mode full
```
**Expected**: Crawls with Playwright, raw_html contains rendered content.

### Test 3: List Mode with Multiple URLs
```bash
python run_crawl.py \
    --client-id test \
    --mode list \
    --start-urls "https://httpbin.org/html,https://httpbin.org/robots.txt,https://httpbin.org/ip" \
    --js-mode off
```
**Expected**: Crawls exactly 3 URLs, outputs 3 JSON lines, no link following.

### Test 4: Crawl Mode with Depth (subdomain restricted)
```bash
python run_crawl.py \
    --client-id test \
    --mode crawl \
    --max-depth 1 \
    --start-urls https://httpbin.org/links/3/0 \
    --js-mode off \
    --restrict-to-subdomain
```
**Expected**: Crawls start URL + discovered links (depth 1), stays on same subdomain.

### Test 5: Crawl Mode with Path Restriction
```bash
python run_crawl.py \
    --client-id test \
    --mode crawl \
    --max-depth 2 \
    --start-urls https://docs.python.org/3/library/ \
    --js-mode off \
    --restrict-to-path
```
**Expected**: Only crawls URLs starting with `/3/library/`.

### Test 6: Verify Output JSON Structure
```bash
# After any crawl:
cat scrapy_app/output_*.jsonl | python -m json.tool | head -50

# Check required fields exist:
cat scrapy_app/output_*.jsonl | python -c "
import json, sys
for line in sys.stdin:
    item = json.loads(line)
    required = ['client_id', 'crawl_job_id', 'url', 'status_code', 'depth',
                'referrer_url', 'raw_html', 'response_headers',
                'meta_title', 'h1', 'meta_description']
    missing = [f for f in required if f not in item]
    if missing:
        print(f'MISSING: {missing}')
    else:
        print(f'OK: {item[\"url\"][:60]}...')
"
```

### Cleanup Test Files
```bash
rm -f scrapy_app/output_*.jsonl
```
