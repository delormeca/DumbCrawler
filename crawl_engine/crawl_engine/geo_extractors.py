"""
GEO (Generative Engine Optimization) Extractors.
Each extractor class has a static extract() method returning a dictionary.
"""
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen

import textstat
from bs4 import BeautifulSoup, Tag

from . import geo_patterns


class ReadabilityExtractor:
    """Extract readability metrics using textstat library."""

    @staticmethod
    def extract(text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                'flesch_reading_ease': None,
                'flesch_kincaid_grade': None,
                'gunning_fog': None,
                'smog_index': None,
                'automated_readability_index': None,
                'coleman_liau_index': None,
                'reading_time_minutes': 0,
                'sentence_count': 0,
                'avg_sentence_length': 0,
                'avg_word_length': 0,
                'syllable_count': 0,
                'difficult_words_count': 0,
                'difficult_words_percent': 0,
                'word_count': 0,
            }

        word_count = textstat.lexicon_count(text, removepunct=True)
        sentence_count = textstat.sentence_count(text)
        syllable_count = textstat.syllable_count(text)
        difficult_words = textstat.difficult_words(text)

        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        avg_word_length = syllable_count / word_count if word_count > 0 else 0
        difficult_words_percent = (difficult_words / word_count * 100) if word_count > 0 else 0

        reading_time_minutes = round(word_count / 225, 1)

        return {
            'flesch_reading_ease': textstat.flesch_reading_ease(text),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
            'gunning_fog': textstat.gunning_fog(text),
            'smog_index': textstat.smog_index(text),
            'automated_readability_index': textstat.automated_readability_index(text),
            'coleman_liau_index': textstat.coleman_liau_index(text),
            'reading_time_minutes': reading_time_minutes,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 2),
            'syllable_count': syllable_count,
            'difficult_words_count': difficult_words,
            'difficult_words_percent': round(difficult_words_percent, 1),
            'word_count': word_count,
        }


class ContentPatternsExtractor:
    """Extract content patterns using regex from geo_patterns."""

    @staticmethod
    def extract(text: str, soup: BeautifulSoup) -> Dict[str, Any]:
        result = {
            'questions_count': 0,
            'questions_examples': [],
            'question_headings_count': 0,
            'question_headings_examples': [],
            'definitions_count': 0,
            'definitions_examples': [],
            'comparisons_count': 0,
            'statistics_count': 0,
            'statistics_examples': [],
            'citations_count': 0,
            'citations_examples': [],
            'expert_mentions_count': 0,
            'semantic_triples_count': 0,
            'semantic_triples_examples': [],
        }

        if not text:
            return result

        questions = geo_patterns.QUESTION_PATTERN.findall(text)
        result['questions_count'] = len(questions)
        result['questions_examples'] = questions[:5]

        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(tag):
                heading_text = heading.get_text(strip=True)
                if geo_patterns.QUESTION_ENDING_PATTERN.match(heading_text):
                    result['question_headings_count'] += 1
                    if len(result['question_headings_examples']) < 5:
                        result['question_headings_examples'].append(heading_text)

        definitions = geo_patterns.DEFINITION_PATTERN.findall(text)
        result['definitions_count'] = len(definitions)
        result['definitions_examples'] = [d[:100] for d in definitions[:5]]

        comparisons = geo_patterns.COMPARISON_PATTERN.findall(text)
        result['comparisons_count'] = len(comparisons)

        statistics = geo_patterns.STATISTICS_PATTERN.findall(text)
        result['statistics_count'] = len(statistics)
        result['statistics_examples'] = statistics[:10]

        citations = geo_patterns.CITATION_PATTERN.findall(text)
        result['citations_count'] = len(citations)
        result['citations_examples'] = [c[:100] for c in citations[:5]]

        experts = geo_patterns.EXPERT_PATTERN.findall(text)
        result['expert_mentions_count'] = len(experts)

        triples = geo_patterns.SEMANTIC_TRIPLE_PATTERN.findall(text)
        result['semantic_triples_count'] = len(triples)
        result['semantic_triples_examples'] = [
            f"{t[0].strip()} {t[1]} {t[2].strip()}"[:80]
            for t in triples[:5]
        ]

        return result


