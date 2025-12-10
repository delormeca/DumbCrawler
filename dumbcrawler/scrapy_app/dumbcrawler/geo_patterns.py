"""
Compiled regex patterns for GEO (Generative Engine Optimization) extraction.
"""
import re

# =============================================================================
# QUESTION PATTERNS
# =============================================================================

# Detect questions in body text and headings
QUESTION_PATTERN = re.compile(
    r'\b(what|who|where|when|why|how|which|whose|whom|'
    r'can|could|would|should|will|does|do|did|is|are|was|were|'
    r'have|has|had|may|might|shall)'
    r'\s+[\w\s,\'-]+\?',
    re.IGNORECASE
)

# Questions that end with ? (simpler pattern for headings)
QUESTION_ENDING_PATTERN = re.compile(r'.+\?$')

# =============================================================================
# DEFINITION PATTERNS
# =============================================================================

# Identify definitions using common definitional phrases
DEFINITION_PATTERN = re.compile(
    r'\b(?:'
    r'(?:[\w\s]+)\s+(?:is|are|was|were)\s+(?:a|an|the)\s+[\w\s,]+'
    r'|(?:[\w\s]+)\s+refers?\s+to\s+[\w\s,]+'
    r'|(?:[\w\s]+)\s+means?\s+[\w\s,]+'
    r'|defined\s+as\s+[\w\s,]+'
    r'|(?:[\w\s]+)\s+(?:is|are)\s+defined\s+as\s+[\w\s,]+'
    r'|the\s+definition\s+of\s+[\w\s]+\s+is\s+[\w\s,]+'
    r')',
    re.IGNORECASE
)

# =============================================================================
# COMPARISON PATTERNS
# =============================================================================

# Find comparisons
COMPARISON_PATTERN = re.compile(
    r'\b(?:'
    r'[\w\s]+\s+vs\.?\s+[\w\s]+'
    r'|[\w\s]+\s+versus\s+[\w\s]+'
    r'|compared\s+to\s+[\w\s]+'
    r'|difference\s+between\s+[\w\s]+\s+and\s+[\w\s]+'
    r'|better\s+than\s+[\w\s]+'
    r'|worse\s+than\s+[\w\s]+'
    r'|pros\s+and\s+cons'
    r'|advantages\s+and\s+disadvantages'
    r'|[\w\s]+\s+or\s+[\w\s]+\?\s+which'
    r')',
    re.IGNORECASE
)

# =============================================================================
# STATISTICS PATTERNS
# =============================================================================

# Match percentages, dollar amounts, large numbers, ratios, multipliers
STATISTICS_PATTERN = re.compile(
    r'(?:'
    r'\d+(?:\.\d+)?%'  # Percentages: 50%, 3.5%
    r'|\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|billion|trillion|M|B|K))?'  # Dollar amounts
    r'|\d+(?:,\d{3})+(?:\.\d+)?'  # Large numbers with commas: 1,000,000
    r'|\d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)'  # Numbers with magnitude words
    r'|\d+(?:\.\d+)?x'  # Multipliers: 2x, 3.5x
    r'|\d+(?:\.\d+)?(?:\s*)?(?:to|:)(?:\s*)?\d+(?:\.\d+)?'  # Ratios: 3:1, 3 to 1
    r'|\d+\s+(?:out\s+of|in)\s+\d+'  # "3 out of 4", "1 in 5"
    r')',
    re.IGNORECASE
)

# =============================================================================
# CITATION PATTERNS
# =============================================================================

# Detect "according to", named sources, research references
CITATION_PATTERN = re.compile(
    r'(?:'
    r'according\s+to\s+[\w\s,\.]+'
    r'|(?:study|research|report|survey|analysis)\s+(?:by|from)\s+[\w\s,]+'
    r'|(?:published|reported)\s+(?:in|by)\s+[\w\s,]+'
    r'|(?:source|data):\s*[\w\s,]+'
    r'|\[\d+\]'  # Numbered citations [1], [2]
    r'|\(\d{4}\)'  # Year citations (2023)
    r'|et\s+al\.?'  # Academic et al.
    r')',
    re.IGNORECASE
)

# =============================================================================
# EXPERT PATTERNS
# =============================================================================

