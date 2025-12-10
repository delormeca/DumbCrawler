# Dumbcrawler GEO Audit Command File

> **Purpose:** Extract 60+ data points for Generative Engine Optimization (GEO) auditing **Dependencies:** textstat, BeautifulSoup (no external APIs) **Estimated Implementation Time:** ~60 minutes

----------

## Overview

Add comprehensive GEO audit capabilities to dumbcrawler, extracting data across 8 categories:

Category

Metrics

Extractability

Questions, definitions, statistics, citations

Structure

Headings, lists, tables, schema

Authority (E-E-A-T)

Author, dates, trust pages, credentials

Freshness

Dates, temporal signals, content age

Readability

Flesch, Gunning Fog, SMOG, etc.

Links

Authority links, outbound analysis

Multimedia

Videos, audio, PDFs

AI Crawlability

Content ratio, JS signals

----------

## Task 0A: Install Dependencies

Install textstat>=0.7.3 and add it to requirements.txt. Verify the import works before continuing.

----------

## Task 0B: Create geo_patterns.py

**File:** `dumbcrawler/scrapy_app/dumbcrawler/geo_patterns.py`

Create a Python module containing compiled regex patterns for:

1.  **Question patterns** - Detect questions in body text and headings (what, who, where, when, why, how, etc.)
2.  **Definition patterns** - Identify definitions using phrases like "X is a", "X refers to", "X means", "defined as"
3.  **Comparison patterns** - Find comparisons using "vs", "compared to", "difference between", "better than", "pros/cons"
4.  **Statistics patterns** - Match percentages, dollar amounts, large numbers, ratios, multipliers
5.  **Citation patterns** - Detect "according to", named sources, research references, academic citations
6.  **Expert patterns** - Find credentials (Dr., PhD, MD, Professor), expert quotes, titles, years of experience
7.  **Temporal patterns** - Match years (19xx, 20xx), relative time phrases, "as of" statements, month-year references, outdated signals
8.  **Semantic triple patterns** - Basic subject-predicate-object patterns like "X is a Y", "X has Y", "X provides Y"
9.  **Authority domains** - Set of trusted domains (.gov, .edu, wikipedia.org, major news sites, research databases)
10.  **Trust page patterns** - Regex for /about, /contact, /privacy, /terms, /author URLs

Verify the module imports correctly.

----------

## Task 1A: Create geo_extractors.py

**File:** `dumbcrawler/scrapy_app/dumbcrawler/geo_extractors.py`

Create a module with 10 extractor classes. Each class should have an `extract()` static method returning a dictionary.

### 1. ReadabilityExtractor

Extract using textstat library:

-   flesch_reading_ease, flesch_kincaid_grade, gunning_fog, smog_index
-   automated_readability_index, coleman_liau_index
-   reading_time_minutes, sentence_count, avg_sentence_length
-   avg_word_length, syllable_count
-   difficult_words_count, difficult_words_percent, word_count

### 2. ContentPatternsExtractor

Use patterns from geo_patterns.py to extract:

-   Questions (count + examples)
-   Question headings (count + examples)
-   Definitions (count + examples)
-   Comparisons (count)
-   Statistics (count + examples)
-   Citations (count + examples)
-   Expert mentions (count)
-   Semantic triples (count + examples)

### 3. HeadingAnalysisExtractor

Analyze heading structure from BeautifulSoup:

-   List of all headings with level, text, word_count
-   Counts for h1 through h6
-   Hierarchy validation (missing h1, multiple h1, skipped levels)
-   Average heading length

### 4. StructureElementsExtractor

Extract structural elements:

-   Lists (ordered count, unordered count, total items)
-   Tables (count, details with rows/cells/header/caption)
-   Blockquotes (count, samples)
-   Code blocks (pre count, inline code count)
-   Definition lists (dl/dt counts)
-   Accordions (details tag count)
-   Figures (count, with caption count)

### 5. SchemaExtractor

Parse JSON-LD structured data:

-   Extract all JSON-LD blocks
-   Recursively collect all @type values
-   Boolean flags for FAQ, HowTo, Article, Person, Organization, Product, Breadcrumb, WebPage schemas
-   Extract author info from schema
-   Extract dates (datePublished, dateModified, dateCreated) from schema

### 6. EEATExtractor

Extract E-E-A-T signals:

-   Author detection (meta tag, rel=author link, common class names)
-   Date detection (time element, meta tags)
-   Trust page link detection (about, contact, privacy, terms, author)
-   Contact info detection (email regex, phone regex, address element)
-   Credential detection (PhD, MD, Professor, Certified, Licensed, years experience)

### 7. LinkAnalysisExtractor

Analyze outbound links:

-   List of outbound links with url, domain, anchor_text, nofollow/sponsored/ugc flags
-   Total outbound count
-   Authority links (matching authority domains set)
-   Gov/edu links count
-   Wikipedia links count
-   Unique domains count
-   Nofollow count and ratio

### 8. TemporalExtractor

Analyze temporal signals:

-   Years mentioned (sorted, deduplicated)
-   Most recent and oldest year
-   Has current year / has last year flags
-   Relative time phrases
-   "As of" statements
-   Month-year references
-   Outdated signals count
-   Content age in days (if published date available)

### 9. MultimediaExtractor

Extract multimedia elements:

-   Videos (YouTube, Vimeo, Wistia iframes; HTML5 video tags)
-   Audio (HTML5 audio; Spotify, Apple Podcasts, Anchor iframes)
-   PDFs (links ending in .pdf)
-   Infographics (images with infographic/chart/diagram/graph in alt or src)
-   Boolean flags for has_video, has_audio, has_pdf

### 10. AICrawlabilityExtractor

Analyze AI crawler accessibility:

-   Content ratio (text bytes / html bytes)
-   Script counts (inline, external, total)
-   Has noscript content flag
-   Meta robots value
-   Iframe count
-   Lazy loading (lazy attribute images, data-src images)
-   Custom elements count (tags with hyphens)
-   Canvas elements count
-   JS dependency signals (heavy framework detection)

Verify all 10 extractors import correctly.

----------

## Task 2A: Update items.py

**File:** `dumbcrawler/scrapy_app/dumbcrawler/items.py`

Replace with a DumbcrawlerItem class containing these field categories:

-   **Core identifiers:** client_id, crawl_job_id, url, crawled_at
-   **HTTP response:** status_code, response_headers, depth, referrer_url
-   **Raw content:** raw_html, page_size_bytes
-   **Page metadata:** meta_title, meta_description, canonical_url, meta_robots, lang_attribute, viewport, charset
-   **Headings:** h1, h2_tags, h3_tags, heading_analysis
-   **Content metrics:** word_count, body_content, markdown_content
-   **GEO extraction:** readability, content_patterns, structure_elements
-   **Social metadata:** og_title, og_description, og_image, og_url, og_type, og_site_name, twitter_card, twitter_title, twitter_description, twitter_image, twitter_site
-   **Images:** images_count, images
-   **Links:** internal_links_count, internal_links, external_links_count, external_links, outbound_link_analysis
-   **Structured data:** json_ld, schema_types, schema_analysis
-   **E-E-A-T & Authority:** eeat_signals, temporal_analysis, multimedia, ai_crawlability

Verify field count (should be approximately 43 fields).

----------

## Task 2B: Update pipelines.py

**File:** `dumbcrawler/scrapy_app/dumbcrawler/pipelines.py`

Create a GEOAuditPipeline class that:

1.  Parses raw_html with BeautifulSoup
2.  Sets crawled_at timestamp
3.  Extracts basic metadata (title, description)
4.  Extracts body text (removing script, style, nav, header, footer)
5.  Calculates word_count and page_size_bytes
6.  Generates markdown_content using html2text
7.  Extracts headings (h1, h2_tags, h3_tags)
8.  Extracts SEO meta (canonical, robots, lang, viewport, charset)
9.  Extracts social meta (Open Graph, Twitter Card)
10.  Extracts images with src, alt, dimensions
11.  Extracts internal and external links with anchor text and nofollow status
12.  Calls all 10 GEO extractors and stores results in appropriate item fields

Verify pipeline compiles correctly.

----------

## Task 2C: Update settings.py

Add the GEOAuditPipeline to ITEM_PIPELINES with priority 300.

----------

## Task 3A: Verification Test

Run a test crawl against a real URL (e.g., python.org) and verify the output JSON contains:

-   readability
-   content_patterns
-   heading_analysis
-   structure_elements
-   schema_analysis
-   eeat_signals
-   temporal_analysis
-   multimedia
-   ai_crawlability
-   outbound_link_analysis

----------

## Output Summary

This implementation extracts **60+ data points** across these categories:

Category

Fields

Key Metrics

Readability

14

Flesch, Gunning Fog, SMOG, reading time

Content Patterns

8

Questions, definitions, statistics, citations

Heading Analysis

10

Hierarchy, counts, validation

Structure Elements

7

Lists, tables, blockquotes, figures

Schema/JSON-LD

12

Type flags, author, dates

E-E-A-T Signals

8

Author, dates, trust pages, credentials

Link Analysis

9

Authority links, domains, nofollow ratio

Temporal Analysis

11

Years, freshness signals, content age

Multimedia

7

Videos, audio, PDFs, infographics

AI Crawlability

9

Content ratio, scripts, JS signals