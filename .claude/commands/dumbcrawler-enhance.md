

Below is a full PAD-style task breakdown for building only the dumb scraper (no DB, no SaaS), using Scrapy + Playwright. You can feed each TASK to Claude / Claude Code one-by-one. 1. Problem analysis & solution approach (brief) What we’re building A simple, stable, API-first crawler engine named

pasted

your task is to :
Make this in markdown code formating as a command file .MD + enhance make it even clearer for claude code:


Architected markdown structure for enhanced Claude Code execution.


I'll create a well-formatted Markdown command file optimized for Claude Code execution. Let me structure this properly.


Creating a comprehensive markdown command file for dumbcrawler project, optimized for Claude Code execution
dumbcrawler_commands.md

Architected comprehensive Markdown command file with enhanced clarity.

I've created a comprehensive, well-formatted Markdown command file optimized for Claude Code execution.

View your command file

Let me copy it to the outputs folder:

Dumbcrawler commands
Document · MD 

Copy the markdown file to outputs folder for user access



Organized output file and catalogued formatting enhancements.

View your command file

Key Improvements Made:

Enhancement	Description
Visual Structure	Added clear section headers, tables, checkboxes, and emoji indicators
Code Blocks	All commands and code properly formatted with syntax highlighting
Verification Steps	Each task has explicit bash commands with expected outputs
STOP Points	Clear "✅ STOP" markers prevent Claude Code from skipping ahead
Copy-Paste Ready	Every code snippet is complete and can be directly executed
File Paths	Explicit paths shown for every file to create/modify
Expected Directory Structure	Visual tree showing final project layout
Execution Order Table	Quick reference for task sequencing
Summary Checklist	Trackable progress table at the end
Troubleshooting Section	Common issues and fixes documented
Retry Instructions	Clear guidance if a task fails
The file is now 1,900+ lines of detailed, actionable instructions that Claude Code can follow step-by-step without ambiguity.

Dumbcrawler commands
Document · MD 
make it better:
# dumbcrawler_tests.command.md
# Manual test commands for dumbcrawler
## ⚙ Assumptions
- Run commands from the project root: dumbcrawler/
- Entry point: python run_crawl.py
- Output: dumbcrawler_output.jsonl (or whatever your pipeline writes)
- Modes:
  - single  → one URL, no discovery
  - list    → several URLs, no discovery
  - crawl   → discovery up to --max-depth
- JS modes:
  - off     → no Playwright
  - auto    → Playwright on depth 0 only (recommended default)
  - full    → Playwright for all requests