# Find credentials, expert quotes, titles, years of experience
EXPERT_PATTERN = re.compile(
    r'(?:'
    r'\bDr\.?\s+[\w]+'
    r'|\bPhD\b'
    r'|\bMD\b'
    r'|\bProfessor\s+[\w]+'
    r'|\bProf\.?\s+[\w]+'
    r'|\bCertified\b'
    r'|\bLicensed\b'
    r'|\d+\+?\s+years?\s+(?:of\s+)?experience'
    r'|expert\s+(?:in|on)\s+[\w\s]+'
    r'|specialist\s+(?:in|on)\s+[\w\s]+'
    r'|authored\s+by'
    r'|written\s+by'
    r')',
    re.IGNORECASE
)

# =============================================================================
# TEMPORAL PATTERNS
# =============================================================================

# Match years (19xx, 20xx)
YEAR_PATTERN = re.compile(r'\b(19\d{2}|20\d{2})\b')

# Relative time phrases
RELATIVE_TIME_PATTERN = re.compile(
    r'\b(?:'
    r'today|yesterday|tomorrow'
    r'|last\s+(?:week|month|year|decade)'
    r'|this\s+(?:week|month|year)'
    r'|next\s+(?:week|month|year)'
    r'|(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+'
    r'(?:days?|weeks?|months?|years?)\s+(?:ago|from\s+now|later)'
    r'|recently|currently|now|soon'
    r')',
    re.IGNORECASE
)

# "As of" statements
AS_OF_PATTERN = re.compile(
    r'\bas\s+of\s+[\w\s,\d]+',
    re.IGNORECASE
)

# Month-year references
MONTH_YEAR_PATTERN = re.compile(
    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December'
    r'|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{4}\b',
    re.IGNORECASE
)

# Outdated signals
OUTDATED_SIGNAL_PATTERN = re.compile(
    r'\b(?:'
    r'outdated|obsolete|deprecated|no\s+longer|was\s+discontinued'
    r'|used\s+to\s+be|formerly|previously|in\s+the\s+past'
    r')\b',
    re.IGNORECASE
)

# =============================================================================
# SEMANTIC TRIPLE PATTERNS
# =============================================================================

# Basic subject-predicate-object patterns
SEMANTIC_TRIPLE_PATTERN = re.compile(
    r'\b([\w\s]+)\s+(is|are|has|have|provides?|offers?|includes?|contains?|'
    r'enables?|allows?|supports?|requires?|uses?|creates?|generates?)\s+([\w\s]+)',
    re.IGNORECASE
)

# =============================================================================
# AUTHORITY DOMAINS
# =============================================================================

# Set of trusted domains
AUTHORITY_DOMAINS = {
    # Government
    '.gov',
    '.gov.uk',
    '.gov.au',
    '.gov.ca',
    '.mil',

    # Educational
    '.edu',
    '.ac.uk',
    '.edu.au',

    # Reference
    'wikipedia.org',
    'wikimedia.org',
    'britannica.com',
    'merriam-webster.com',
    'dictionary.com',

    # Major news sites
    'nytimes.com',
    'washingtonpost.com',
    'theguardian.com',
    'bbc.com',
    'bbc.co.uk',
    'reuters.com',
    'apnews.com',
    'cnn.com',
    'npr.org',
    'wsj.com',
    'economist.com',
    'forbes.com',
    'bloomberg.com',

    # Research databases
    'pubmed.gov',
    'ncbi.nlm.nih.gov',
    'nature.com',
    'science.org',
    'sciencedirect.com',
    'springer.com',
    'wiley.com',
    'jstor.org',
    'researchgate.net',
    'scholar.google.com',
    'arxiv.org',
    'doi.org',

    # Tech authority
    'developer.mozilla.org',
    'w3.org',
    'ietf.org',
    'iso.org',

    # Health authority
    'who.int',
    'cdc.gov',
    'nih.gov',
    'mayoclinic.org',
    'webmd.com',
    'healthline.com',
}

# =============================================================================
# TRUST PAGE PATTERNS
# =============================================================================

# Regex for trust page URLs
TRUST_PAGE_PATTERN = re.compile(
    r'(?:'
    r'/about(?:-us)?/?$'
    r'|/contact(?:-us)?/?$'
    r'|/privacy(?:-policy)?/?$'
    r'|/terms(?:-(?:of-service|and-conditions|of-use))?/?$'
    r'|/author/[\w-]+'
    r'|/team/?$'
    r'|/our-team/?$'
    r'|/editorial(?:-policy)?/?$'
    r'|/disclaimer/?$'
    r'|/legal/?$'
    r')',
    re.IGNORECASE
)

# =============================================================================
# EMAIL AND PHONE PATTERNS
# =============================================================================

EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

PHONE_PATTERN = re.compile(
    r'(?:'
    r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # US format
    r'|\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'  # International
    r')'
)
