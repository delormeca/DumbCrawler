# dumbcrawler_tests.command.md

> **Manual test commands for dumbcrawler**  
> Execute each test, then validate output with the provided checks.

---

## ⚙️ Assumptions

| Item | Value |
|------|-------|
| **Working directory** | `dumbcrawler/` (project root) |
| **Entry point** | `python run_crawl.py` |
| **Output location** | `scrapy_app/output_{crawl_job_id}.jsonl` |
| **Python environment** | Virtual env activated (`.venv`) |

### Crawl Modes

| Mode | Behavior |
|------|----------|
| `single` | One URL, no link discovery |
| `list` | Multiple URLs, no link discovery |
| `crawl` | Auto-discovery up to `--max-depth` |

### JS Modes

| Mode | Behavior |
|------|----------|
| `off` | No Playwright — plain HTTP only |
| `auto` | Playwright on depth 0 only *(recommended)* |
| `full` | Playwright for ALL requests |

### Scoping Flags

| Flag | Effect |
|------|--------|
| `--restrict-to-subdomain true` | Stay on exact subdomain (e.g., `blog.example.com` only) |
| `--restrict-to-subdomain false` | Allow entire domain (e.g., `*.example.com`) |
| `--restrict-to-path true` | Stay within starting path prefix (e.g., `/blog/*`) |
| `--restrict-to-path false` | Allow any path on allowed domain(s) |

---

## 🧹 Pre-Test Cleanup

```bash
# Remove old output files before testing
rm -f scrapy_app/output_*.jsonl
```

---

## 1️⃣ Subdomain-Only Crawl

**Target:** `https://lasallecollege.lcieducation.com/`  
**Goal:** Crawl ONLY this subdomain — reject other `*.lcieducation.com` subdomains.

### 1A. Shallow crawl (depth 2), JS auto, subdomain-only

```bash
python run_crawl.py \
  --client-id 1 \
  --crawl-job-id lasalle_subdomain_d2 \
  --mode crawl \
  --start-urls "https://lasallecollege.lcieducation.com/" \
  --max-depth 2 \
  --js-mode auto \
  --restrict-to-subdomain true \
  --restrict-to-path false
```

**✅ Expected:**
- All URLs in output have `lasallecollege.lcieducation.com` as host
- No URLs from `www.lcieducation.com`, `inter.lcieducation.com`, etc.
- Depth 0 uses Playwright; depths 1-2 use plain HTTP

**🔍 Validate:**
```bash
# Count URLs and check hosts
cat scrapy_app/output_lasalle_subdomain_d2.jsonl | python3 -c "
import json, sys
from urllib.parse import urlparse
from collections import Counter

hosts = Counter()
depths = Counter()
for line in sys.stdin:
    item = json.loads(line)
    host = urlparse(item['url']).netloc
    hosts[host] += 1
    depths[item['depth']] += 1

print('=== HOST DISTRIBUTION ===')
for host, count in hosts.most_common():
    status = '✅' if host == 'lasallecollege.lcieducation.com' else '❌ VIOLATION'
    print(f'  {status} {host}: {count}')

print('\n=== DEPTH DISTRIBUTION ===')
for depth, count in sorted(depths.items()):
    print(f'  Depth {depth}: {count} pages')
"
```

### 1B. Deeper crawl (depth 4), JS off, subdomain-only

```bash
python run_crawl.py \
  --client-id 1 \
  --crawl-job-id lasalle_subdomain_d4 \
  --mode crawl \
  --start-urls "https://lasallecollege.lcieducation.com/" \
  --max-depth 4 \
  --js-mode off \
  --restrict-to-subdomain true \
  --restrict-to-path false
```

**✅ Expected:**
- More pages discovered (depth 3-4)
- Still restricted to `lasallecollege.lcieducation.com`
- Faster execution (no Playwright overhead)

---

## 2️⃣ Whole-Domain Crawl