class HeadingAnalysisExtractor:
    """Analyze heading structure from BeautifulSoup."""

    @staticmethod
    def extract(soup: BeautifulSoup) -> Dict[str, Any]:
        headings = []
        counts = {'h1': 0, 'h2': 0, 'h3': 0, 'h4': 0, 'h5': 0, 'h6': 0}
        hierarchy_issues = []

        prev_level = 0
        has_h1 = False

        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(tag):
                text = heading.get_text(strip=True)
                level = int(tag[1])
                word_count = len(text.split())

                headings.append({
                    'level': level,
                    'tag': tag,
                    'text': text[:200],
                    'word_count': word_count,
                })

                counts[tag] += 1

                if level == 1:
                    has_h1 = True

        ordered_headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            level = int(heading.name[1])
            ordered_headings.append({
                'level': level,
                'tag': heading.name,
                'text': text[:200],
                'word_count': len(text.split()),
            })

        if not has_h1:
            hierarchy_issues.append('missing_h1')

        if counts['h1'] > 1:
            hierarchy_issues.append('multiple_h1')

        prev_level = 0
        for h in ordered_headings:
            if h['level'] > prev_level + 1 and prev_level > 0:
                hierarchy_issues.append(f"skipped_level_h{prev_level}_to_h{h['level']}")
            prev_level = h['level']

        total_words = sum(h['word_count'] for h in ordered_headings)
        avg_length = round(total_words / len(ordered_headings), 1) if ordered_headings else 0

        return {
            'headings': ordered_headings,
            'h1_count': counts['h1'],
            'h2_count': counts['h2'],
            'h3_count': counts['h3'],
            'h4_count': counts['h4'],
            'h5_count': counts['h5'],
            'h6_count': counts['h6'],
            'total_headings': len(ordered_headings),
            'hierarchy_issues': list(set(hierarchy_issues)),
            'avg_heading_length': avg_length,
        }


class StructureElementsExtractor:
    """Extract structural elements from HTML."""

    @staticmethod
    def extract(soup: BeautifulSoup) -> Dict[str, Any]:
        ordered_lists = soup.find_all('ol')
        unordered_lists = soup.find_all('ul')
        total_list_items = len(soup.find_all('li'))

        tables = soup.find_all('table')
        table_details = []
        for table in tables[:10]:
            rows = len(table.find_all('tr'))
            cells = len(table.find_all(['td', 'th']))
            has_header = bool(table.find('thead') or table.find('th'))
            caption = table.find('caption')
            table_details.append({
                'rows': rows,
                'cells': cells,
                'has_header': has_header,
                'caption': caption.get_text(strip=True)[:100] if caption else None,
            })

        blockquotes = soup.find_all('blockquote')
        blockquote_samples = [
            bq.get_text(strip=True)[:200] for bq in blockquotes[:5]
        ]

        pre_tags = soup.find_all('pre')
        inline_code = soup.find_all('code')
        inline_code_count = sum(
            1 for code in inline_code
            if not code.find_parent('pre')
        )

        dl_tags = soup.find_all('dl')
        dt_tags = soup.find_all('dt')

        details_tags = soup.find_all('details')

        figures = soup.find_all('figure')
        figures_with_caption = sum(
            1 for fig in figures if fig.find('figcaption')
        )

        return {
            'ordered_lists_count': len(ordered_lists),
            'unordered_lists_count': len(unordered_lists),
            'total_list_items': total_list_items,
            'tables_count': len(tables),
            'table_details': table_details,
            'blockquotes_count': len(blockquotes),
            'blockquote_samples': blockquote_samples,
            'pre_code_blocks_count': len(pre_tags),
            'inline_code_count': inline_code_count,
            'definition_lists_count': len(dl_tags),
            'definition_terms_count': len(dt_tags),
            'accordions_count': len(details_tags),
            'figures_count': len(figures),
            'figures_with_caption_count': figures_with_caption,
        }