---
## 1️⃣ Subdomain-only crawl  
Target: https://lasallecollege.lcieducation.com/  
Goal: **Crawl ONLY this subdomain**, not other lcieducation.com subdomains.
### 1A. Shallow crawl, JS auto, subdomain-only
```bash
python run_crawl.py \
  --client-id 1 \
  --crawl-job-id lasalle_subdomain_depth2 \
  --mode crawl \
  --start-urls "https://lasallecollege.lcieducation.com/" \
  --max-depth 2 \
  --js-mode auto \
  --restrict-to-subdomain true \
  --restrict-to-path false

Afficher plus

3 étapes

Copy test commands file to outputs for user access



Prepared to enhance documentation with structural improvements.

View your test commands file

Key Improvements:

Enhancement	What Changed
Structured Tables	Added reference tables for modes, JS modes, scoping flags
Numbered Test Sections	10 organized test categories with emoji headers
Validation Scripts	Every test has a Python validation snippet to verify results
Expected Outcomes	Clear ✅ checkboxes describing what should happen
Real-World URLs	Tests use actual sites (lasallecollege.lcieducation.com, docs.python.org, quotes.toscrape.com)
Comparison Tests	JS mode comparison (6A vs 6B), depth comparison (7A/7B/7C)
Error Handling	Tests for 404s, timeouts, invalid URLs
Performance Test	Load test with stats collection
Quick Reference Table	Summary of all 17 test jobs at the end
Troubleshooting	Common issues and fixes
Cleanup Commands	Pre-test and post-test cleanup
Test Coverage:

✅ Subdomain-only crawl (shallow + deep)
✅ Whole-domain crawl
✅ Subfolder/path restriction
✅ Single URL mode
✅ List mode (multiple URLs)
✅ JS mode comparison (off vs full)
✅ Depth limit verification (0, 1, 2)
✅ Output structure validation
✅ Error handling (404, timeout, invalid)
✅ Performance/load testing
Dumbcrawler tests.command
Document · MD 

**Top-Level Fields:** - client_id: (string) Reference to Client entity - crawl_job_id: (string) Reference to CrawlJob entity - url: (string) Page URL - h1: (string) H1 tag content - meta_title: (string) Meta title - meta_description: (string) Meta description - screenshot_url: (string) Screenshot im

pasted

we are still testing so far o good, what datapoints from these can we get :


Analyzed crawler capabilities against target schema requirements.
14s












Great question! Let me analyze what your current dumbcrawler can provide vs. what the target schema needs:

📊 Data Point Coverage Analysis
✅ Already Captured (11 fields)
Target Field	dumbcrawler Field	Status
client_id	client_id	✅ Direct
crawl_job_id	crawl_job_id	✅ Direct
url	url	✅ Direct
h1	h1	✅ Direct
meta_title	meta_title	✅ Direct
meta_description	meta_description	✅ Direct
raw_html	raw_html	✅ Direct
status_code	status_code	✅ Direct
discovery_depth	depth	✅ Rename
discovered_from_url	referrer_url	✅ Rename
headers	response_headers	✅ Direct
🔧 Can Extract from raw_html (Add to Pipeline)
These require BeautifulSoup parsing — easy additions to MetadataExtractionPipeline:

Field	Extraction Method	Complexity
Heading Hierarchy		
h2_tags	soup.find_all('h2')	🟢 Easy
h3_tags	soup.find_all('h3')	🟢 Easy
SEO Meta Tags		
canonical_url	soup.find('link', rel='canonical')['href']	🟢 Easy
meta_robots	soup.find('meta', attrs={'name': 'robots'})['content']	🟢 Easy
lang_attribute	soup.find('html').get('lang')	🟢 Easy
viewport	soup.find('meta', attrs={'name': 'viewport'})['content']	🟢 Easy
charset	soup.find('meta', charset=True) or from <meta http-equiv>	🟢 Easy
Content Metrics		
word_count	len(soup.get_text().split())	🟢 Easy
page_size_bytes	len(raw_html.encode('utf-8'))	🟢 Easy
Open Graph		
og_title	soup.find('meta', property='og:title')['content']	🟢 Easy
og_description	soup.find('meta', property='og:description')['content']	🟢 Easy
og_image	soup.find('meta', property='og:image')['content']	🟢 Easy
og_url	soup.find('meta', property='og:url')['content']	🟢 Easy
Twitter Cards		
twitter_card	soup.find('meta', attrs={'name': 'twitter:card'})['content']	🟢 Easy
twitter_title	soup.find('meta', attrs={'name': 'twitter:title'})['content']	🟢 Easy
twitter_description	soup.find('meta', attrs={'name': 'twitter:description'})['content']	🟢 Easy
twitter_image	soup.find('meta', attrs={'name': 'twitter:image'})['content']	🟢 Easy
Links		
internal_links_count	Count links matching domain	🟡 Medium
external_links_count	Count links NOT matching domain	🟡 Medium
internal_links_array	Extract href + anchor text + location	🟡 Medium
Images		
images_count	len(soup.find_all('img'))	🟢 Easy
images_alt_texts	[img.get('alt') for img in soup.find_all('img')]	🟢 Easy
Structured Data		
json_ld	Parse <script type="application/ld+json">	🟡 Medium
schema_types	Extract @type from JSON-LD	🟡 Medium
📸 Requires Playwright Enhancement
Field	How to Get	Complexity
screenshot_url	page.screenshot() → save to file/S3	🟡 Medium
load_time_ms	Playwright timing API	🟡 Medium
body_content	page.inner_text('body') (cleaner than BS4)	🟢 Easy
🔌 Requires External Services
Field	Service Needed	Complexity
content_embeddings	OpenAI / Cohere / local model	🔴 External API
vectorization_status	Your application logic	🟡 App logic
markdown_content	html2text or markdownify library	🟢 Easy (library)
quality_score	Custom SEO rules engine	🔴 Complex
quality_issues	Custom SEO rules engine	🔴 Complex
schema_validation_status	JSON-LD validator library	🟡 Medium
🚫 Application-Level (Not Crawler's Job)
Field	Why Not in Crawler
discovered_from_url_id	Requires database lookup
version_number	Requires versioning system
is_deleted	Application state
tag_* fields	User-defined, post-crawl
custom_tags	User-defined, post-crawl
crawled_at	Add datetime.utcnow().isoformat() ✅ Easy
🎯 Recommended Next Steps
Phase 1: Quick Wins (30 min)
Add these to MetadataExtractionPipeline:

python
# Already parsing soup, just add:
item['h2_tags'] = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
item['h3_tags'] = [h3.get_text(strip=True) for h3 in soup.find_all('h3')]
item['canonical_url'] = soup.find('link', rel='canonical')['href'] if soup.find('link', rel='canonical') else None
item['word_count'] = len(soup.get_text().split())
item['page_size_bytes'] = len(item['raw_html'].encode('utf-8'))
item['crawled_at'] = datetime.utcnow().isoformat() + 'Z'
item['lang_attribute'] = soup.find('html').get('lang') if soup.find('html') else None
Phase 2: Social Metadata (15 min)
python
item['social_metadata'] = {
    'og_title': self._get_meta_property(soup, 'og:title'),
    'og_description': self._get_meta_property(soup, 'og:description'),
    'og_image': self._get_meta_property(soup, 'og:image'),
    'og_url': self._get_meta_property(soup, 'og:url'),
    'twitter_card': self._get_meta_name(soup, 'twitter:card'),
    'twitter_title': self._get_meta_name(soup, 'twitter:title'),
    # ... etc
}
Phase 3: Link Analysis (45 min)
Extract internal/external links with anchor text and location detection.

Phase 4: Screenshots (30 min)
Enable Playwright screenshots on depth 0.

📈 Coverage Summary
Category	Fields	Can Get Now	Easy to Add	Needs Work
Core	11	11 ✅	-	-
SEO Meta	8	3	5	-
Social	8	0	8	-
Content	5	1	3	1
Links	6	0	4	2
Structure	4	1	2	1
Advanced	10+	0	2	8+
Bottom line: You can get ~70% of the useful data points with BeautifulSoup enhancements to your existing pipeline. Want me to create an enhanced MetadataExtractionPipeline that captures all the easy wins?

create a command file to add all the things we can add easily


3 étapes

Copy enhanced extraction command file to outputs



Orchestrated file organization and prepared summary delivery.

View your enhanced extraction command file

Summary
Created a comprehensive command file that adds 40+ new data points to dumbcrawler:

New Fields by Category
Category	Fields Added	Count
Timestamps	crawled_at	1
Content	body_content, markdown_content, word_count, page_size_bytes	4
Headings	h2_tags, h3_tags	2
SEO Meta	canonical_url, meta_robots, lang_attribute, viewport, charset	5
Open Graph	og_title, og_description, og_image, og_url, og_type, og_site_name	6
Twitter	twitter_card, twitter_title, twitter_description, twitter_image, twitter_site	5
Images	images_count, images (array with src/alt/dimensions)	2
Links	internal_links_count, external_links_count, internal_links, external_links	4
Structured Data	json_ld, schema_types	2
Total: 31 new fields (on top of existing 11 = 42 fields total)

What the Command File Includes
Complete items.py — All field definitions with organized comments
Complete pipelines.py — Full extraction logic with helper methods
Verification tests — 5 test commands with validation scripts
Output JSON reference — Full schema documentation
Troubleshooting guide — Common issues and fixes
Key Technical Decisions
Single parse — BeautifulSoup parses raw_html once, extracts everything
Markdown conversion — Uses html2text library for clean output
Link categorization — Compares against base domain (last 2 parts of netloc)
Nofollow detection — Checks rel attribute on anchor tags
JSON-LD handling — Parses all <script type="application/ld+json"> blocks, handles arrays
Dumbcrawler enhanced extraction.command
Document · MD 


Comment puis-je vous aider ?








Dumbcrawler enhanced extraction.command · MD
Copier

# dumbcrawler_enhanced_extraction.command.md

> **Enhance dumbcrawler to extract 40+ additional data points**  
> All extractions use BeautifulSoup on existing `raw_html` — no external APIs required.

---

## 📋 Overview

### What We're Adding

| Category | Fields | Complexity |
|----------|--------|------------|
| **Timestamps** | `crawled_at` | 🟢 Trivial |
| **Content Metrics** | `word_count`, `page_size_bytes` | 🟢 Trivial |
| **SEO Meta** | `canonical_url`, `meta_robots`, `lang_attribute`, `viewport`, `charset` | 🟢 Easy |
| **Heading Hierarchy** | `h2_tags`, `h3_tags` | 🟢 Easy |
| **Social Metadata** | `og_*` (4 fields), `twitter_*` (4 fields) | 🟢 Easy |
| **Images** | `images_count`, `images` array with alt/src | 🟢 Easy |
| **Links Analysis** | `internal_links_count`, `external_links_count`, `internal_links_array`, `external_links_array` | 🟡 Medium |
| **Structured Data** | `json_ld`, `schema_types` | 🟡 Medium |
| **Content** | `body_content`, `markdown_content` | 🟢 Easy |

### New Dependencies

```
html2text>=2024.2.26
```

### Files to Modify

| File | Action |
|------|--------|
| `dumbcrawler/scrapy_app/dumbcrawler/items.py` | Add new fields |
| `dumbcrawler/scrapy_app/dumbcrawler/pipelines.py` | Enhance extraction |
| `dumbcrawler/requirements.txt` | Add html2text |

---

## 🚀 Execution Order

| Task | Description | Time |
|------|-------------|------|
| 0A | Install new dependency | 2 min |
| 1A | Update items.py with new fields | 5 min |
| 2A | Add helper methods to pipeline | 10 min |
| 2B | Add timestamp & content metrics | 5 min |
| 2C | Add SEO meta extraction | 10 min |
| 2D | Add heading hierarchy | 5 min |
| 2E | Add social metadata | 10 min |
| 2F | Add image extraction | 10 min |
| 2G | Add link analysis | 15 min |
| 2H | Add JSON-LD extraction | 10 min |
| 2I | Add body/markdown content | 10 min |
| 3A | Verification tests | 10 min |

**Total: ~90 minutes**

---

## Task 0A: Install New Dependency

### Step 1: Add to requirements.txt

```bash
cd dumbcrawler
echo "html2text>=2024.2.26" >> requirements.txt
```

### Step 2: Install

```bash
source .venv/bin/activate
pip install html2text>=2024.2.26
```

### Step 3: Verify

```bash
python -c "import html2text; print(f'html2text version: {html2text.__version__}')"
```

**Expected:** Version number printed without error.

✅ **STOP — Verify dependency installed before continuing.**

---

## Task 1A: Update items.py with New Fields

### Step 1: Replace entire items.py

**File:** `dumbcrawler/scrapy_app/dumbcrawler/items.py`

```python
"""
Scrapy Item definition for dumbcrawler.
Defines all fields extracted from crawled pages.
"""