**Target:** `https://lasallecollege.lcieducation.com/`  
**Goal:** Crawl ANY subdomain of `lcieducation.com`.

### 2A. Domain-wide crawl (depth 2)

```bash
python run_crawl.py \
  --client-id 2 \
  --crawl-job-id lci_wholedomain_d2 \
  --mode crawl \
  --start-urls "https://lasallecollege.lcieducation.com/" \
  --max-depth 2 \
  --js-mode auto \
  --restrict-to-subdomain false \
  --restrict-to-path false
```

**✅ Expected:**
- URLs from multiple subdomains: `lasallecollege.`, `www.`, `inter.`, etc.
- All hosts end with `lcieducation.com`
- No external domains (e.g., `facebook.com`, `linkedin.com`)

**🔍 Validate:**
```bash
cat scrapy_app/output_lci_wholedomain_d2.jsonl | python3 -c "
import json, sys
from urllib.parse import urlparse
from collections import Counter

hosts = Counter()
for line in sys.stdin:
    item = json.loads(line)
    host = urlparse(item['url']).netloc
    hosts[host] += 1

print('=== SUBDOMAINS DISCOVERED ===')
for host, count in hosts.most_common(20):
    is_lci = host.endswith('lcieducation.com')
    status = '✅' if is_lci else '❌ EXTERNAL'
    print(f'  {status} {host}: {count}')
"
```

---

## 3️⃣ Subfolder-Only Crawl

**Target:** `https://docs.python.org/3/library/`  
**Goal:** Crawl ONLY URLs under `/3/library/` path.

### 3A. Path-restricted crawl (depth 2)

```bash
python run_crawl.py \
  --client-id 3 \
  --crawl-job-id python_library_d2 \
  --mode crawl \
  --start-urls "https://docs.python.org/3/library/" \
  --max-depth 2 \
  --js-mode off \
  --restrict-to-subdomain true \
  --restrict-to-path true
```

**✅ Expected:**
- All URLs start with `https://docs.python.org/3/library/`
- No URLs like `/3/tutorial/`, `/3/reference/`, `/2.7/`

**🔍 Validate:**
```bash
cat scrapy_app/output_python_library_d2.jsonl | python3 -c "
import json, sys
from urllib.parse import urlparse

valid = 0
invalid = 0
invalid_urls = []

for line in sys.stdin:
    item = json.loads(line)
    path = urlparse(item['url']).path
    if path.startswith('/3/library'):
        valid += 1
    else:
        invalid += 1
        invalid_urls.append(item['url'])

print(f'✅ Valid (under /3/library/): {valid}')
print(f'❌ Invalid (outside path): {invalid}')
if invalid_urls:
    print('\nViolating URLs:')
    for url in invalid_urls[:10]:
        print(f'  - {url}')
"
```

### 3B. Combined: subdomain + path restriction

```bash
python run_crawl.py \
  --client-id 3 \
  --crawl-job-id python_library_strict \
  --mode crawl \
  --start-urls "https://docs.python.org/3/library/json.html" \
  --max-depth 3 \
  --js-mode off \
  --restrict-to-subdomain true \
  --restrict-to-path true
```

**✅ Expected:**
- Strictest scope: same subdomain AND same path prefix
- Only `docs.python.org/3/library/*` URLs

---

## 4️⃣ Single URL Mode

**Goal:** Fetch exactly ONE page, no link discovery.

### 4A. Single page, JS off

```bash
python run_crawl.py \
  --client-id 4 \
  --crawl-job-id single_httpbin \
  --mode single \
  --start-urls "https://httpbin.org/html" \
  --js-mode off
```

**✅ Expected:**
- Exactly 1 line in output
- `depth: 0`
- `referrer_url: null`

**🔍 Validate:**
```bash
wc -l < scrapy_app/output_single_httpbin.jsonl
# Expected: 1

cat scrapy_app/output_single_httpbin.jsonl | python3 -m json.tool | head -20
```