class SchemaExtractor:
    """Parse JSON-LD structured data."""

    @staticmethod
    def extract(soup: BeautifulSoup) -> Dict[str, Any]:
        import json

        result = {
            'json_ld_blocks': [],
            'schema_types': [],
            'has_faq_schema': False,
            'has_howto_schema': False,
            'has_article_schema': False,
            'has_person_schema': False,
            'has_organization_schema': False,
            'has_product_schema': False,
            'has_breadcrumb_schema': False,
            'has_webpage_schema': False,
            'schema_author': None,
            'schema_date_published': None,
            'schema_date_modified': None,
            'schema_date_created': None,
        }

        json_ld_scripts = soup.find_all('script', type='application/ld+json')

        all_types = set()
        dates = {}

        for script in json_ld_scripts:
            try:
                content = script.string
                if not content:
                    continue

                data = json.loads(content)
                result['json_ld_blocks'].append(data)

                SchemaExtractor._extract_types_and_data(
                    data, all_types, dates, result
                )

            except (json.JSONDecodeError, TypeError):
                continue

        result['schema_types'] = list(all_types)

        type_lower = {t.lower() for t in all_types}
        result['has_faq_schema'] = 'faqpage' in type_lower
        result['has_howto_schema'] = 'howto' in type_lower
        result['has_article_schema'] = any(
            t in type_lower for t in ['article', 'newsarticle', 'blogposting']
        )
        result['has_person_schema'] = 'person' in type_lower
        result['has_organization_schema'] = 'organization' in type_lower
        result['has_product_schema'] = 'product' in type_lower
        result['has_breadcrumb_schema'] = 'breadcrumblist' in type_lower
        result['has_webpage_schema'] = 'webpage' in type_lower

        result['schema_date_published'] = dates.get('datePublished')
        result['schema_date_modified'] = dates.get('dateModified')
        result['schema_date_created'] = dates.get('dateCreated')

        return result

    @staticmethod
    def _extract_types_and_data(
        data: Any,
        types: set,
        dates: dict,
        result: dict
    ) -> None:
        """Recursively extract @type values and metadata from JSON-LD."""
        if isinstance(data, dict):
            if '@type' in data:
                type_val = data['@type']
                if isinstance(type_val, list):
                    types.update(type_val)
                else:
                    types.add(type_val)

            if 'author' in data and result['schema_author'] is None:
                author = data['author']
                if isinstance(author, dict):
                    result['schema_author'] = author.get('name')
                elif isinstance(author, str):
                    result['schema_author'] = author

            for date_key in ['datePublished', 'dateModified', 'dateCreated']:
                if date_key in data and date_key not in dates:
                    dates[date_key] = data[date_key]

            for value in data.values():
                SchemaExtractor._extract_types_and_data(value, types, dates, result)

        elif isinstance(data, list):
            for item in data:
                SchemaExtractor._extract_types_and_data(item, types, dates, result)


