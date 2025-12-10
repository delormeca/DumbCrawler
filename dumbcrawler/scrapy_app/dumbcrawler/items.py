"""
Scrapy Items for dumbcrawler with GEO (Generative Engine Optimization) audit fields.
"""
import scrapy


class DumbcrawlerItem(scrapy.Item):
    """
    Item representing a crawled page with comprehensive GEO audit data.
    Contains 60+ data points across 10 categories.
    """
    # =========================================================================
    # CORE IDENTIFIERS
    # =========================================================================
    client_id = scrapy.Field()
    crawl_job_id = scrapy.Field()
    url = scrapy.Field()
    crawled_at = scrapy.Field()  # ISO timestamp

    # =========================================================================
    # HTTP RESPONSE
    # =========================================================================
    status_code = scrapy.Field()  # int
    response_headers = scrapy.Field()  # dict
    depth = scrapy.Field()  # int
    referrer_url = scrapy.Field()  # str or None

    # =========================================================================
    # RAW CONTENT
    # =========================================================================
    raw_html = scrapy.Field()
    page_size_bytes = scrapy.Field()  # int

    # =========================================================================
    # PAGE METADATA
    # =========================================================================
    meta_title = scrapy.Field()
    meta_description = scrapy.Field()
    canonical_url = scrapy.Field()
    meta_robots = scrapy.Field()
    lang_attribute = scrapy.Field()
    hreflang = scrapy.Field()  # Dict from HreflangExtractor
    viewport = scrapy.Field()
    charset = scrapy.Field()

    # =========================================================================
    # HEADINGS
    # =========================================================================
    h1 = scrapy.Field()  # First H1 text
    h2_tags = scrapy.Field()  # List of H2 texts
    h3_tags = scrapy.Field()  # List of H3 texts
    heading_analysis = scrapy.Field()  # Dict from HeadingAnalysisExtractor

    # =========================================================================
    # CONTENT METRICS
    # =========================================================================
    word_count = scrapy.Field()  # int
    body_content = scrapy.Field()  # Plain text content
    markdown_content = scrapy.Field()  # Markdown conversion

    # =========================================================================
    # GEO EXTRACTION
    # =========================================================================
    readability = scrapy.Field()  # Dict from ReadabilityExtractor
    content_patterns = scrapy.Field()  # Dict from ContentPatternsExtractor
    structure_elements = scrapy.Field()  # Dict from StructureElementsExtractor

    # =========================================================================
    # SOCIAL METADATA
    # =========================================================================
    og_title = scrapy.Field()
    og_description = scrapy.Field()
    og_image = scrapy.Field()
    og_url = scrapy.Field()
    og_type = scrapy.Field()
    og_site_name = scrapy.Field()
    twitter_card = scrapy.Field()
    twitter_title = scrapy.Field()
    twitter_description = scrapy.Field()
    twitter_image = scrapy.Field()
    twitter_site = scrapy.Field()

    # =========================================================================
    # IMAGES
    # =========================================================================
    images_count = scrapy.Field()  # int
    images = scrapy.Field()  # List of dicts: src, alt, width, height

    # =========================================================================
    # LINKS
    # =========================================================================
    internal_links_count = scrapy.Field()  # int
    internal_links = scrapy.Field()  # List of dicts: url, anchor_text
    external_links_count = scrapy.Field()  # int
    external_links = scrapy.Field()  # List of dicts: url, anchor_text, nofollow
    outbound_link_analysis = scrapy.Field()  # Dict from LinkAnalysisExtractor
    link_health = scrapy.Field()  # Dict from BrokenLinkExtractor

    # =========================================================================
    # STRUCTURED DATA
    # =========================================================================
    json_ld = scrapy.Field()  # List of parsed JSON-LD blocks
    schema_types = scrapy.Field()  # List of @type values found
    schema_analysis = scrapy.Field()  # Dict from SchemaExtractor

    # =========================================================================
    # E-E-A-T & AUTHORITY
    # =========================================================================
    eeat_signals = scrapy.Field()  # Dict from EEATExtractor
    temporal_analysis = scrapy.Field()  # Dict from TemporalExtractor
    multimedia = scrapy.Field()  # Dict from MultimediaExtractor
    ai_crawlability = scrapy.Field()  # Dict from AICrawlabilityExtractor