### 4B. Single JS-heavy page, JS full

```bash
python run_crawl.py \
  --client-id 4 \
  --crawl-job-id single_js_quotes \
  --mode single \
  --start-urls "https://quotes.toscrape.com/js/" \
  --js-mode full
```

**✅ Expected:**
- `raw_html` contains rendered quotes (e.g., "Albert Einstein")
- Not just empty JS skeleton

**🔍 Validate:**
```bash
cat scrapy_app/output_single_js_quotes.jsonl | python3 -c "
import json, sys
item = json.loads(sys.stdin.read())
html = item.get('raw_html', '')

if 'Albert Einstein' in html or 'class=\"quote\"' in html:
    print('✅ JS content rendered successfully')
    print(f'   HTML length: {len(html):,} chars')
else:
    print('❌ JS content NOT rendered')
    print(f'   HTML preview: {html[:300]}...')
"
```

---

## 5️⃣ List Mode (Multiple URLs)

**Goal:** Fetch multiple specific URLs, no discovery.

### 5A. Three URLs, JS off

```bash
python run_crawl.py \
  --client-id 5 \
  --crawl-job-id list_httpbin \
  --mode list \
  --start-urls "https://httpbin.org/html,https://httpbin.org/robots.txt,https://httpbin.org/ip" \
  --js-mode off
```

**✅ Expected:**
- Exactly 3 lines in output
- All `depth: 0`
- No additional discovered URLs

**🔍 Validate:**
```bash
cat scrapy_app/output_list_httpbin.jsonl | python3 -c "
import json, sys

urls = []
for line in sys.stdin:
    item = json.loads(line)
    urls.append(item['url'])
    
print(f'Total URLs crawled: {len(urls)}')
for url in urls:
    print(f'  ✅ {url}')
"
```

### 5B. Mixed domains in list mode

```bash
python run_crawl.py \
  --client-id 5 \
  --crawl-job-id list_mixed \
  --mode list \
  --start-urls "https://example.com,https://httpbin.org/html,https://jsonplaceholder.typicode.com/posts/1" \
  --js-mode off
```

**✅ Expected:**
- 3 URLs from 3 different domains
- All fetched regardless of scoping flags (list mode ignores scoping)

---

## 6️⃣ JS Mode Comparison

**Goal:** Compare output between JS modes on same target.

### 6A. JS-heavy site with js_mode=off

```bash
python run_crawl.py \
  --client-id 6 \
  --crawl-job-id js_compare_off \
  --mode single \
  --start-urls "https://quotes.toscrape.com/js/" \
  --js-mode off
```

### 6B. JS-heavy site with js_mode=full

```bash
python run_crawl.py \
  --client-id 6 \
  --crawl-job-id js_compare_full \
  --mode single \
  --start-urls "https://quotes.toscrape.com/js/" \
  --js-mode full
```

**🔍 Compare:**
```bash
echo "=== JS OFF ==="
cat scrapy_app/output_js_compare_off.jsonl | python3 -c "
import json, sys
item = json.loads(sys.stdin.read())
html = item['raw_html']
has_quotes = 'Albert Einstein' in html
print(f'HTML length: {len(html):,} chars')
print(f'Contains quotes: {has_quotes}')
"

echo ""
echo "=== JS FULL ==="
cat scrapy_app/output_js_compare_full.jsonl | python3 -c "
import json, sys
item = json.loads(sys.stdin.read())
html = item['raw_html']
has_quotes = 'Albert Einstein' in html
print(f'HTML length: {len(html):,} chars')
print(f'Contains quotes: {has_quotes}')
"
```

**✅ Expected:**
- `js_mode=off`: Shorter HTML, no quote content
- `js_mode=full`: Longer HTML, contains rendered quotes

---

## 7️⃣ Depth Limit Verification

**Goal:** Confirm `--max-depth` is respected.

