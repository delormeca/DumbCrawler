"""
Pipelines for dumbcrawler.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import html2text
from bs4 import BeautifulSoup

from .geo_extractors import (
    ReadabilityExtractor,
    ContentPatternsExtractor,
    HeadingAnalysisExtractor,
    StructureElementsExtractor,
    SchemaExtractor,
    EEATExtractor,
    LinkAnalysisExtractor,
    BrokenLinkExtractor,
    HreflangExtractor,
    TemporalExtractor,
    MultimediaExtractor,
    AICrawlabilityExtractor,
)


class GEOAuditPipeline:
    """
    Comprehensive GEO (Generative Engine Optimization) audit pipeline.
    Extracts 60+ data points across 10 categories.
    """

    def __init__(self):
        self.html2text_handler = html2text.HTML2Text()
        self.html2text_handler.ignore_links = False
        self.html2text_handler.ignore_images = False
        self.html2text_handler.body_width = 0  # No wrapping

    def process_item(self, item, spider):
        """Process item and extract all GEO audit data."""
        raw_html = item.get("raw_html", "")
        url = item.get("url", "")

        if not raw_html:
            return item

        try:
            soup = BeautifulSoup(raw_html, "lxml")
        except Exception as e:
            spider.logger.warning(f"Failed to parse HTML for {url}: {e}")
            return item

        # Set crawled_at timestamp
        item["crawled_at"] = datetime.utcnow().isoformat() + "Z"

        # Calculate page size
        item["page_size_bytes"] = len(raw_html.encode('utf-8'))

        # Extract basic metadata
        self._extract_metadata(item, soup)

        # Extract body text
        body_text = self._extract_body_text(soup)
        item["body_content"] = body_text
        item["word_count"] = len(body_text.split()) if body_text else 0

        # Generate markdown content
        try:
            item["markdown_content"] = self.html2text_handler.handle(raw_html)
        except Exception as e:
            spider.logger.warning(f"Markdown conversion failed for {url}: {e}")
            item["markdown_content"] = None

        # Extract headings
        self._extract_headings(item, soup)

        # Extract SEO meta tags
        self._extract_seo_meta(item, soup)

        # Extract hreflang alternate tags
        try:
            item["hreflang"] = HreflangExtractor.extract(soup)
        except Exception as e:
            spider.logger.warning(f"Hreflang extraction failed: {e}")
            item["hreflang"] = {}

        # Extract social meta tags
        self._extract_social_meta(item, soup)

        # Extract images
        self._extract_images(item, soup)

        # Extract links
        self._extract_links(item, soup, url)

        # Broken link sampling (content decay signal)
        try:
            item["link_health"] = BrokenLinkExtractor.extract(soup, url)
        except Exception as e:
            spider.logger.warning(f"Broken link check failed: {e}")
            item["link_health"] = {}

        # Call all GEO extractors
        try:
            item["readability"] = ReadabilityExtractor.extract(body_text)
        except Exception as e:
            spider.logger.warning(f"Readability extraction failed: {e}")
            item["readability"] = {}

        try:
            item["content_patterns"] = ContentPatternsExtractor.extract(body_text, soup)
        except Exception as e:
            spider.logger.warning(f"Content patterns extraction failed: {e}")
            item["content_patterns"] = {}

        try:
            item["heading_analysis"] = HeadingAnalysisExtractor.extract(soup)
        except Exception as e:
            spider.logger.warning(f"Heading analysis failed: {e}")
            item["heading_analysis"] = {}

        try:
            item["structure_elements"] = StructureElementsExtractor.extract(soup)
        except Exception as e:
            spider.logger.warning(f"Structure elements extraction failed: {e}")
            item["structure_elements"] = {}

        try:
            schema_result = SchemaExtractor.extract(soup)
            item["schema_analysis"] = schema_result
            item["json_ld"] = schema_result.get("json_ld_blocks", [])
            item["schema_types"] = schema_result.get("schema_types", [])
        except Exception as e:
            spider.logger.warning(f"Schema extraction failed: {e}")
            item["schema_analysis"] = {}
            item["json_ld"] = []
            item["schema_types"] = []

        try:
            item["eeat_signals"] = EEATExtractor.extract(soup, url)
        except Exception as e:
            spider.logger.warning(f"E-E-A-T extraction failed: {e}")
            item["eeat_signals"] = {}

        try:
            item["outbound_link_analysis"] = LinkAnalysisExtractor.extract(soup, url)
        except Exception as e:
            spider.logger.warning(f"Link analysis failed: {e}")
            item["outbound_link_analysis"] = {}

        try:
            # Get published date for content age calculation
            published_date = None
            modified_date = None

            if item.get("eeat_signals"):
                published_date = item["eeat_signals"].get("published_date")
                modified_date = item["eeat_signals"].get("modified_date")
            if not published_date and item.get("schema_analysis"):
                published_date = item["schema_analysis"].get("schema_date_published")
            if not modified_date and item.get("schema_analysis"):
                modified_date = item["schema_analysis"].get("schema_date_modified")

            # HTTP Last-Modified header (server freshness signal)
            http_last_modified = None
            headers = item.get("response_headers") or {}
            if headers:
                http_last_modified = headers.get("Last-Modified") or headers.get("last-modified")
                if isinstance(http_last_modified, list) and http_last_modified:
                    http_last_modified = http_last_modified[0]

            item["temporal_analysis"] = TemporalExtractor.extract(
                body_text,
                published_date,
                modified_date,
                http_last_modified,
            )
        except Exception as e:
            spider.logger.warning(f"Temporal analysis failed: {e}")
            item["temporal_analysis"] = {}

        try:
            item["multimedia"] = MultimediaExtractor.extract(soup)
        except Exception as e:
            spider.logger.warning(f"Multimedia extraction failed: {e}")
            item["multimedia"] = {}

        try:
            item["ai_crawlability"] = AICrawlabilityExtractor.extract(soup, raw_html)
        except Exception as e:
            spider.logger.warning(f"AI crawlability extraction failed: {e}")
            item["ai_crawlability"] = {}

        return item

    def _extract_metadata(self, item, soup):
        """Extract basic page metadata."""
        # Title
        title_tag = soup.find("title")
        item["meta_title"] = title_tag.get_text(strip=True) if title_tag else None

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        item["meta_description"] = meta_desc.get("content", "").strip() if meta_desc else None

    def _extract_body_text(self, soup):
        """Extract body text, removing non-content elements."""
        # Clone soup to avoid modifying original
        body = soup.find("body")
        if not body:
            return ""

        # Create a copy for text extraction
        body_copy = BeautifulSoup(str(body), "lxml")

        # Remove non-content elements
        for tag in body_copy.find_all([
            "script", "style", "nav", "header", "footer",
            "aside", "noscript", "iframe", "svg"
        ]):
            tag.decompose()

        # Also remove common non-content classes
        for selector in [".nav", ".navigation", ".menu", ".sidebar",
                         ".footer", ".header", ".advertisement", ".ads"]:
            for elem in body_copy.select(selector):
                elem.decompose()

        return body_copy.get_text(separator=" ", strip=True)

    def _extract_headings(self, item, soup):
        """Extract heading tags."""
        # First H1
        h1_tag = soup.find("h1")
        item["h1"] = h1_tag.get_text(strip=True) if h1_tag else None

        # All H2s
        item["h2_tags"] = [
            h2.get_text(strip=True) for h2 in soup.find_all("h2")
        ]

        # All H3s
        item["h3_tags"] = [
            h3.get_text(strip=True) for h3 in soup.find_all("h3")
        ]

    def _extract_seo_meta(self, item, soup):
        """Extract SEO-related meta tags."""
        # Canonical URL
        canonical = soup.find("link", attrs={"rel": "canonical"})
        item["canonical_url"] = canonical.get("href") if canonical else None

        # Meta robots
        robots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        item["meta_robots"] = robots.get("content") if robots else None

        # Language
        html_tag = soup.find("html")
        item["lang_attribute"] = html_tag.get("lang") if html_tag else None

        # Viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        item["viewport"] = viewport.get("content") if viewport else None

        # Charset
        charset_meta = soup.find("meta", attrs={"charset": True})
        if charset_meta:
            item["charset"] = charset_meta.get("charset")
        else:
            content_type = soup.find("meta", attrs={"http-equiv": "Content-Type"})
            if content_type:
                content = content_type.get("content", "")
                match = re.search(r"charset=([^\s;]+)", content, re.I)
                item["charset"] = match.group(1) if match else None
            else:
                item["charset"] = None

    def _extract_social_meta(self, item, soup):
        """Extract Open Graph and Twitter Card meta tags."""
        # Open Graph
        og_tags = {
            "og_title": "og:title",
            "og_description": "og:description",
            "og_image": "og:image",
            "og_url": "og:url",
            "og_type": "og:type",
            "og_site_name": "og:site_name",
        }

        for field, property_name in og_tags.items():
            meta = soup.find("meta", attrs={"property": property_name})
            item[field] = meta.get("content") if meta else None

        # Twitter Card
        twitter_tags = {
            "twitter_card": "twitter:card",
            "twitter_title": "twitter:title",
            "twitter_description": "twitter:description",
            "twitter_image": "twitter:image",
            "twitter_site": "twitter:site",
        }

        for field, name in twitter_tags.items():
            meta = soup.find("meta", attrs={"name": name})
            if not meta:
                # Also try property attribute
                meta = soup.find("meta", attrs={"property": name})
            item[field] = meta.get("content") if meta else None

    def _extract_images(self, item, soup):
        """Extract image information."""
        images = []

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            image_info = {
                "src": src[:500],  # Truncate long URLs
                "alt": img.get("alt", "")[:200],
                "width": img.get("width"),
                "height": img.get("height"),
            }
            images.append(image_info)

        item["images"] = images
        item["images_count"] = len(images)

    def _extract_links(self, item, soup, base_url):
        """Extract internal and external links."""
        try:
            base_domain = urlparse(base_url).netloc.lower()
        except Exception:
            base_domain = ""

        internal_links = []
        external_links = []

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            anchor_text = link.get_text(strip=True)[:200]

            # Skip non-http links and anchors
            if href.startswith("#") or href.startswith("javascript:"):
                continue

            # Determine if internal or external
            if href.startswith(("http://", "https://")):
                try:
                    link_domain = urlparse(href).netloc.lower()
                except Exception:
                    continue

                if link_domain == base_domain or link_domain.endswith("." + base_domain):
                    internal_links.append({
                        "url": href[:500],
                        "anchor_text": anchor_text,
                    })
                else:
                    rel = link.get("rel", [])
                    if isinstance(rel, str):
                        rel = [rel]

                    external_links.append({
                        "url": href[:500],
                        "anchor_text": anchor_text,
                        "nofollow": "nofollow" in rel,
                    })
            else:
                # Relative URL - internal
                internal_links.append({
                    "url": href[:500],
                    "anchor_text": anchor_text,
                })

        item["internal_links"] = internal_links
        item["internal_links_count"] = len(internal_links)
        item["external_links"] = external_links
        item["external_links_count"] = len(external_links)


class MetadataExtractionPipeline:
    """
    Extract basic metadata from raw_html:
    - meta_title: <title> content
    - h1: First <h1> content
    - meta_description: <meta name="description"> content

    Note: GEOAuditPipeline already handles these, so this is kept for
    backward compatibility or standalone use.
    """

    def process_item(self, item, spider):
        raw_html = item.get("raw_html", "")

        if not raw_html:
            item["meta_title"] = None
            item["h1"] = None
            item["meta_description"] = None
            return item

        try:
            soup = BeautifulSoup(raw_html, "lxml")

            # Extract <title>
            title_tag = soup.find("title")
            item["meta_title"] = title_tag.get_text(strip=True) if title_tag else None

            # Extract first <h1>
            h1_tag = soup.find("h1")
            item["h1"] = h1_tag.get_text(strip=True) if h1_tag else None

            # Extract <meta name="description">
            meta_desc = soup.find("meta", attrs={"name": "description"})
            item["meta_description"] = meta_desc.get("content", "").strip() if meta_desc else None

        except Exception as e:
            spider.logger.warning(f"Metadata extraction failed for {item.get('url')}: {e}")
            item["meta_title"] = None
            item["h1"] = None
            item["meta_description"] = None

        return item


class JsonOutputPipeline:
    """
    Output items as JSON Lines (one JSON object per line).
    Output file: output_{crawl_job_id}.jsonl
    """

    def __init__(self):
        self.file = None
        self.output_path = None

    def open_spider(self, spider):
        """Open output file when spider starts."""
        # Get crawl_job_id for unique filename
        job_id = getattr(spider, "crawl_job_id", "default")
        self.output_path = Path(f"output_{job_id}.jsonl")

        spider.logger.info(f"Opening output file: {self.output_path}")
        self.file = open(self.output_path, "w", encoding="utf-8")

    def close_spider(self, spider):
        """Close output file when spider finishes."""
        if self.file:
            self.file.close()
            spider.logger.info(f"Closed output file: {self.output_path}")

    def process_item(self, item, spider):
        """Write item as JSON line."""
        # Convert item to dict if needed
        item_dict = dict(item) if hasattr(item, "items") else item

        # Write JSON line
        line = json.dumps(item_dict, ensure_ascii=False, default=str)
        self.file.write(line + "\n")
        self.file.flush()

        return item