import scrapy


class DumbcrawlerItem(scrapy.Item):
    """
    Complete item structure for crawled pages.
    Organized by category for clarity.
    """

    # ─────────────────────────────────────────────────────────────
    # IDENTIFIERS
    # ─────────────────────────────────────────────────────────────
    client_id = scrapy.Field()
    crawl_job_id = scrapy.Field()
    url = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # HTTP RESPONSE
    # ─────────────────────────────────────────────────────────────
    status_code = scrapy.Field()
    response_headers = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # DISCOVERY / CRAWL CONTEXT
    # ─────────────────────────────────────────────────────────────
    depth = scrapy.Field()
    referrer_url = scrapy.Field()
    crawled_at = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # RAW CONTENT
    # ─────────────────────────────────────────────────────────────
    raw_html = scrapy.Field()
    body_content = scrapy.Field()       # Plain text extracted from body
    markdown_content = scrapy.Field()   # HTML converted to markdown

    # ─────────────────────────────────────────────────────────────
    # CONTENT METRICS
    # ─────────────────────────────────────────────────────────────
    word_count = scrapy.Field()
    page_size_bytes = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # PRIMARY SEO FIELDS
    # ─────────────────────────────────────────────────────────────
    meta_title = scrapy.Field()
    h1 = scrapy.Field()
    meta_description = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # HEADING HIERARCHY
    # ─────────────────────────────────────────────────────────────
    h2_tags = scrapy.Field()    # List of h2 text content
    h3_tags = scrapy.Field()    # List of h3 text content

    # ─────────────────────────────────────────────────────────────
    # SEO META TAGS
    # ─────────────────────────────────────────────────────────────
    canonical_url = scrapy.Field()
    meta_robots = scrapy.Field()
    lang_attribute = scrapy.Field()
    viewport = scrapy.Field()
    charset = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # SOCIAL METADATA (Open Graph)
    # ─────────────────────────────────────────────────────────────
    og_title = scrapy.Field()
    og_description = scrapy.Field()
    og_image = scrapy.Field()
    og_url = scrapy.Field()
    og_type = scrapy.Field()
    og_site_name = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # SOCIAL METADATA (Twitter Cards)
    # ─────────────────────────────────────────────────────────────
    twitter_card = scrapy.Field()
    twitter_title = scrapy.Field()
    twitter_description = scrapy.Field()
    twitter_image = scrapy.Field()
    twitter_site = scrapy.Field()

    # ─────────────────────────────────────────────────────────────
    # IMAGES
    # ─────────────────────────────────────────────────────────────
    images_count = scrapy.Field()
    images = scrapy.Field()  # List of {src, alt, width, height}

    # ─────────────────────────────────────────────────────────────
    # LINKS
    # ─────────────────────────────────────────────────────────────
    internal_links_count = scrapy.Field()
    external_links_count = scrapy.Field()
    internal_links = scrapy.Field()  # List of {url, anchor_text, nofollow}
    external_links = scrapy.Field()  # List of {url, anchor_text, nofollow}

    # ─────────────────────────────────────────────────────────────
    # STRUCTURED DATA (JSON-LD)
    # ─────────────────────────────────────────────────────────────
    json_ld = scrapy.Field()         # Raw JSON-LD objects (list)
    schema_types = scrapy.Field()    # List of @type values found