### 7A. Depth 0 (start URL only)

```bash
python run_crawl.py \
  --client-id 7 \
  --crawl-job-id depth_test_0 \
  --mode crawl \
  --start-urls "https://httpbin.org/links/5/0" \
  --max-depth 0 \
  --js-mode off \
  --restrict-to-subdomain true
```

**✅ Expected:** Exactly 1 URL (no link following at depth 0)

### 7B. Depth 1

```bash
python run_crawl.py \
  --client-id 7 \
  --crawl-job-id depth_test_1 \
  --mode crawl \
  --start-urls "https://httpbin.org/links/5/0" \
  --max-depth 1 \
  --js-mode off \
  --restrict-to-subdomain true
```

**✅ Expected:** ~6 URLs (1 start + 5 linked pages)

### 7C. Depth 2

```bash
python run_crawl.py \
  --client-id 7 \
  --crawl-job-id depth_test_2 \
  --mode crawl \
  --start-urls "https://httpbin.org/links/5/0" \
  --max-depth 2 \
  --js-mode off \
  --restrict-to-subdomain true
```

**✅ Expected:** More URLs discovered at depth 2

**🔍 Compare depths:**
```bash
for job in depth_test_0 depth_test_1 depth_test_2; do
  count=$(wc -l < "scrapy_app/output_${job}.jsonl" 2>/dev/null || echo "0")
  echo "${job}: ${count} URLs"
done
```

---

## 8️⃣ Output Structure Validation

**Goal:** Verify all required fields exist in output.

### 8A. Field completeness check

```bash
# Run any crawl first, then:
cat scrapy_app/output_*.jsonl | head -5 | python3 -c "
import json, sys

REQUIRED_FIELDS = [
    'client_id',
    'crawl_job_id', 
    'url',
    'status_code',
    'depth',
    'referrer_url',
    'raw_html',
    'response_headers',
    'meta_title',
    'h1',
    'meta_description'
]

for i, line in enumerate(sys.stdin, 1):
    item = json.loads(line)
    missing = [f for f in REQUIRED_FIELDS if f not in item]
    
    if missing:
        print(f'❌ Item {i}: Missing fields: {missing}')
    else:
        print(f'✅ Item {i}: All fields present')
        
    # Show sample values
    print(f'   url: {item.get(\"url\", \"N/A\")[:60]}...')
    print(f'   status_code: {item.get(\"status_code\")}')
    print(f'   depth: {item.get(\"depth\")}')
    print(f'   meta_title: {str(item.get(\"meta_title\", \"\"))[:50]}...')
    print()
"
```

### 8B. JSON validity check

```bash
# Verify all lines are valid JSON
cat scrapy_app/output_*.jsonl | python3 -c "
import json, sys

valid = 0
invalid = 0

for i, line in enumerate(sys.stdin, 1):
    try:
        json.loads(line)
        valid += 1
    except json.JSONDecodeError as e:
        invalid += 1
        print(f'❌ Line {i}: Invalid JSON - {e}')

print(f'\n✅ Valid JSON lines: {valid}')
print(f'❌ Invalid JSON lines: {invalid}')
"
```

---

## 9️⃣ Error Handling Tests

**Goal:** Verify graceful handling of errors.

### 9A. Non-existent URL

```bash
python run_crawl.py \
  --client-id 9 \
  --crawl-job-id error_404 \
  --mode single \
  --start-urls "https://httpbin.org/status/404" \
  --js-mode off
```

**✅ Expected:** 
- Output contains item with `status_code: 404`
- No crash

### 9B. Connection timeout (slow endpoint)

```bash
python run_crawl.py \
  --client-id 9 \
  --crawl-job-id error_timeout \
  --mode single \
  --start-urls "https://httpbin.org/delay/60" \
  --js-mode off
```

**✅ Expected:**
- Request times out (DOWNLOAD_TIMEOUT = 30)
- Error logged, no crash