class EEATExtractor:
    """Extract E-E-A-T (Experience, Expertise, Authoritativeness, Trust) signals."""

    @staticmethod
    def extract(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        result = {
            'author_name': None,
            'author_url': None,
            'published_date': None,
            'modified_date': None,
            'has_about_page_link': False,
            'has_contact_page_link': False,
            'has_privacy_page_link': False,
            'has_terms_page_link': False,
            'has_author_page_link': False,
            'trust_page_links': [],
            'has_email': False,
            'has_phone': False,
            'has_address': False,
            'credentials_found': [],
        }

        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            result['author_name'] = author_meta.get('content', '').strip()

        author_link = soup.find('a', attrs={'rel': 'author'})
        if author_link:
            if not result['author_name']:
                result['author_name'] = author_link.get_text(strip=True)
            result['author_url'] = author_link.get('href')

        author_classes = ['author', 'byline', 'post-author', 'entry-author']
        for cls in author_classes:
            author_elem = soup.find(class_=re.compile(cls, re.I))
            if author_elem and not result['author_name']:
                result['author_name'] = author_elem.get_text(strip=True)[:100]
                break

        time_elem = soup.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                result['published_date'] = datetime_attr

        date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_meta:
            result['published_date'] = date_meta.get('content')

        modified_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
        if modified_meta:
            result['modified_date'] = modified_meta.get('content')

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            href_lower = href.lower()

            if geo_patterns.TRUST_PAGE_PATTERN.search(href):
                result['trust_page_links'].append(href)

            if '/about' in href_lower:
                result['has_about_page_link'] = True
            if '/contact' in href_lower:
                result['has_contact_page_link'] = True
            if '/privacy' in href_lower:
                result['has_privacy_page_link'] = True
            if '/terms' in href_lower or '/tos' in href_lower:
                result['has_terms_page_link'] = True
            if '/author/' in href_lower:
                result['has_author_page_link'] = True

        page_text = soup.get_text()

        if geo_patterns.EMAIL_PATTERN.search(page_text):
            result['has_email'] = True

        if geo_patterns.PHONE_PATTERN.search(page_text):
            result['has_phone'] = True

        if soup.find('address'):
            result['has_address'] = True

        credentials = geo_patterns.EXPERT_PATTERN.findall(page_text)
        result['credentials_found'] = list(set(credentials[:10]))

        return result


class LinkAnalysisExtractor:
    """Analyze outbound links."""

    @staticmethod
    def extract(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        result = {
            'outbound_links': [],
            'total_outbound_count': 0,
            'authority_links': [],
            'authority_links_count': 0,
            'gov_edu_links_count': 0,
            'wikipedia_links_count': 0,
            'unique_domains_count': 0,
            'nofollow_count': 0,
            'nofollow_ratio': 0,
        }

        try:
            base_domain = urlparse(base_url).netloc.lower()
        except Exception:
            base_domain = ''

        seen_domains = set()
        outbound_links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            if not href.startswith(('http://', 'https://')):
                continue

            try:
                parsed = urlparse(href)
                domain = parsed.netloc.lower()
            except Exception:
                continue

            if domain == base_domain or domain.endswith('.' + base_domain):
                continue

            rel = link.get('rel', [])
            if isinstance(rel, str):
                rel = [rel]

            nofollow = 'nofollow' in rel
            sponsored = 'sponsored' in rel
            ugc = 'ugc' in rel

            anchor_text = link.get_text(strip=True)[:200]

            link_info = {
                'url': href[:500],
                'domain': domain,
                'anchor_text': anchor_text,
                'nofollow': nofollow,
                'sponsored': sponsored,
                'ugc': ugc,
            }

            outbound_links.append(link_info)
            seen_domains.add(domain)

            is_authority = LinkAnalysisExtractor._is_authority_domain(domain)
            if is_authority:
                result['authority_links'].append(link_info)

            if '.gov' in domain or '.edu' in domain:
                result['gov_edu_links_count'] += 1

            if 'wikipedia.org' in domain:
                result['wikipedia_links_count'] += 1

            if nofollow:
                result['nofollow_count'] += 1

        result['outbound_links'] = outbound_links
        result['total_outbound_count'] = len(outbound_links)
        result['authority_links_count'] = len(result['authority_links'])
        result['unique_domains_count'] = len(seen_domains)

        if result['total_outbound_count'] > 0:
            result['nofollow_ratio'] = round(
                result['nofollow_count'] / result['total_outbound_count'], 2
            )

        return result

    @staticmethod
    def _is_authority_domain(domain: str) -> bool:
        """Check if domain is in authority list."""
        domain_lower = domain.lower()

        for auth_domain in geo_patterns.AUTHORITY_DOMAINS:
            if auth_domain.startswith('.'):
                if domain_lower.endswith(auth_domain):
                    return True
            else:
                if domain_lower == auth_domain or domain_lower.endswith('.' + auth_domain):
                    return True

        return False


class BrokenLinkExtractor:
    """Check sampled links for broken statuses as a content decay signal."""

    @staticmethod
    def extract(
        soup: BeautifulSoup,
        base_url: str,
        max_links: int = 20,
        timeout: int = 5,
    ) -> Dict[str, Any]:
        result = {
            'checked_links_count': 0,
            'broken_links_count': 0,
            'broken_links': [],
            'sampled_links': [],
        }

        seen = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            href_lower = href.lower()

            if href_lower.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            full_url = urljoin(base_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)

            status, reason = BrokenLinkExtractor._check_url(full_url, timeout)
            result['checked_links_count'] += 1
            result['sampled_links'].append({
                'url': full_url[:500],
                'status': status,
                'reason': reason[:200] if isinstance(reason, str) else reason,
            })

            if status is None or status >= 400:
                result['broken_links'].append({
                    'url': full_url[:500],
                    'status': status,
                    'reason': reason[:200] if isinstance(reason, str) else reason,
                })

            if result['checked_links_count'] >= max_links:
                break

        result['broken_links_count'] = len(result['broken_links'])
        return result

    @staticmethod
    def _check_url(url: str, timeout: int) -> Tuple[Optional[int], Optional[str]]:
        """HEAD request to detect obvious breakage."""
        headers = {'User-Agent': 'crawl_engine/1.0'}
        try:
            req = Request(url, method='HEAD', headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                return getattr(resp, 'status', None), None
        except HTTPError as e:
            if getattr(e, 'code', None) == 405:
                try:
                    req_get = Request(url, method='GET', headers=headers)
                    with urlopen(req_get, timeout=timeout) as resp:
                        return getattr(resp, 'status', None), None
                except Exception:
                    pass
            return getattr(e, 'code', None), getattr(e, 'reason', str(e))
        except URLError as e:
            return None, getattr(e, 'reason', str(e))
        except Exception as e:
            return None, str(e)


class HreflangExtractor:
    """Extract hreflang alternate links."""

    @staticmethod
    def extract(soup: BeautifulSoup) -> Dict[str, Any]:
        tags = []
        values = set()

        for link in soup.find_all('link', attrs={'rel': re.compile(r'\balternate\b', re.I)}):
            href = (link.get('href') or '').strip()
            hreflang = (link.get('hreflang') or '').strip()

            if not href or not hreflang:
                continue

            hreflang_value = hreflang.lower()
            tags.append({
                'hreflang': hreflang_value,
                'href': href[:500],
            })
            values.add(hreflang_value)

        return {
            'hreflang_tags': tags,
            'hreflang_count': len(tags),
            'unique_hreflang_values': sorted(values),
            'has_x_default': 'x-default' in values,
        }


class TemporalExtractor:
    """Analyze temporal signals in content."""

    @staticmethod
    def extract(
        text: str,
        published_date: Optional[str] = None,
        modified_date: Optional[str] = None,
        http_last_modified: Optional[str] = None
    ) -> Dict[str, Any]:
        current_year = datetime.now().year
        last_year = current_year - 1

        result = {
            'years_mentioned': [],
            'most_recent_year': None,
            'oldest_year': None,
            'has_current_year': False,
            'has_last_year': False,
            'relative_time_phrases': [],
            'as_of_statements': [],
            'month_year_references': [],
            'outdated_signals_count': 0,
            'content_age_days': None,
            'last_update_age_days': None,
            'http_last_modified': http_last_modified,
            'http_last_modified_age_days': None,
        }

        if not text:
            return result

        years = [int(y) for y in geo_patterns.YEAR_PATTERN.findall(text)]
        years = sorted(set(years))
        result['years_mentioned'] = years

        if years:
            result['most_recent_year'] = max(years)
            result['oldest_year'] = min(years)
            result['has_current_year'] = current_year in years
            result['has_last_year'] = last_year in years

        relative_phrases = geo_patterns.RELATIVE_TIME_PATTERN.findall(text)
        result['relative_time_phrases'] = list(set(relative_phrases[:10]))

        as_of = geo_patterns.AS_OF_PATTERN.findall(text)
        result['as_of_statements'] = [s[:100] for s in as_of[:5]]

        month_year = geo_patterns.MONTH_YEAR_PATTERN.findall(text)
        result['month_year_references'] = list(set(month_year[:10]))

        outdated = geo_patterns.OUTDATED_SIGNAL_PATTERN.findall(text)
        result['outdated_signals_count'] = len(outdated)

        if published_date:
            result['content_age_days'] = TemporalExtractor._calculate_age_days(published_date)

        if modified_date:
            result['last_update_age_days'] = TemporalExtractor._calculate_age_days(modified_date)

        if http_last_modified:
            result['http_last_modified_age_days'] = TemporalExtractor._calculate_age_days(
                http_last_modified, http_format=True
            )

        return result

    @staticmethod
    def _calculate_age_days(date_str: str, http_format: bool = False) -> Optional[int]:
        from email.utils import parsedate_to_datetime

        try:
            if http_format:
                parsed_date = parsedate_to_datetime(date_str)
            else:
                parsed_date = datetime.fromisoformat(
                    date_str.replace('Z', '+00:00')
                )

            now = datetime.now(parsed_date.tzinfo) if parsed_date.tzinfo else datetime.now()
            age = now - parsed_date
            return max(0, age.days)
        except (ValueError, TypeError, AttributeError):
            return None


class MultimediaExtractor:
    """Extract multimedia elements from HTML."""

    @staticmethod
    def extract(soup: BeautifulSoup) -> Dict[str, Any]:
        result = {
            'videos': [],
            'video_count': 0,
            'has_video': False,
            'audio': [],
            'audio_count': 0,
            'has_audio': False,
            'pdfs': [],
            'pdf_count': 0,
            'has_pdf': False,
            'infographics': [],
            'infographic_count': 0,
        }

        videos = []

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '') or iframe.get('data-src', '')
            if any(domain in src.lower() for domain in
                   ['youtube.com', 'youtu.be', 'vimeo.com', 'wistia.com', 'wistia.net']):
                videos.append({
                    'type': 'iframe',
                    'src': src[:500],
                    'platform': MultimediaExtractor._detect_video_platform(src),
                })

        for video in soup.find_all('video'):
            src = video.get('src', '')
            source = video.find('source')
            if source:
                src = source.get('src', src)
            if src:
                videos.append({
                    'type': 'html5_video',
                    'src': src[:500],
                    'platform': 'native',
                })

        result['videos'] = videos
        result['video_count'] = len(videos)
        result['has_video'] = len(videos) > 0

        audio = []

        for audio_tag in soup.find_all('audio'):
            src = audio_tag.get('src', '')
            source = audio_tag.find('source')
            if source:
                src = source.get('src', src)
            if src:
                audio.append({
                    'type': 'html5_audio',
                    'src': src[:500],
                    'platform': 'native',
                })

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '') or iframe.get('data-src', '')
            if any(domain in src.lower() for domain in
                   ['spotify.com', 'podcasts.apple.com', 'anchor.fm', 'soundcloud.com']):
                audio.append({
                    'type': 'iframe',
                    'src': src[:500],
                    'platform': MultimediaExtractor._detect_audio_platform(src),
                })

        result['audio'] = audio
        result['audio_count'] = len(audio)
        result['has_audio'] = len(audio) > 0

        pdfs = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.lower().endswith('.pdf'):
                pdfs.append({
                    'url': href[:500],
                    'anchor_text': link.get_text(strip=True)[:100],
                })

        result['pdfs'] = pdfs
        result['pdf_count'] = len(pdfs)
        result['has_pdf'] = len(pdfs) > 0

        infographics = []
        infographic_keywords = ['infographic', 'chart', 'diagram', 'graph', 'visualization']

        for img in soup.find_all('img'):
            alt = img.get('alt', '').lower()
            src = (img.get('src', '') or img.get('data-src', '')).lower()

            if any(kw in alt or kw in src for kw in infographic_keywords):
                infographics.append({
                    'src': img.get('src', img.get('data-src', ''))[:500],
                    'alt': img.get('alt', '')[:200],
                })

        result['infographics'] = infographics
        result['infographic_count'] = len(infographics)

        return result

    @staticmethod
    def _detect_video_platform(src: str) -> str:
        src_lower = src.lower()
        if 'youtube' in src_lower or 'youtu.be' in src_lower:
            return 'youtube'
        if 'vimeo' in src_lower:
            return 'vimeo'
        if 'wistia' in src_lower:
            return 'wistia'
        return 'unknown'

    @staticmethod
    def _detect_audio_platform(src: str) -> str:
        src_lower = src.lower()
        if 'spotify' in src_lower:
            return 'spotify'
        if 'apple' in src_lower:
            return 'apple_podcasts'
        if 'anchor' in src_lower:
            return 'anchor'
        if 'soundcloud' in src_lower:
            return 'soundcloud'
        return 'unknown'


class AICrawlabilityExtractor:
    """Analyze AI crawler accessibility."""

    @staticmethod
    def extract(soup: BeautifulSoup, raw_html: str) -> Dict[str, Any]:
        result = {
            'content_ratio': 0,
            'html_size_bytes': 0,
            'text_size_bytes': 0,
            'inline_scripts_count': 0,
            'external_scripts_count': 0,
            'total_scripts_count': 0,
            'has_noscript_content': False,
            'meta_robots': None,
            'iframe_count': 0,
            'lazy_images_count': 0,
            'data_src_images_count': 0,
            'custom_elements_count': 0,
            'canvas_elements_count': 0,
            'js_framework_signals': [],
        }

        html_size = len(raw_html.encode('utf-8')) if raw_html else 0
        text = soup.get_text()
        text_size = len(text.encode('utf-8')) if text else 0

        result['html_size_bytes'] = html_size
        result['text_size_bytes'] = text_size
        result['content_ratio'] = round(text_size / html_size, 3) if html_size > 0 else 0

        scripts = soup.find_all('script')
        inline_count = 0
        external_count = 0

        for script in scripts:
            if script.get('src'):
                external_count += 1
            elif script.string:
                inline_count += 1

        result['inline_scripts_count'] = inline_count
        result['external_scripts_count'] = external_count
        result['total_scripts_count'] = len(scripts)

        noscript_tags = soup.find_all('noscript')
        result['has_noscript_content'] = any(
            ns.get_text(strip=True) for ns in noscript_tags
        )

        meta_robots = soup.find('meta', attrs={'name': re.compile(r'^robots$', re.I)})
        if meta_robots:
            result['meta_robots'] = meta_robots.get('content', '')

        result['iframe_count'] = len(soup.find_all('iframe'))

        lazy_images = 0
        data_src_images = 0

        for img in soup.find_all('img'):
            if img.get('loading') == 'lazy':
                lazy_images += 1
            if img.get('data-src') and not img.get('src'):
                data_src_images += 1

        result['lazy_images_count'] = lazy_images
        result['data_src_images_count'] = data_src_images

        custom_elements = 0
        for tag in soup.find_all():
            if '-' in tag.name:
                custom_elements += 1

        result['custom_elements_count'] = custom_elements

        result['canvas_elements_count'] = len(soup.find_all('canvas'))

        frameworks = []

        if soup.find(attrs={'ng-app': True}) or soup.find(attrs={'ng-controller': True}):
            frameworks.append('angular')

        if soup.find(attrs={'data-reactroot': True}) or soup.find(attrs={'data-reactid': True}):
            frameworks.append('react')

        if soup.find(attrs={'data-v-': re.compile(r'.*')}) or soup.find(attrs={'v-bind': True}):
            frameworks.append('vue')

        if soup.find(attrs={'data-ember-action': True}):
            frameworks.append('ember')

        for script in soup.find_all('script', src=True):
            src = script.get('src', '').lower()
            if 'react' in src:
                frameworks.append('react')
            if 'angular' in src:
                frameworks.append('angular')
            if 'vue' in src:
                frameworks.append('vue')
            if 'jquery' in src:
                frameworks.append('jquery')
            if 'next' in src:
                frameworks.append('nextjs')
            if 'nuxt' in src:
                frameworks.append('nuxt')

        result['js_framework_signals'] = list(set(frameworks))

        return result
