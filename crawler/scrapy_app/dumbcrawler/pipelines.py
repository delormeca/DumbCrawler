# Define your item pipelines here

import json
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dateutil.parser import ParserError

# Import GEO extractors for comprehensive analysis
from .geo_extractors import (
    ReadabilityExtractor,
    ContentPatternsExtractor,
    HeadingAnalysisExtractor,
    StructureElementsExtractor,
    SchemaExtractor,
    EEATExtractor,
    LinkAnalysisExtractor,
    HreflangExtractor,
    TemporalExtractor,
    MultimediaExtractor,
    AICrawlabilityExtractor,
    # BrokenLinkExtractor - excluded for performance (makes external HTTP requests)
)


class DumbCrawlerPipeline:
    """
    Pipeline to process and serialize crawled items.

    Extracts comprehensive metadata from raw_html:
    - SEO tags (canonical, robots, lang, viewport)
    - Open Graph metadata
    - Twitter Cards metadata
    - Heading hierarchy (h2, h3)
    - Images analysis
    - Internal/external links
    - JSON-LD structured data
    - Content metrics (word count, page size)
    """

    def process_item(self, item, spider):
        """Process each crawled item with full metadata extraction."""
        # Add crawl timestamp
        item["crawled_at"] = datetime.now(timezone.utc).isoformat()

        # Add crawler info
        item["crawler"] = {
            "name": "DumbCrawler",
            "version": "2.0",
            "mode": getattr(spider, 'crawl_mode', 'unknown'),
            "js_mode": getattr(spider, 'js_mode', 'unknown'),
            "scope": getattr(spider, 'scope', 'unknown'),
        }

        # Extract enhanced metadata from raw_html
        raw_html = item.get("raw_html", "")
        url = item.get("url", "")

        if raw_html:
            try:
                soup = BeautifulSoup(raw_html, 'html.parser')
                item = self._extract_enhanced_metadata(item, soup, url)
            except Exception as e:
                spider.logger.debug(f"Error parsing HTML for {url}: {e}")

        return item

    def _extract_enhanced_metadata(self, item, soup, url):
        """Extract all enhanced metadata from parsed HTML."""
        parsed_url = urlparse(url)
        base_domain = self._get_base_domain(parsed_url.netloc)

        # === CONTENT METRICS ===
        item["page_size_bytes"] = len(item.get("raw_html", "").encode('utf-8'))
        body_text = self._extract_body_text(soup)
        item["body_text"] = body_text
        item["word_count"] = len(body_text.split()) if body_text else 0

        # === MAIN CONTENT (for entity extraction - excludes nav/header/footer/sidebar) ===
        main_content = self._extract_main_content(soup)
        item["main_content"] = main_content
        item["main_content_word_count"] = len(main_content.split()) if main_content else 0

        # === HEADING HIERARCHY ===
        item["h2_tags"] = [h.get_text(strip=True) for h in soup.find_all('h2') if h.get_text(strip=True)]
        item["h3_tags"] = [h.get_text(strip=True) for h in soup.find_all('h3') if h.get_text(strip=True)]

        # === SEO META TAGS ===
        item["canonical_url"] = self._get_tag_content(soup, 'link', rel='canonical', attr='href')
        item["meta_robots"] = self._get_meta_content(soup, 'robots')
        item["lang"] = soup.find('html').get('lang') if soup.find('html') else None
        item["viewport"] = self._get_meta_content(soup, 'viewport')
        item["charset"] = self._get_charset(soup)

        # === OPEN GRAPH ===
        item["og"] = {
            "title": self._get_meta_property(soup, 'og:title'),
            "description": self._get_meta_property(soup, 'og:description'),
            "image": self._get_meta_property(soup, 'og:image'),
            "url": self._get_meta_property(soup, 'og:url'),
            "type": self._get_meta_property(soup, 'og:type'),
            "site_name": self._get_meta_property(soup, 'og:site_name'),
        }

        # === TWITTER CARDS ===
        item["twitter"] = {
            "card": self._get_meta_content(soup, 'twitter:card'),
            "title": self._get_meta_content(soup, 'twitter:title'),
            "description": self._get_meta_content(soup, 'twitter:description'),
            "image": self._get_meta_content(soup, 'twitter:image'),
            "site": self._get_meta_content(soup, 'twitter:site'),
        }

        # === IMAGES ===
        images = self._extract_images(soup, url)
        item["images"] = images
        item["images_count"] = len(images)

        # === LINKS ANALYSIS ===
        internal_links, external_links = self._extract_links(soup, url, base_domain)
        item["internal_links"] = internal_links
        item["internal_links_count"] = len(internal_links)
        item["external_links"] = external_links
        item["external_links_count"] = len(external_links)

        # === ANCHOR TEXT ANALYSIS ===
        anchor_analysis = self._analyze_anchor_texts(internal_links)
        item["anchor_analysis"] = anchor_analysis

        # === JSON-LD STRUCTURED DATA ===
        json_ld = self._extract_json_ld(soup)
        item["json_ld"] = json_ld
        item["schema_types"] = self._extract_schema_types(json_ld)

        # === CONTENT AGE ===
        item["content_age"] = self._extract_content_age(item, soup, json_ld)

        # === GEO EXTRACTORS (Generative Engine Optimization) ===
        try:
            # 1. Readability metrics (requires textstat)
            item["readability"] = ReadabilityExtractor.extract(body_text)
        except Exception as e:
            item["readability"] = {"error": str(e)}

        try:
            # 2. Content patterns (questions, definitions, comparisons, statistics, etc.)
            item["content_patterns"] = ContentPatternsExtractor.extract(body_text, soup)
        except Exception as e:
            item["content_patterns"] = {"error": str(e)}

        try:
            # 3. Enhanced heading analysis
            item["heading_analysis"] = HeadingAnalysisExtractor.extract(soup)
        except Exception as e:
            item["heading_analysis"] = {"error": str(e)}

        try:
            # 4. Structure elements (lists, tables, blockquotes, code blocks, figures)
            item["structure_elements"] = StructureElementsExtractor.extract(soup)
        except Exception as e:
            item["structure_elements"] = {"error": str(e)}

        try:
            # 5. Enhanced schema/JSON-LD analysis
            item["schema_analysis"] = SchemaExtractor.extract(soup)
        except Exception as e:
            item["schema_analysis"] = {"error": str(e)}

        try:
            # 6. E-E-A-T signals (Experience, Expertise, Authoritativeness, Trust)
            item["eeat_signals"] = EEATExtractor.extract(soup, url)
        except Exception as e:
            item["eeat_signals"] = {"error": str(e)}

        try:
            # 7. Outbound/authority link analysis
            item["outbound_link_analysis"] = LinkAnalysisExtractor.extract(soup, url)
        except Exception as e:
            item["outbound_link_analysis"] = {"error": str(e)}

        try:
            # 8. Hreflang tags for international SEO
            item["hreflang"] = HreflangExtractor.extract(soup)
        except Exception as e:
            item["hreflang"] = {"error": str(e)}

        try:
            # 9. Temporal signals (years mentioned, freshness indicators)
            published_date = item.get("content_age", {}).get("published")
            modified_date = item.get("content_age", {}).get("modified")
            http_last_modified = item.get("response_headers", {}).get("Last-Modified")
            item["temporal_signals"] = TemporalExtractor.extract(
                body_text, published_date, modified_date, http_last_modified
            )
        except Exception as e:
            item["temporal_signals"] = {"error": str(e)}

        try:
            # 10. Multimedia elements (videos, audio, PDFs, infographics)
            item["multimedia"] = MultimediaExtractor.extract(soup)
        except Exception as e:
            item["multimedia"] = {"error": str(e)}

        try:
            # 11. AI crawlability signals
            item["ai_crawlability"] = AICrawlabilityExtractor.extract(soup, item.get("raw_html", ""))
        except Exception as e:
            item["ai_crawlability"] = {"error": str(e)}

        return item

    # === HELPER METHODS ===

    def _get_base_domain(self, netloc):
        """Extract base domain (last two parts) from netloc."""
        parts = netloc.lower().split('.')
        return '.'.join(parts[-2:]) if len(parts) >= 2 else netloc.lower()

    def _get_meta_content(self, soup, name):
        """Extract <meta name="X"> content."""
        meta = soup.find('meta', attrs={'name': re.compile(f'^{re.escape(name)}$', re.I)})
        return meta.get('content') if meta and meta.get('content') else None

    def _get_meta_property(self, soup, prop):
        """Extract <meta property="X"> content (Open Graph)."""
        meta = soup.find('meta', attrs={'property': re.compile(f'^{re.escape(prop)}$', re.I)})
        return meta.get('content') if meta and meta.get('content') else None

    def _get_tag_content(self, soup, tag, attr='content', **find_attrs):
        """Extract content from a specific tag with attributes."""
        element = soup.find(tag, attrs=find_attrs)
        return element.get(attr) if element and element.get(attr) else None

    def _get_charset(self, soup):
        """Extract character encoding."""
        meta = soup.find('meta', charset=True)
        if meta:
            return meta['charset']
        meta = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})
        if meta and meta.get('content'):
            match = re.search(r'charset=([^\s;]+)', meta['content'], re.I)
            if match:
                return match.group(1)
        return None

    def _extract_body_text(self, soup):
        """Extract visible text from body, excluding scripts/styles."""
        body = soup.find('body')
        if not body:
            return ''
        # Remove unwanted elements
        for element in body.find_all(['script', 'style', 'noscript', 'iframe']):
            element.decompose()
        text = body.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_main_content(self, soup):
        """
        Extract main article content, excluding navigation/header/footer/sidebar.

        This is optimized for entity extraction and NLP analysis.
        Tries multiple strategies to find the main content area.
        """
        # Strategy 1: Look for <main> or <article> elements
        main_element = soup.find('main') or soup.find('article')

        if main_element:
            # Clone to avoid modifying original
            main_clone = BeautifulSoup(str(main_element), 'html.parser')
            # Remove nested nav/aside within main
            for element in main_clone.find_all(['script', 'style', 'noscript', 'iframe', 'nav', 'aside']):
                element.decompose()
            text = main_clone.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 200:  # Valid main content
                return text

        # Strategy 2: Look for common content containers
        content_selectors = [
            {'class_': re.compile(r'(article|post|entry|content|main)[-_]?(body|content|text|area)?', re.I)},
            {'id': re.compile(r'(article|post|entry|content|main)[-_]?(body|content|text|area)?', re.I)},
            {'role': 'main'},
            {'itemprop': 'articleBody'},
        ]

        for selector in content_selectors:
            element = soup.find(['div', 'section', 'article'], attrs=selector)
            if element:
                elem_clone = BeautifulSoup(str(element), 'html.parser')
                for unwanted in elem_clone.find_all(['script', 'style', 'noscript', 'iframe', 'nav', 'aside']):
                    unwanted.decompose()
                text = elem_clone.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 200:
                    return text

        # Strategy 3: Fallback - body minus nav/header/footer/aside
        body = soup.find('body')
        if not body:
            return ''

        body_clone = BeautifulSoup(str(body), 'html.parser')
        # Remove all structural/boilerplate elements
        for element in body_clone.find_all([
            'script', 'style', 'noscript', 'iframe',
            'nav', 'header', 'footer', 'aside',
            'form', 'button', 'input', 'select', 'textarea'
        ]):
            element.decompose()

        # Also remove elements with common boilerplate class names
        boilerplate_patterns = re.compile(
            r'(nav|menu|sidebar|footer|header|comment|share|social|related|widget|ad|promo|banner|cookie|popup|modal)',
            re.I
        )
        for element in body_clone.find_all(class_=boilerplate_patterns):
            element.decompose()
        for element in body_clone.find_all(id=boilerplate_patterns):
            element.decompose()

        text = body_clone.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_images(self, soup, base_url):
        """Extract image data: src, alt, dimensions."""
        images = []
        for img in soup.find_all('img')[:100]:  # Limit to first 100
            src = img.get('src', '')
            if src:
                src = urljoin(base_url, src)
            image_data = {'src': src, 'alt': img.get('alt', '')}
            if img.get('width'):
                image_data['width'] = img['width']
            if img.get('height'):
                image_data['height'] = img['height']
            images.append(image_data)
        return images

    def _extract_links(self, soup, page_url, base_domain):
        """Extract and categorize links as internal or external."""
        internal, external = [], []
        for a in soup.find_all('a', href=True)[:500]:  # Limit to first 500
            href = a['href']
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'data:')):
                continue
            full_url = urljoin(page_url, href)
            parsed = urlparse(full_url)
            if parsed.scheme not in ('http', 'https'):
                continue
            rel = a.get('rel', [])
            if isinstance(rel, str):
                rel = rel.split()
            link_data = {
                'url': full_url,
                'anchor': a.get_text(strip=True)[:100],
                'nofollow': 'nofollow' in rel,
            }
            link_domain = self._get_base_domain(parsed.netloc)
            if link_domain == base_domain:
                internal.append(link_data)
            else:
                external.append(link_data)
        return internal, external

    # Generic anchor text patterns (EN/FR/ES) - bad for SEO
    GENERIC_ANCHORS = {
        # English
        'click here', 'click', 'here', 'read more', 'read', 'more', 'learn more',
        'learn', 'see more', 'view more', 'view', 'see', 'go', 'go here', 'link',
        'this link', 'this page', 'this article', 'this post', 'continue',
        'continue reading', 'full article', 'full story', 'details', 'more info',
        'more information', 'info', 'download', 'get it', 'get', 'start',
        'start here', 'begin', 'next', 'previous', 'back', 'home', 'website',
        'site', 'page', 'article', 'post', 'blog', 'check it out', 'check out',
        'find out', 'find out more', 'discover', 'explore', 'visit', 'source',
        # French
        'cliquez ici', 'cliquer ici', 'cliquez', 'ici', 'en savoir plus',
        'lire la suite', 'lire plus', 'lire', 'voir plus', 'voir', 'suite',
        'continuer', 'plus', 'plus d\'info', 'plus d\'infos', 'plus d\'informations',
        'en apprendre plus', 'découvrir', 'découvrez', 'visiter', 'visitez',
        'accéder', 'accédez', 'consulter', 'consultez', 'télécharger',
        'commencer', 'suivant', 'précédent', 'retour', 'accueil', 'page',
        'article', 'ce lien', 'cette page', 'cet article', 'ce site',
        # Spanish
        'haga clic aquí', 'clic aquí', 'haz clic', 'clic', 'aquí', 'leer más',
        'leer', 'más', 'ver más', 'ver', 'saber más', 'más información',
        'más info', 'continuar', 'continuar leyendo', 'siguiente', 'anterior',
        'volver', 'inicio', 'página', 'artículo', 'descargar', 'obtener',
        'comenzar', 'empezar', 'descubrir', 'descubre', 'explorar', 'visitar',
        'visita', 'este enlace', 'esta página', 'este artículo', 'este sitio',
        # Common symbols/patterns
        '>', '>>', '→', '...', '»', 'more...', 'lire...', 'más...',
    }

    def _analyze_anchor_texts(self, internal_links):
        """
        Analyze anchor text quality for internal links.

        Returns analysis with:
        - generic_count: links with generic/non-descriptive anchors
        - empty_count: links with no anchor text
        - image_only_count: links that only contain an image
        - good_count: links with descriptive anchors
        - generic_links: list of links with generic anchors (for review)
        """
        generic_links = []
        empty_links = []
        good_links = []

        for link in internal_links:
            anchor = link.get('anchor', '').strip()
            anchor_lower = anchor.lower()

            if not anchor:
                # Empty anchor
                empty_links.append(link)
            elif anchor_lower in self.GENERIC_ANCHORS or self._is_generic_anchor(anchor_lower):
                # Generic anchor
                generic_links.append(link)
            else:
                # Good descriptive anchor
                good_links.append(link)

        total = len(internal_links)
        return {
            "total_internal_links": total,
            "generic_anchor_count": len(generic_links),
            "generic_anchor_percent": round((len(generic_links) / total * 100), 1) if total > 0 else 0,
            "empty_anchor_count": len(empty_links),
            "empty_anchor_percent": round((len(empty_links) / total * 100), 1) if total > 0 else 0,
            "good_anchor_count": len(good_links),
            "good_anchor_percent": round((len(good_links) / total * 100), 1) if total > 0 else 0,
            # Sample of problematic links for review
            "generic_anchor_samples": generic_links[:20],
            "empty_anchor_samples": empty_links[:10],
        }

    def _is_generic_anchor(self, anchor_lower):
        """Check if anchor matches generic patterns beyond exact matches."""
        # Very short anchors (1-2 chars) are usually generic
        if len(anchor_lower) <= 2:
            return True

        # Check for patterns
        generic_patterns = [
            r'^click\s',          # starts with "click"
            r'^clic\s',           # French/Spanish click
            r'\shere$',           # ends with "here"
            r'\sici$',            # ends with "ici" (French)
            r'\saquí$',           # ends with "aquí" (Spanish)
            r'^read\s',           # starts with "read"
            r'^lire\s',           # starts with "lire"
            r'^leer\s',           # starts with "leer"
            r'^voir\s',           # starts with "voir"
            r'^ver\s',            # starts with "ver"
            r'more\s*>>?$',       # ends with "more >" or "more >>"
            r'plus\s*>>?$',       # ends with "plus >"
            r'más\s*>>?$',        # ends with "más >"
            r'^\d+$',             # just numbers
            r'^#\d+$',            # just #number
        ]

        for pattern in generic_patterns:
            if re.search(pattern, anchor_lower):
                return True

        return False

    def _extract_json_ld(self, soup):
        """Extract all JSON-LD structured data blocks."""
        json_ld_list = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                content = script.string
                if content:
                    data = json.loads(content)
                    if isinstance(data, list):
                        json_ld_list.extend(data)
                    else:
                        json_ld_list.append(data)
            except (json.JSONDecodeError, Exception):
                pass
        return json_ld_list

    def _extract_schema_types(self, json_ld_data):
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
                for value in obj.values():
                    extract_types(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_types(item)
        for item in json_ld_data:
            extract_types(item)
        # Remove duplicates while preserving order
        seen = set()
        return [t for t in types if not (t in seen or seen.add(t))]

    # === CONTENT AGE EXTRACTION ===

    def _extract_content_age(self, item, soup, json_ld_data):
        """
        Extract content age from multiple sources.

        Returns dict with:
        - published: ISO date string when content was first published
        - modified: ISO date string when content was last modified
        - sources: dict showing where each date was found

        Sources checked (in priority order):
        1. JSON-LD structured data (most reliable)
        2. Open Graph article times
        3. Meta tags (various formats)
        4. HTTP Last-Modified header
        5. HTML <time> elements
        6. Common date patterns in HTML
        """
        result = {
            "published": None,
            "modified": None,
            "sources": {}
        }

        # Track all found dates with their sources for transparency
        found_dates = {
            "published": [],
            "modified": []
        }

        # === 1. JSON-LD STRUCTURED DATA (highest priority) ===
        self._extract_dates_from_json_ld(json_ld_data, found_dates)

        # === 2. OPEN GRAPH ARTICLE TIMES ===
        self._extract_dates_from_og(soup, found_dates)

        # === 3. META TAGS ===
        self._extract_dates_from_meta(soup, found_dates)

        # === 4. HTTP HEADERS ===
        self._extract_dates_from_headers(item, found_dates)

        # === 5. HTML TIME ELEMENTS ===
        self._extract_dates_from_time_elements(soup, found_dates)

        # === 6. COMMON HTML PATTERNS ===
        self._extract_dates_from_html_patterns(soup, found_dates)

        # Select best dates (first found = highest priority)
        if found_dates["published"]:
            best = found_dates["published"][0]
            result["published"] = best["date"]
            result["sources"]["published"] = best["source"]

        if found_dates["modified"]:
            best = found_dates["modified"][0]
            result["modified"] = best["date"]
            result["sources"]["modified"] = best["source"]

        # If we have modified but not published, use modified as published
        if result["modified"] and not result["published"]:
            result["published"] = result["modified"]
            result["sources"]["published"] = result["sources"].get("modified", "inferred")

        # Calculate age in days if we have a date
        if result["published"]:
            try:
                pub_date = datetime.fromisoformat(result["published"].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                result["age_days"] = (now - pub_date).days
            except (ValueError, TypeError):
                result["age_days"] = None
        else:
            result["age_days"] = None

        return result

    def _parse_date(self, date_str):
        """
        Parse a date string into ISO format.
        Returns ISO date string or None if parsing fails.
        """
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip()
        if not date_str:
            return None

        try:
            # Try dateutil parser (handles most formats)
            parsed = date_parser.parse(date_str, fuzzy=True)
            # Ensure timezone aware
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except (ParserError, ValueError, OverflowError):
            pass

        # Try HTTP date format (RFC 2822)
        try:
            parsed = parsedate_to_datetime(date_str)
            return parsed.isoformat()
        except (ValueError, TypeError):
            pass

        return None

    def _extract_dates_from_json_ld(self, json_ld_data, found_dates):
        """Extract dates from JSON-LD structured data."""
        date_fields = {
            'datePublished': 'published',
            'dateCreated': 'published',
            'dateModified': 'modified',
            'dateUpdated': 'modified',
            'uploadDate': 'published',  # For VideoObject
        }

        def search_json_ld(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return
            if isinstance(obj, dict):
                for field, date_type in date_fields.items():
                    if field in obj:
                        parsed = self._parse_date(obj[field])
                        if parsed:
                            found_dates[date_type].append({
                                "date": parsed,
                                "source": f"json-ld:{field}"
                            })
                for value in obj.values():
                    search_json_ld(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    search_json_ld(item, depth + 1)

        for item in json_ld_data:
            search_json_ld(item)

    def _extract_dates_from_og(self, soup, found_dates):
        """Extract dates from Open Graph article tags."""
        og_date_tags = [
            ('article:published_time', 'published'),
            ('article:published', 'published'),
            ('og:article:published_time', 'published'),
            ('article:modified_time', 'modified'),
            ('article:modified', 'modified'),
            ('og:article:modified_time', 'modified'),
            ('og:updated_time', 'modified'),
        ]

        for prop, date_type in og_date_tags:
            content = self._get_meta_property(soup, prop)
            if content:
                parsed = self._parse_date(content)
                if parsed:
                    found_dates[date_type].append({
                        "date": parsed,
                        "source": f"og:{prop}"
                    })

    def _extract_dates_from_meta(self, soup, found_dates):
        """Extract dates from various meta tags."""
        meta_date_tags = [
            # Published date meta tags
            ('date', 'published'),
            ('pubdate', 'published'),
            ('publish-date', 'published'),
            ('publish_date', 'published'),
            ('published-date', 'published'),
            ('article:published', 'published'),
            ('DC.date', 'published'),
            ('DC.date.issued', 'published'),
            ('dc.date', 'published'),
            ('dcterms.created', 'published'),
            ('sailthru.date', 'published'),
            ('cXenseParse:recs:publishtime', 'published'),
            # Modified date meta tags
            ('last-modified', 'modified'),
            ('lastmod', 'modified'),
            ('modified', 'modified'),
            ('revised', 'modified'),
            ('DC.date.modified', 'modified'),
            ('dcterms.modified', 'modified'),
        ]

        for name, date_type in meta_date_tags:
            content = self._get_meta_content(soup, name)
            if content:
                parsed = self._parse_date(content)
                if parsed:
                    found_dates[date_type].append({
                        "date": parsed,
                        "source": f"meta:{name}"
                    })

    def _extract_dates_from_headers(self, item, found_dates):
        """Extract dates from HTTP headers."""
        response_headers = item.get("response_headers", {})

        # Last-Modified header
        last_modified = response_headers.get("Last-Modified") or response_headers.get("last-modified")
        if last_modified:
            parsed = self._parse_date(last_modified)
            if parsed:
                found_dates["modified"].append({
                    "date": parsed,
                    "source": "header:Last-Modified"
                })

        # Date header (when response was generated, less useful but can indicate freshness)
        date_header = response_headers.get("Date") or response_headers.get("date")
        if date_header:
            parsed = self._parse_date(date_header)
            if parsed:
                found_dates["modified"].append({
                    "date": parsed,
                    "source": "header:Date"
                })

    def _extract_dates_from_time_elements(self, soup, found_dates):
        """Extract dates from HTML <time> elements."""
        time_elements = soup.find_all('time')

        for time_el in time_elements[:10]:  # Limit to first 10
            datetime_attr = time_el.get('datetime')
            if datetime_attr:
                parsed = self._parse_date(datetime_attr)
                if parsed:
                    # Try to determine if it's published or modified based on context
                    parent_classes = ' '.join(time_el.parent.get('class', []) if time_el.parent else []).lower()
                    el_classes = ' '.join(time_el.get('class', [])).lower()
                    itemprop = (time_el.get('itemprop') or '').lower()

                    if any(x in parent_classes + el_classes + itemprop for x in ['modified', 'updated', 'edit']):
                        date_type = 'modified'
                    else:
                        date_type = 'published'

                    found_dates[date_type].append({
                        "date": parsed,
                        "source": f"time[datetime]:{itemprop or 'element'}"
                    })

    def _extract_dates_from_html_patterns(self, soup, found_dates):
        """Extract dates from common HTML patterns."""
        # Common class names that often contain dates
        date_selectors = [
            # Published
            ('.published', 'published'),
            ('.post-date', 'published'),
            ('.entry-date', 'published'),
            ('.article-date', 'published'),
            ('.date-published', 'published'),
            ('.publish-date', 'published'),
            ('[itemprop="datePublished"]', 'published'),
            ('[data-date]', 'published'),
            # Modified
            ('.modified', 'modified'),
            ('.updated', 'modified'),
            ('.last-modified', 'modified'),
            ('.date-modified', 'modified'),
            ('[itemprop="dateModified"]', 'modified'),
        ]

        for selector, date_type in date_selectors:
            try:
                elements = soup.select(selector)
                for el in elements[:3]:  # Limit per selector
                    # Try datetime attribute first
                    date_str = el.get('datetime') or el.get('data-date') or el.get('content')
                    if not date_str:
                        # Fall back to text content
                        date_str = el.get_text(strip=True)

                    if date_str:
                        parsed = self._parse_date(date_str)
                        if parsed:
                            found_dates[date_type].append({
                                "date": parsed,
                                "source": f"html:{selector}"
                            })
                            break  # Only take first match per selector
            except Exception:
                continue  # Skip invalid selectors


class JsonFilePipeline:
    """
    Pipeline to save each item as a separate JSON file.

    Files are named based on URL hash for uniqueness.
    Output directory is configurable via CRAWL_OUTPUT_DIR setting.
    """

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)

    @classmethod
    def from_crawler(cls, crawler):
        output_dir = crawler.settings.get('CRAWL_OUTPUT_DIR', 'output')
        return cls(output_dir)

    def open_spider(self, spider):
        """Create output directory when spider starts."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        spider.logger.info(f"JSON output directory: {self.output_dir.absolute()}")

    def process_item(self, item, spider):
        """Save each item as a JSON file."""
        # Generate filename from URL hash
        url = item.get('url', '')
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
        filename = f"{url_hash}.json"
        filepath = self.output_dir / filename

        # Write JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(item, f, ensure_ascii=False, indent=2)

        spider.logger.debug(f"Saved: {filepath}")
        return item

    def close_spider(self, spider):
        """Log summary when spider closes."""
        file_count = len(list(self.output_dir.glob('*.json')))
        spider.logger.info(f"Crawl complete. {file_count} JSON files saved to {self.output_dir.absolute()}")


def serialize_item(item):
    """
    Serialize a crawl item to a clean JSON string.

    This function can be used standalone to serialize items.
    """
    return json.dumps(item, ensure_ascii=False, indent=2, default=str)


class ApiPipeline:
    """
    Pipeline to send crawl results to an API endpoint in batches.

    Requires spider to have:
    - api_url: The API endpoint URL
    - crawl_job_id: The crawl job ID
    - project_id: The project ID
    - api_key: The API key for authentication

    Results are batched and sent periodically to reduce API calls.
    """

    def __init__(self, api_url, crawl_job_id, project_id, api_key, batch_size=50):
        self.api_url = api_url
        self.crawl_job_id = crawl_job_id
        self.project_id = project_id
        self.api_key = api_key
        self.batch_size = batch_size
        self.items_buffer = []
        self.stats = {
            "pages_queued": 0,
            "pages_crawled": 0,
            "pages_errored": 0,
        }
        self._sent_running = False

    @classmethod
    def from_crawler(cls, crawler):
        api_url = crawler.settings.get('API_URL')
        crawl_job_id = crawler.settings.get('CRAWL_JOB_ID')
        project_id = crawler.settings.get('PROJECT_ID')
        api_key = crawler.settings.get('API_KEY')
        batch_size = crawler.settings.getint('API_BATCH_SIZE', 50)

        if not all([api_url, crawl_job_id, project_id, api_key]):
            raise ValueError(
                "ApiPipeline requires API_URL, CRAWL_JOB_ID, PROJECT_ID, and API_KEY settings"
            )

        return cls(api_url, crawl_job_id, project_id, api_key, batch_size)

    def open_spider(self, spider):
        """Send 'running' status when spider starts."""
        spider.logger.info(f"ApiPipeline: Starting crawl job {self.crawl_job_id}")
        self._send_batch(status="running")
        self._sent_running = True

    def process_item(self, item, spider):
        """Buffer items and send in batches."""
        # Convert item to API format (strip extra fields not needed)
        api_item = self._convert_to_api_format(item)
        self.items_buffer.append(api_item)

        # Track stats
        self.stats["pages_crawled"] += 1
        if item.get("error"):
            self.stats["pages_errored"] += 1

        # Send batch if buffer is full
        if len(self.items_buffer) >= self.batch_size:
            self._send_batch(status="running")
            self.items_buffer = []

        return item

    def close_spider(self, spider):
        """Send final batch with 'completed' status."""
        spider.logger.info(f"ApiPipeline: Completing crawl job {self.crawl_job_id}")

        # Determine status based on whether we crawled any pages successfully
        # Note: finish_reason is not set yet when close_spider is called
        # So we check if pages were actually crawled
        if self.stats["pages_crawled"] > 0:
            status = "completed"
            spider.logger.info(f"ApiPipeline: Crawl completed successfully ({self.stats['pages_crawled']} pages)")
        else:
            status = "failed"
            spider.logger.warning(f"ApiPipeline: Crawl failed - no pages crawled")

        # Send remaining items with final status
        self._send_batch(status=status)
        spider.logger.info(
            f"ApiPipeline: Sent {self.stats['pages_crawled']} pages "
            f"({self.stats['pages_errored']} errors)"
        )

    def _convert_to_api_format(self, item):
        """Convert pipeline item to API format with all fundamental fields."""
        return {
            # === CORE IDENTIFIERS ===
            "url": item.get("url", ""),
            "status_code": item.get("status_code"),
            "depth": item.get("depth", 0),
            "referrer": item.get("referrer"),
            "crawled_at": item.get("crawled_at"),

            # === PAGE METRICS ===
            "page_size_bytes": item.get("page_size_bytes", 0),
            "word_count": item.get("word_count", 0),
            "main_content_word_count": item.get("main_content_word_count", 0),

            # === CONTENT (for NLP/entity extraction) ===
            "body_text": item.get("body_text", ""),
            "main_content": item.get("main_content", ""),

            # === BASIC METADATA ===
            "metadata": {
                "title": item.get("metadata", {}).get("title"),
                "meta_description": item.get("metadata", {}).get("meta_description"),
                "h1": item.get("metadata", {}).get("h1"),
            },

            # === HEADING HIERARCHY ===
            "h2_tags": item.get("h2_tags", []),
            "h3_tags": item.get("h3_tags", []),

            # === SEO META TAGS ===
            "canonical_url": item.get("canonical_url"),
            "meta_robots": item.get("meta_robots"),
            "lang": item.get("lang"),
            "viewport": item.get("viewport"),
            "charset": item.get("charset"),

            # === SOCIAL META (Open Graph & Twitter) ===
            "og": item.get("og", {}),
            "twitter": item.get("twitter", {}),

            # === IMAGES ===
            "images": item.get("images", []),
            "images_count": item.get("images_count", 0),

            # === LINKS ===
            "internal_links": item.get("internal_links", []),
            "internal_links_count": item.get("internal_links_count", 0),
            "external_links": item.get("external_links", []),
            "external_links_count": item.get("external_links_count", 0),
            "link_locations": item.get("link_locations", {
                "nav": {"count": 0, "links": []},
                "header": {"count": 0, "links": []},
                "footer": {"count": 0, "links": []},
                "aside": {"count": 0, "links": []},
                "main": {"count": 0, "links": []},
            }),
            "anchor_analysis": item.get("anchor_analysis", {}),

            # === STRUCTURED DATA ===
            "json_ld": item.get("json_ld", []),
            "schema_types": item.get("schema_types", []),

            # === CONTENT AGE ===
            "content_age": item.get("content_age", {}),

            # === TECHNICAL ===
            "request_headers": item.get("request_headers", {}),
            "response_headers": item.get("response_headers", {}),
            "performance": {
                "download_latency_s": item.get("performance", {}).get("download_latency_s"),
                "timing": item.get("performance", {}).get("timing"),
            },
            "screenshot_path": item.get("screenshot_path"),
            "raw_html": item.get("raw_html", ""),
            "error": item.get("error"),

            # === GEO DATA (Generative Engine Optimization) ===
            "readability": item.get("readability", {}),
            "content_patterns": item.get("content_patterns", {}),
            "heading_analysis": item.get("heading_analysis", {}),
            "structure_elements": item.get("structure_elements", {}),
            "schema_analysis": item.get("schema_analysis", {}),
            "eeat_signals": item.get("eeat_signals", {}),
            "outbound_link_analysis": item.get("outbound_link_analysis", {}),
            "hreflang": item.get("hreflang", {}),
            "temporal_signals": item.get("temporal_signals", {}),
            "multimedia": item.get("multimedia", {}),
            "ai_crawlability": item.get("ai_crawlability", {}),
        }

    def _send_batch(self, status="running"):
        """Send batch of items to API."""
        import urllib.request
        import urllib.error

        payload = {
            "crawl_job_id": self.crawl_job_id,
            "project_id": self.project_id,
            "api_key": self.api_key,
            "status": status,
            "pages": self.items_buffer,
            "stats": self.stats.copy(),
        }

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'DumbCrawler/2.0',
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                if response_data.get("success"):
                    return True
                else:
                    print(f"API error: {response_data.get('error')}")
                    return False

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            print(f"HTTP error {e.code}: {error_body}")
            return False
        except urllib.error.URLError as e:
            print(f"URL error: {e.reason}")
            return False
        except Exception as e:
            print(f"Error sending batch to API: {e}")
            return False