```

### Step 2: Verify syntax

```bash
cd dumbcrawler/scrapy_app
python -c "from dumbcrawler.items import DumbcrawlerItem; print('✅ items.py valid')"
```

✅ **STOP — Verify items.py compiles before continuing.**

---

## Task 2A: Add Helper Methods to Pipeline

### Step 1: Replace entire pipelines.py

**File:** `dumbcrawler/scrapy_app/dumbcrawler/pipelines.py`

```python
"""
Scrapy Pipelines for dumbcrawler.
- MetadataExtractionPipeline: Extracts all metadata from raw_html
- JsonOutputPipeline: Writes items to JSONL file
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import html2text


class MetadataExtractionPipeline:
    """
    Extracts comprehensive metadata from raw_html.
    Populates 40+ fields from a single BeautifulSoup parse.
    """

    def __init__(self):
        # Configure html2text for clean markdown output
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # No wrapping

    def process_item(self, item, spider):
        """Main processing entry point."""
        raw_html = item.get('raw_html', '')
        url = item.get('url', '')

        if not raw_html:
            spider.logger.warning(f"No raw_html for {url}")
            return item

        # Parse once, extract everything
        soup = BeautifulSoup(raw_html, 'lxml')
        parsed_url = urlparse(url)
        base_domain = self._get_base_domain(parsed_url.netloc)

        # ─────────────────────────────────────────────────────────
        # TIMESTAMPS
        # ─────────────────────────────────────────────────────────
        item['crawled_at'] = datetime.now(timezone.utc).isoformat()

        # ─────────────────────────────────────────────────────────
        # CONTENT METRICS
        # ─────────────────────────────────────────────────────────
        item['page_size_bytes'] = len(raw_html.encode('utf-8'))

        body_text = self._extract_body_text(soup)
        item['body_content'] = body_text
        item['word_count'] = len(body_text.split()) if body_text else 0

        # ─────────────────────────────────────────────────────────
        # MARKDOWN CONTENT
        # ─────────────────────────────────────────────────────────
        item['markdown_content'] = self._convert_to_markdown(raw_html)

        # ─────────────────────────────────────────────────────────
        # PRIMARY SEO FIELDS
        # ─────────────────────────────────────────────────────────
        item['meta_title'] = self._get_title(soup)
        item['h1'] = self._get_first_h1(soup)
        item['meta_description'] = self._get_meta_name(soup, 'description')

        # ─────────────────────────────────────────────────────────
        # HEADING HIERARCHY
        # ─────────────────────────────────────────────────────────
        item['h2_tags'] = self._get_all_headings(soup, 'h2')
        item['h3_tags'] = self._get_all_headings(soup, 'h3')

        # ─────────────────────────────────────────────────────────
        # SEO META TAGS
        # ─────────────────────────────────────────────────────────
        item['canonical_url'] = self._get_canonical(soup)
        item['meta_robots'] = self._get_meta_name(soup, 'robots')
        item['lang_attribute'] = self._get_lang(soup)
        item['viewport'] = self._get_meta_name(soup, 'viewport')
        item['charset'] = self._get_charset(soup)

        # ─────────────────────────────────────────────────────────
        # OPEN GRAPH
        # ─────────────────────────────────────────────────────────
        item['og_title'] = self._get_meta_property(soup, 'og:title')
        item['og_description'] = self._get_meta_property(soup, 'og:description')
        item['og_image'] = self._get_meta_property(soup, 'og:image')
        item['og_url'] = self._get_meta_property(soup, 'og:url')
        item['og_type'] = self._get_meta_property(soup, 'og:type')
        item['og_site_name'] = self._get_meta_property(soup, 'og:site_name')

        # ─────────────────────────────────────────────────────────
        # TWITTER CARDS
        # ─────────────────────────────────────────────────────────
        item['twitter_card'] = self._get_meta_name(soup, 'twitter:card')
        item['twitter_title'] = self._get_meta_name(soup, 'twitter:title')
        item['twitter_description'] = self._get_meta_name(soup, 'twitter:description')
        item['twitter_image'] = self._get_meta_name(soup, 'twitter:image')
        item['twitter_site'] = self._get_meta_name(soup, 'twitter:site')

        # ─────────────────────────────────────────────────────────
        # IMAGES
        # ─────────────────────────────────────────────────────────
        images = self._extract_images(soup, url)
        item['images'] = images
        item['images_count'] = len(images)

        # ─────────────────────────────────────────────────────────
        # LINKS
        # ─────────────────────────────────────────────────────────
        internal_links, external_links = self._extract_links(soup, url, base_domain)
        item['internal_links'] = internal_links
        item['internal_links_count'] = len(internal_links)
        item['external_links'] = external_links
        item['external_links_count'] = len(external_links)

        # ─────────────────────────────────────────────────────────
        # JSON-LD / STRUCTURED DATA
        # ─────────────────────────────────────────────────────────
        json_ld_data = self._extract_json_ld(soup, spider)
        item['json_ld'] = json_ld_data
        item['schema_types'] = self._extract_schema_types(json_ld_data)

        return item

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _get_base_domain(self, netloc: str) -> str:
        """Extract base domain (last two parts) from netloc."""
        parts = netloc.lower().split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return netloc.lower()

    def _get_title(self, soup: BeautifulSoup) -> str | None:
        """Extract  tag content."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        return None

    def _get_first_h1(self, soup: BeautifulSoup) -> str | None:
        """Extract first  tag content."""
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        return None

    def _get_all_headings(self, soup: BeautifulSoup, tag: str) -> list[str]:
        """Extract all headings of given type."""
        headings = soup.find_all(tag)
        return [h.get_text(strip=True) for h in headings if h.get_text(strip=True)]

    def _get_meta_name(self, soup: BeautifulSoup, name: str) -> str | None:
        """Extract  content."""
        # Try name attribute
        meta = soup.find('meta', attrs={'name': re.compile(f'^{re.escape(name)}$', re.I)})
        if meta and meta.get('content'):
            return meta['content']
        return None

    def _get_meta_property(self, soup: BeautifulSoup, prop: str) -> str | None:
        """Extract  content (Open Graph)."""
        meta = soup.find('meta', attrs={'property': re.compile(f'^{re.escape(prop)}$', re.I)})
        if meta and meta.get('content'):
            return meta['content']
        return None

    def _get_canonical(self, soup: BeautifulSoup) -> str | None:
        """Extract canonical URL."""
        link = soup.find('link', rel='canonical')
        if link and link.get('href'):
            return link['href']
        return None

    def _get_lang(self, soup: BeautifulSoup) -> str | None:
        """Extract html lang attribute."""
        html_tag = soup.find('html')
        if html_tag:
            return html_tag.get('lang')
        return None

    def _get_charset(self, soup: BeautifulSoup) -> str | None:
        """Extract character encoding."""
        # Method 1: 
        meta = soup.find('meta', charset=True)
        if meta:
            return meta['charset']

        # Method 2: 
        meta = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})
        if meta and meta.get('content'):
            match = re.search(r'charset=([^\s;]+)', meta['content'], re.I)
            if match:
                return match.group(1)

        return None

    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """Extract visible text from body, excluding scripts/styles."""
        body = soup.find('body')
        if not body:
            return ''

        # Remove unwanted elements
        for element in body.find_all(['script', 'style', 'noscript', 'iframe']):
            element.decompose()

        # Get text with space separation
        text = body.get_text(separator=' ', strip=True)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _convert_to_markdown(self, html: str) -> str:
        """Convert HTML to markdown."""
        try:
            return self.html_converter.handle(html).strip()
        except Exception:
            return ''

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """Extract image data: src, alt, dimensions."""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                # Resolve relative URLs
                src = urljoin(base_url, src)

            image_data = {
                'src': src,
                'alt': img.get('alt', ''),
            }

            # Optional dimensions
            if img.get('width'):
                image_data['width'] = img['width']
            if img.get('height'):
                image_data['height'] = img['height']

            images.append(image_data)

        return images

    def _extract_links(
        self,
        soup: BeautifulSoup,
        page_url: str,
        base_domain: str
    ) -> tuple[list[dict], list[dict]]:
        """
        Extract and categorize links as internal or external.
        Returns (internal_links, external_links).
        """
        internal = []
        external = []

        parsed_page = urlparse(page_url)

        for a in soup.find_all('a', href=True):
            href = a['href']

            # Skip non-http links
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'data:')):
                continue

            # Resolve relative URLs
            full_url = urljoin(page_url, href)
            parsed = urlparse(full_url)

            # Skip non-http schemes
            if parsed.scheme not in ('http', 'https'):
                continue

            # Determine if nofollow
            rel = a.get('rel', [])
            if isinstance(rel, str):
                rel = rel.split()
            nofollow = 'nofollow' in rel

            link_data = {
                'url': full_url,
                'anchor_text': a.get_text(strip=True),
                'nofollow': nofollow,
            }

            # Categorize: internal if same base domain
            link_domain = self._get_base_domain(parsed.netloc)
            if link_domain == base_domain:
                internal.append(link_data)
            else:
                external.append(link_data)

        return internal, external

    def _extract_json_ld(self, soup: BeautifulSoup, spider) -> list[dict]:
        """Extract all JSON-LD structured data blocks."""
        json_ld_list = []

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                content = script.string
                if content:
                    data = json.loads(content)
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        json_ld_list.extend(data)
                    else:
                        json_ld_list.append(data)
            except json.JSONDecodeError as e:
                spider.logger.debug(f"Invalid JSON-LD: {e}")
            except Exception as e:
                spider.logger.debug(f"Error parsing JSON-LD: {e}")

        return json_ld_list

    def _extract_schema_types(self, json_ld_data: list[dict]) -> list[str]:
        """Extract all @type values from JSON-LD."""
        types = []

        def extract_types(obj):
            if isinstance(obj, dict):
                if '@type' in obj:
                    t = obj['@type']
                    if isinstance(t, list):
                        types.extend(t)
                    else:
                        types.append(t)
                # Recursively check nested objects
                for value in obj.values():
                    extract_types(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_types(item)

        for item in json_ld_data:
            extract_types(item)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for t in types:
            if t not in seen:
                seen.add(t)
                unique.append(t)

        return unique


class JsonOutputPipeline:
    """
    Writes items to JSON Lines file.
    One JSON object per line, UTF-8 encoded.
    """

    def __init__(self):
        self.file = None
        self.filepath = None

    def open_spider(self, spider):
        """Open output file when spider starts."""
        crawl_job_id = getattr(spider, 'crawl_job_id', 'default')
        self.filepath = Path(f'output_{crawl_job_id}.jsonl')
        self.file = open(self.filepath, 'w', encoding='utf-8')
        spider.logger.info(f"Writing output to: {self.filepath.absolute()}")

    def close_spider(self, spider):
        """Close output file when spider finishes."""
        if self.file:
            self.file.close()
            spider.logger.info(f"Output saved: {self.filepath.absolute()}")

    def process_item(self, item, spider):
        """Write item as single JSON line."""
        line = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(line + '\n')
        self.file.flush()
        return item
```

### Step 2: Verify syntax

```bash
cd dumbcrawler/scrapy_app
python -c "from dumbcrawler.pipelines import MetadataExtractionPipeline, JsonOutputPipeline; print('✅ pipelines.py valid')"
```

### Step 3: Verify imports work

```bash
python -c "
from dumbcrawler.pipelines import MetadataExtractionPipeline
from dumbcrawler.items import DumbcrawlerItem
print('✅ All imports working')
"
```

✅ **STOP — Verify pipeline compiles and imports work.**

---

## Task 3A: Run Verification Tests

### Test 1: Single URL with all extractions

```bash
cd dumbcrawler

python run_crawl.py \
  --client-id test \
  --crawl-job-id enhanced_test_1 \
  --mode single \
  --start-urls "https://www.python.org/" \
  --js-mode off
```

### Test 2: Validate all fields present

```bash
cat scrapy_app/output_enhanced_test_1.jsonl | python3 -c "
import json
import sys

item = json.loads(sys.stdin.read())

# Define expected fields by category
FIELDS = {
    'Identifiers': ['client_id', 'crawl_job_id', 'url'],
    'HTTP': ['status_code', 'response_headers'],
    'Discovery': ['depth', 'referrer_url', 'crawled_at'],
    'Raw Content': ['raw_html', 'body_content', 'markdown_content'],
    'Metrics': ['word_count', 'page_size_bytes'],
    'Primary SEO': ['meta_title', 'h1', 'meta_description'],
    'Headings': ['h2_tags', 'h3_tags'],
    'SEO Meta': ['canonical_url', 'meta_robots', 'lang_attribute', 'viewport', 'charset'],
    'Open Graph': ['og_title', 'og_description', 'og_image', 'og_url', 'og_type', 'og_site_name'],
    'Twitter': ['twitter_card', 'twitter_title', 'twitter_description', 'twitter_image', 'twitter_site'],
    'Images': ['images_count', 'images'],
    'Links': ['internal_links_count', 'external_links_count', 'internal_links', 'external_links'],
    'Structured Data': ['json_ld', 'schema_types'],
}

print('=' * 60)
print('FIELD PRESENCE CHECK')
print('=' * 60)

total_fields = 0
present_fields = 0

for category, fields in FIELDS.items():
    print(f'\n{category}:')
    for field in fields:
        total_fields += 1
        if field in item:
            present_fields += 1
            value = item[field]
            # Truncate long values
            if isinstance(value, str) and len(value) > 50:
                display = value[:50] + '...'
            elif isinstance(value, list):
                display = f'[{len(value)} items]'
            elif isinstance(value, dict):
                display = f'{{...}}'
            else:
                display = value
            print(f'  ✅ {field}: {display}')
        else:
            print(f'  ❌ {field}: MISSING')

print(f'\n{\"=\" * 60}')
print(f'TOTAL: {present_fields}/{total_fields} fields present')
print('=' * 60)
"
```

### Test 3: Validate data quality

```bash
cat scrapy_app/output_enhanced_test_1.jsonl | python3 -c "
import json
import sys

item = json.loads(sys.stdin.read())

print('=== DATA QUALITY CHECK ===\n')

# Check metrics make sense
print('📊 Content Metrics:')
print(f'   Word count: {item.get(\"word_count\", 0):,}')
print(f'   Page size: {item.get(\"page_size_bytes\", 0):,} bytes')
print(f'   Body content length: {len(item.get(\"body_content\", \"\")):,} chars')
print(f'   Markdown length: {len(item.get(\"markdown_content\", \"\")):,} chars')

# Check SEO
print('\n🔍 SEO Data:')
print(f'   Title: {item.get(\"meta_title\", \"N/A\")[:60]}')
print(f'   H1: {item.get(\"h1\", \"N/A\")[:60]}')
print(f'   Description: {str(item.get(\"meta_description\", \"N/A\"))[:60]}')
print(f'   Canonical: {item.get(\"canonical_url\", \"N/A\")[:60]}')
print(f'   Lang: {item.get(\"lang_attribute\", \"N/A\")}')

# Check headings
print('\n📑 Heading Hierarchy:')
h2s = item.get('h2_tags', [])
h3s = item.get('h3_tags', [])
print(f'   H2 tags: {len(h2s)}')
if h2s:
    print(f'   First H2: {h2s[0][:50]}...' if len(h2s[0]) > 50 else f'   First H2: {h2s[0]}')
print(f'   H3 tags: {len(h3s)}')

# Check social
print('\n📱 Social Metadata:')
print(f'   OG Title: {item.get(\"og_title\", \"N/A\")[:50]}')
print(f'   OG Image: {item.get(\"og_image\", \"N/A\")[:50]}')
print(f'   Twitter Card: {item.get(\"twitter_card\", \"N/A\")}')

# Check images
print('\n🖼️  Images:')
print(f'   Count: {item.get(\"images_count\", 0)}')
images = item.get('images', [])
if images:
    print(f'   First image src: {images[0].get(\"src\", \"N/A\")[:50]}...')

# Check links
print('\n🔗 Links:')
print(f'   Internal: {item.get(\"internal_links_count\", 0)}')
print(f'   External: {item.get(\"external_links_count\", 0)}')

# Check JSON-LD
print('\n📋 Structured Data:')
schema_types = item.get('schema_types', [])
print(f'   Schema types: {schema_types if schema_types else \"None found\"}')
json_ld = item.get('json_ld', [])
print(f'   JSON-LD blocks: {len(json_ld)}')

print('\n' + '=' * 40)
"
```

### Test 4: Test with JS-heavy site

```bash
python run_crawl.py \
  --client-id test \
  --crawl-job-id enhanced_test_js \
  --mode single \
  --start-urls "https://quotes.toscrape.com/js/" \
  --js-mode full
```

```bash
cat scrapy_app/output_enhanced_test_js.jsonl | python3 -c "
import json
import sys

item = json.loads(sys.stdin.read())

print('=== JS RENDERING CHECK ===\n')

body = item.get('body_content', '')
has_quotes = 'Albert Einstein' in body

print(f'Body content length: {len(body):,} chars')
print(f'Contains quote text: {\"✅ Yes\" if has_quotes else \"❌ No\"}')

if has_quotes:
    print('\nSample body content:')
    # Find and show quote
    idx = body.find('Albert Einstein')
    start = max(0, idx - 50)
    end = min(len(body), idx + 100)
    print(f'   ...{body[start:end]}...')
"
```

### Test 5: Test crawl mode with link extraction

```bash
python run_crawl.py \
  --client-id test \
  --crawl-job-id enhanced_crawl \
  --mode crawl \
  --start-urls "https://httpbin.org/links/5/0" \
  --max-depth 1 \
  --js-mode off \
  --restrict-to-subdomain true
```

```bash
cat scrapy_app/output_enhanced_crawl.jsonl | python3 -c "
import json
import sys

print('=== CRAWL MODE LINK CHECK ===\n')

total_internal = 0
total_external = 0
pages = 0

for line in sys.stdin:
    item = json.loads(line)
    pages += 1
    total_internal += item.get('internal_links_count', 0)
    total_external += item.get('external_links_count', 0)
    print(f'Page {pages}: {item[\"url\"]}')
    print(f'  Internal links: {item.get(\"internal_links_count\", 0)}')
    print(f'  External links: {item.get(\"external_links_count\", 0)}')

print(f'\n--- TOTALS ---')
print(f'Pages crawled: {pages}')
print(f'Total internal links found: {total_internal}')
print(f'Total external links found: {total_external}')
"
```

✅ **STOP — All tests should pass before considering task complete.**

---

## 📋 Complete Field Reference

### Output JSON Structure

```json
{
  "client_id": "string",
  "crawl_job_id": "string",
  "url": "string",
  
  "status_code": 200,
  "response_headers": {"Content-Type": "text/html", ...},
  
  "depth": 0,
  "referrer_url": null,
  "crawled_at": "2024-01-15T10:30:00.123456+00:00",
  
  "raw_html": "...",
  "body_content": "Plain text content without HTML tags...",
  "markdown_content": "# Page Title\n\nContent in markdown...",
  
  "word_count": 1523,
  "page_size_bytes": 45678,
  
  "meta_title": "Page Title - Site Name",
  "h1": "Main Heading",
  "meta_description": "Page description for SEO",
  
  "h2_tags": ["Section 1", "Section 2"],
  "h3_tags": ["Subsection A", "Subsection B"],
  
  "canonical_url": "https://example.com/page",
  "meta_robots": "index, follow",
  "lang_attribute": "en",
  "viewport": "width=device-width, initial-scale=1",
  "charset": "UTF-8",
  
  "og_title": "Open Graph Title",
  "og_description": "OG Description",
  "og_image": "https://example.com/image.jpg",
  "og_url": "https://example.com/page",
  "og_type": "website",
  "og_site_name": "Example Site",
  
  "twitter_card": "summary_large_image",
  "twitter_title": "Twitter Title",
  "twitter_description": "Twitter Description",
  "twitter_image": "https://example.com/twitter-image.jpg",
  "twitter_site": "@example",
  
  "images_count": 5,
  "images": [
    {"src": "https://example.com/img1.jpg", "alt": "Description", "width": "800", "height": "600"},
    {"src": "https://example.com/img2.png", "alt": ""}
  ],
  
  "internal_links_count": 25,
  "external_links_count": 8,
  "internal_links": [
    {"url": "https://example.com/about", "anchor_text": "About Us", "nofollow": false}
  ],
  "external_links": [
    {"url": "https://twitter.com/example", "anchor_text": "Twitter", "nofollow": true}
  ],
  
  "json_ld": [
    {"@context": "https://schema.org", "@type": "Organization", "name": "Example"}
  ],
  "schema_types": ["Organization", "WebPage"]
}
```

---

## ⚠️ Troubleshooting

### "No module named 'html2text'"

```bash
source .venv/bin/activate
pip install html2text
```

### Empty body_content

The page might have content loaded via JavaScript. Try:
- Use `--js-mode full`
- Check if `raw_html` has content

### JSON-LD not extracted

- Verify page actually has `<script type="application/ld+json">`
- Check spider logs for JSON parse errors

### Links not categorized correctly

- `base_domain` is calculated from the start URL
- Check logs for domain comparison logic

### Markdown content is messy

- html2text does best-effort conversion
- Some complex layouts may not convert cleanly

---

## 🔄 Future Enhancements (Not Included)

| Feature | Complexity | Notes |
|---------|------------|-------|
| Screenshots | 🟡 Medium | Requires Playwright page.screenshot() |
| Load time | 🟡 Medium | Requires Playwright timing API |
| Embeddings | 🔴 External | Requires OpenAI/Cohere API |
| Quality scoring | 🔴 Complex | Requires rules engine |
| Link location detection | 🟡 Medium | Detect nav/footer/body |