### 9C. Invalid URL handling

```bash
python run_crawl.py \
  --client-id 9 \
  --crawl-job-id error_invalid \
  --mode list \
  --start-urls "https://httpbin.org/html,not-a-valid-url,https://example.com" \
  --js-mode off
```

**✅ Expected:**
- Valid URLs crawled successfully
- Invalid URL logged as error or skipped

---

## 🔟 Performance / Load Tests

**Goal:** Test behavior under moderate load.

### 10A. Many pages (depth 3)

```bash
time python run_crawl.py \
  --client-id 10 \
  --crawl-job-id perf_depth3 \
  --mode crawl \
  --start-urls "https://docs.python.org/3/" \
  --max-depth 3 \
  --js-mode off \
  --restrict-to-subdomain true \
  --restrict-to-path false
```

**🔍 Stats:**
```bash
echo "=== CRAWL STATISTICS ==="
cat scrapy_app/output_perf_depth3.jsonl | python3 -c "
import json, sys
from collections import Counter

depths = Counter()
statuses = Counter()
total = 0

for line in sys.stdin:
    item = json.loads(line)
    depths[item['depth']] += 1
    statuses[item['status_code']] += 1
    total += 1

print(f'Total pages: {total}')
print(f'\nBy depth:')
for d, c in sorted(depths.items()):
    print(f'  Depth {d}: {c}')
print(f'\nBy status:')
for s, c in sorted(statuses.items()):
    print(f'  {s}: {c}')
"
```

---

## 📋 Quick Reference: All Test Jobs

| Job ID | Mode | JS | Subdomain | Path | Purpose |
|--------|------|-----|-----------|------|---------|
| `lasalle_subdomain_d2` | crawl | auto | ✅ | ❌ | Subdomain restriction |
| `lasalle_subdomain_d4` | crawl | off | ✅ | ❌ | Deep subdomain crawl |
| `lci_wholedomain_d2` | crawl | auto | ❌ | ❌ | Whole domain |
| `python_library_d2` | crawl | off | ✅ | ✅ | Path restriction |
| `python_library_strict` | crawl | off | ✅ | ✅ | Strict scoping |
| `single_httpbin` | single | off | - | - | Single URL basic |
| `single_js_quotes` | single | full | - | - | Single URL + JS |
| `list_httpbin` | list | off | - | - | Multi-URL list |
| `list_mixed` | list | off | - | - | Mixed domains |
| `js_compare_off` | single | off | - | - | JS comparison |
| `js_compare_full` | single | full | - | - | JS comparison |
| `depth_test_0` | crawl | off | ✅ | ❌ | Depth limit |
| `depth_test_1` | crawl | off | ✅ | ❌ | Depth limit |
| `depth_test_2` | crawl | off | ✅ | ❌ | Depth limit |
| `error_404` | single | off | - | - | Error handling |
| `error_timeout` | single | off | - | - | Timeout handling |
| `perf_depth3` | crawl | off | ✅ | ❌ | Performance |

---

## 🧹 Post-Test Cleanup

```bash
# Remove all test output files
rm -f scrapy_app/output_*.jsonl

# Remove Scrapy cache (optional)
rm -rf scrapy_app/.scrapy/

# Remove log files (if any)
rm -f scrapy_app/*.log
```

---

## ⚠️ Troubleshooting

### "No module named 'scrapy'"
```bash
source .venv/bin/activate
pip install scrapy scrapy-playwright playwright beautifulsoup4 lxml
```

### "Playwright browser not found"
```bash
playwright install chromium
```

### "Twisted reactor already installed"
Restart Python interpreter or use a fresh terminal.

### Empty output file
- Check spider logs for errors
- Verify URL is accessible: `curl -I <url>`
- Try with `--js-mode off` first

### Scoping not working
- Verify flags: `--restrict-to-subdomain true` (not just `--restrict-to-subdomain`)
- Check logs for "Rejected" messages
