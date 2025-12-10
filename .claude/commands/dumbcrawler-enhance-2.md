#@title Enhanced Delorme Entities Extractor with JINA AI & DataForSEO { vertical-output: true }
import requests
import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import base64
import json
import time
from urllib.parse import urlparse

# ========== UI COMPONENTS ==========

# Mode selection
mode_selector = widgets.RadioButtons(
    options=[
        ('1. Analyze my content only', 'content_only'),
        ('2. Analyze my content + benchmark competitors', 'content_benchmark'),
        ('3. 1-on-1 comparison', 'url_analysis')
    ],
    description='Mode:',
    layout=widgets.Layout(width='100%'),
    style={'description_width': '100px'}
)

# API Keys section
api_keys_label = widgets.HTML('<h3>API Credentials</h3>')
google_nlp_key = widgets.Password(
    description='Google NLP API Key:', 
    placeholder='Your Google NLP API Key', 
    layout=widgets.Layout(width='80%'),
    style={'description_width': '150px'}
)
jina_api_key = widgets.Password(
    description='JINA AI API Key:', 
    placeholder='Your JINA AI API Key', 
    layout=widgets.Layout(width='80%'),
    style={'description_width': '150px'}
)
dataforseo_login = widgets.Text(
    description='DataForSEO Login:', 
    placeholder='your@email.com', 
    layout=widgets.Layout(width='80%'),
    style={'description_width': '150px'}
)
dataforseo_password = widgets.Password(
    description='DataForSEO Password:', 
    placeholder='Your DataForSEO Password', 
    layout=widgets.Layout(width='80%'),
    style={'description_width': '150px'}
)

# Content input section
content_label = widgets.HTML('<h3>Your Content</h3>')
content_source = widgets.RadioButtons(
    options=[('Paste content', 'paste'), ('Scrape with JINA AI', 'scrape')],
    description='Source:',
    layout=widgets.Layout(width='50%'),
    style={'description_width': '100px'}
)
content_input = widgets.Textarea(
    description='Content/URL:', 
    placeholder='Paste your content here OR enter URL to scrape', 
    layout=widgets.Layout(width='80%', height='200px'),
    style={'description_width': '100px'}
)

# Content display area for JINA scraping
content_display = widgets.Textarea(
    description='Scraped Content:', 
    placeholder='JINA AI scraped content will appear here', 
    layout=widgets.Layout(width='90%', height='200px'),
    style={'description_width': '120px'},
    disabled=True
)

# Benchmark settings (for mode 2)
benchmark_label = widgets.HTML('<h3>Benchmark Settings</h3>')
benchmark_keyword = widgets.Text(
    description='Keyword:', 
    placeholder='Enter keyword to search', 
    layout=widgets.Layout(width='80%'),
    style={'description_width': '150px'}
)

# All available location/language combinations from DataForSEO
LOCATION_PRESETS = {
    # Popular/Common selections first
    '🌟 USA - English': {'location_code': 2840, 'language_code': 'en', 'se_domain': 'google.com'},
    '🌟 UK - English': {'location_code': 2826, 'language_code': 'en', 'se_domain': 'google.co.uk'},
    '🌟 Canada - English': {'location_code': 2124, 'language_code': 'en', 'se_domain': 'google.ca'},
    '🌟 Canada - French': {'location_code': 2124, 'language_code': 'fr', 'se_domain': 'google.ca'},
    '🌟 France - French': {'location_code': 2250, 'language_code': 'fr', 'se_domain': 'google.fr'},
    '🌟 Germany - German': {'location_code': 2276, 'language_code': 'de', 'se_domain': 'google.de'},
    '🌟 Spain - Spanish': {'location_code': 2724, 'language_code': 'es', 'se_domain': 'google.es'},
    '🌟 Italy - Italian': {'location_code': 2380, 'language_code': 'it', 'se_domain': 'google.it'},
    '🌟 Brazil - Portuguese': {'location_code': 2076, 'language_code': 'pt', 'se_domain': 'google.com.br'},
    '🌟 Mexico - Spanish': {'location_code': 2484, 'language_code': 'es', 'se_domain': 'google.com.mx'},
    '🌟 Australia - English': {'location_code': 2036, 'language_code': 'en', 'se_domain': 'google.com.au'},
    # All other locations alphabetically
    'Algeria - Arabic': {'location_code': 2012, 'language_code': 'ar', 'se_domain': 'google.dz'},
    'Algeria - French': {'location_code': 2012, 'language_code': 'fr', 'se_domain': 'google.dz'},
    'Angola - Portuguese': {'location_code': 2024, 'language_code': 'pt', 'se_domain': 'google.co.ao'},
    'Argentina - Spanish': {'location_code': 2032, 'language_code': 'es', 'se_domain': 'google.com.ar'},
    'Armenia - Armenian': {'location_code': 2051, 'language_code': 'hy', 'se_domain': 'google.am'},
    'Austria - German': {'location_code': 2040, 'language_code': 'de', 'se_domain': 'google.at'},
    'Azerbaijan - Azeri': {'location_code': 2031, 'language_code': 'az', 'se_domain': 'google.az'},
    'Bahrain - Arabic': {'location_code': 2048, 'language_code': 'ar', 'se_domain': 'google.com.bh'},
    'Bangladesh - Bengali': {'location_code': 2050, 'language_code': 'bn', 'se_domain': 'google.com.bd'},
    'Belgium - Dutch': {'location_code': 2056, 'language_code': 'nl', 'se_domain': 'google.be'},
    'Belgium - French': {'location_code': 2056, 'language_code': 'fr', 'se_domain': 'google.be'},
    'Belgium - German': {'location_code': 2056, 'language_code': 'de', 'se_domain': 'google.be'},
    'Bolivia - Spanish': {'location_code': 2068, 'language_code': 'es', 'se_domain': 'google.com.bo'},
    'Bosnia and Herzegovina - Bosnian': {'location_code': 2070, 'language_code': 'bs', 'se_domain': 'google.ba'},
    'Bulgaria - Bulgarian': {'location_code': 2100, 'language_code': 'bg', 'se_domain': 'google.bg'},
    'Burkina Faso - French': {'location_code': 2854, 'language_code': 'fr', 'se_domain': 'google.bf'},
    'Cambodia - English': {'location_code': 2116, 'language_code': 'en', 'se_domain': 'google.com.kh'},
    'Cameroon - French': {'location_code': 2120, 'language_code': 'fr', 'se_domain': 'google.cm'},
    'Chile - Spanish': {'location_code': 2152, 'language_code': 'es', 'se_domain': 'google.cl'},
    'Colombia - Spanish': {'location_code': 2170, 'language_code': 'es', 'se_domain': 'google.com.co'},
    'Costa Rica - Spanish': {'location_code': 2188, 'language_code': 'es', 'se_domain': 'google.co.cr'},
    "Cote d'Ivoire - French": {'location_code': 2384, 'language_code': 'fr', 'se_domain': 'google.ci'},
    'Croatia - Croatian': {'location_code': 2191, 'language_code': 'hr', 'se_domain': 'google.hr'},
    'Cyprus - English': {'location_code': 2196, 'language_code': 'en', 'se_domain': 'google.com.cy'},
    'Cyprus - Greek': {'location_code': 2196, 'language_code': 'el', 'se_domain': 'google.com.cy'},
    'Czechia - Czech': {'location_code': 2203, 'language_code': 'cs', 'se_domain': 'google.cz'},
    'Denmark - Danish': {'location_code': 2208, 'language_code': 'da', 'se_domain': 'google.dk'},
    'Dominican Republic - Spanish': {'location_code': 2214, 'language_code': 'es', 'se_domain': 'google.com.do'},
    'Ecuador - Spanish': {'location_code': 2218, 'language_code': 'es', 'se_domain': 'google.com.ec'},
    'Egypt - Arabic': {'location_code': 2818, 'language_code': 'ar', 'se_domain': 'google.com.eg'},
    'Egypt - English': {'location_code': 2818, 'language_code': 'en', 'se_domain': 'google.com.eg'},
    'El Salvador - Spanish': {'location_code': 2222, 'language_code': 'es', 'se_domain': 'google.com.sv'},
    'Estonia - Estonian': {'location_code': 2233, 'language_code': 'et', 'se_domain': 'google.ee'},
    'Ethiopia - Amharic': {'location_code': 2231, 'language_code': 'am', 'se_domain': 'google.com.et'},
    'Finland - Finnish': {'location_code': 2246, 'language_code': 'fi', 'se_domain': 'google.fi'},
    'Georgia - Georgian': {'location_code': 2268, 'language_code': 'ka', 'se_domain': 'google.ge'},
    'Ghana - English': {'location_code': 2288, 'language_code': 'en', 'se_domain': 'google.com.gh'},
    'Greece - English': {'location_code': 2300, 'language_code': 'en', 'se_domain': 'google.gr'},
    'Greece - Greek': {'location_code': 2300, 'language_code': 'el', 'se_domain': 'google.gr'},
    'Guatemala - Spanish': {'location_code': 2320, 'language_code': 'es', 'se_domain': 'google.com.gt'},
    'Haiti - French': {'location_code': 2332, 'language_code': 'fr', 'se_domain': 'google.ht'},
    'Honduras - Spanish': {'location_code': 2340, 'language_code': 'es', 'se_domain': 'google.hn'},
    'Hong Kong - Chinese (Traditional)': {'location_code': 2344, 'language_code': 'zh-TW', 'se_domain': 'google.com.hk'},
    'Hong Kong - English': {'location_code': 2344, 'language_code': 'en', 'se_domain': 'google.com.hk'},
    'Hungary - Hungarian': {'location_code': 2348, 'language_code': 'hu', 'se_domain': 'google.hu'},
    'Iceland - Icelandic': {'location_code': 2352, 'language_code': 'is', 'se_domain': 'google.is'},
    'India - English': {'location_code': 2356, 'language_code': 'en', 'se_domain': 'google.co.in'},
    'India - Hindi': {'location_code': 2356, 'language_code': 'hi', 'se_domain': 'google.co.in'},
    'Indonesia - English': {'location_code': 2360, 'language_code': 'en', 'se_domain': 'google.co.id'},
    'Indonesia - Indonesian': {'location_code': 2360, 'language_code': 'id', 'se_domain': 'google.co.id'},
    'Ireland - English': {'location_code': 2372, 'language_code': 'en', 'se_domain': 'google.ie'},
    'Israel - Hebrew': {'location_code': 2376, 'language_code': 'iw', 'se_domain': 'google.co.il'},
    'Jamaica - English': {'location_code': 2388, 'language_code': 'en', 'se_domain': 'google.com.jm'},
    'Japan - Japanese': {'location_code': 2392, 'language_code': 'ja', 'se_domain': 'google.co.jp'},
    'Jordan - Arabic': {'location_code': 2400, 'language_code': 'ar', 'se_domain': 'google.jo'},
    'Kazakhstan - Kazakh': {'location_code': 2398, 'language_code': 'kk', 'se_domain': 'google.kz'},
    'Kazakhstan - Russian': {'location_code': 2398, 'language_code': 'ru', 'se_domain': 'google.kz'},
    'Kenya - English': {'location_code': 2404, 'language_code': 'en', 'se_domain': 'google.co.ke'},
    'Kenya - Swahili': {'location_code': 2404, 'language_code': 'sw', 'se_domain': 'google.co.ke'},
    'Kuwait - Arabic': {'location_code': 2414, 'language_code': 'ar', 'se_domain': 'google.com.kw'},
    'Latvia - Latvian': {'location_code': 2428, 'language_code': 'lv', 'se_domain': 'google.lv'},
    'Lebanon - Arabic': {'location_code': 2422, 'language_code': 'ar', 'se_domain': 'google.com.lb'},
    'Lithuania - Lithuanian': {'location_code': 2440, 'language_code': 'lt', 'se_domain': 'google.lt'},
    'Malaysia - English': {'location_code': 2458, 'language_code': 'en', 'se_domain': 'google.com.my'},
    'Malaysia - Malay': {'location_code': 2458, 'language_code': 'ms', 'se_domain': 'google.com.my'},
    'Malta - English': {'location_code': 2470, 'language_code': 'en', 'se_domain': 'google.com.mt'},
    'Mauritius - French': {'location_code': 2480, 'language_code': 'fr', 'se_domain': 'google.mu'},
    'Moldova - Romanian': {'location_code': 2498, 'language_code': 'ro', 'se_domain': 'google.md'},
    'Mongolia - Mongolian': {'location_code': 2496, 'language_code': 'mn', 'se_domain': 'google.mn'},
    'Morocco - French': {'location_code': 2504, 'language_code': 'fr', 'se_domain': 'google.co.ma'},
    'Myanmar (Burma) - English': {'location_code': 2104, 'language_code': 'en', 'se_domain': 'google.com.mm'},
    'Nepal - Nepali': {'location_code': 2524, 'language_code': 'ne', 'se_domain': 'google.com.np'},
    'Netherlands - Dutch': {'location_code': 2528, 'language_code': 'nl', 'se_domain': 'google.nl'},
    'New Zealand - English': {'location_code': 2554, 'language_code': 'en', 'se_domain': 'google.co.nz'},
    'Nicaragua - Spanish': {'location_code': 2558, 'language_code': 'es', 'se_domain': 'google.com.ni'},
    'Nigeria - English': {'location_code': 2566, 'language_code': 'en', 'se_domain': 'google.com.ng'},
    'Norway - Norwegian': {'location_code': 2578, 'language_code': 'no', 'se_domain': 'google.no'},
    'Oman - Arabic': {'location_code': 2512, 'language_code': 'ar', 'se_domain': 'google.com.om'},
    'Pakistan - English': {'location_code': 2586, 'language_code': 'en', 'se_domain': 'google.com.pk'},
    'Pakistan - Urdu': {'location_code': 2586, 'language_code': 'ur', 'se_domain': 'google.com.pk'},
    'Palestine - Arabic': {'location_code': 2275, 'language_code': 'ar', 'se_domain': 'google.ps'},
    'Panama - Spanish': {'location_code': 2591, 'language_code': 'es', 'se_domain': 'google.com.pa'},
    'Paraguay - Spanish': {'location_code': 2600, 'language_code': 'es', 'se_domain': 'google.com.py'},
    'Peru - Spanish': {'location_code': 2604, 'language_code': 'es', 'se_domain': 'google.com.pe'},
    'Philippines - English': {'location_code': 2608, 'language_code': 'en', 'se_domain': 'google.com.ph'},
    'Philippines - Filipino': {'location_code': 2608, 'language_code': 'tl', 'se_domain': 'google.com.ph'},
    'Poland - Polish': {'location_code': 2616, 'language_code': 'pl', 'se_domain': 'google.pl'},
    'Portugal - Portuguese': {'location_code': 2620, 'language_code': 'pt', 'se_domain': 'google.pt'},
    'Puerto Rico - Spanish': {'location_code': 2630, 'language_code': 'es', 'se_domain': 'google.com.pr'},
    'Qatar - Arabic': {'location_code': 2634, 'language_code': 'ar', 'se_domain': 'google.com.qa'},
    'Romania - Romanian': {'location_code': 2642, 'language_code': 'ro', 'se_domain': 'google.ro'},
    'Russia - Russian': {'location_code': 2643, 'language_code': 'ru', 'se_domain': 'google.ru'},
    'Saudi Arabia - Arabic': {'location_code': 2682, 'language_code': 'ar', 'se_domain': 'google.com.sa'},
    'Senegal - French': {'location_code': 2686, 'language_code': 'fr', 'se_domain': 'google.sn'},
    'Serbia - Serbian': {'location_code': 2688, 'language_code': 'sr', 'se_domain': 'google.rs'},
    'Singapore - English': {'location_code': 2702, 'language_code': 'en', 'se_domain': 'google.com.sg'},
    'Slovakia - Slovak': {'location_code': 2703, 'language_code': 'sk', 'se_domain': 'google.sk'},
    'Slovenia - Slovenian': {'location_code': 2705, 'language_code': 'sl', 'se_domain': 'google.si'},
    'South Africa - English': {'location_code': 2710, 'language_code': 'en', 'se_domain': 'google.co.za'},
    'South Korea - Korean': {'location_code': 2410, 'language_code': 'ko', 'se_domain': 'google.co.kr'},
    'Sri Lanka - English': {'location_code': 2144, 'language_code': 'en', 'se_domain': 'google.lk'},
    'Sweden - Swedish': {'location_code': 2752, 'language_code': 'sv', 'se_domain': 'google.se'},
    'Switzerland - French': {'location_code': 2756, 'language_code': 'fr', 'se_domain': 'google.ch'},
    'Switzerland - German': {'location_code': 2756, 'language_code': 'de', 'se_domain': 'google.ch'},
    'Taiwan - Chinese (Traditional)': {'location_code': 2158, 'language_code': 'zh-TW', 'se_domain': 'google.com.tw'},
    'Thailand - Thai': {'location_code': 2764, 'language_code': 'th', 'se_domain': 'google.co.th'},
    'Trinidad and Tobago - English': {'location_code': 2780, 'language_code': 'en', 'se_domain': 'google.tt'},
    'Tunisia - Arabic': {'location_code': 2788, 'language_code': 'ar', 'se_domain': 'google.tn'},
    'Tunisia - French': {'location_code': 2788, 'language_code': 'fr', 'se_domain': 'google.tn'},
    'Turkey - Turkish': {'location_code': 2792, 'language_code': 'tr', 'se_domain': 'google.com.tr'},
    'Ukraine - Russian': {'location_code': 2804, 'language_code': 'ru', 'se_domain': 'google.com.ua'},
    'Ukraine - Ukrainian': {'location_code': 2804, 'language_code': 'uk', 'se_domain': 'google.com.ua'},
    'United Arab Emirates - Arabic': {'location_code': 2784, 'language_code': 'ar', 'se_domain': 'google.ae'},
    'United Arab Emirates - English': {'location_code': 2784, 'language_code': 'en', 'se_domain': 'google.ae'},
    'United States - Spanish': {'location_code': 2840, 'language_code': 'es', 'se_domain': 'google.com'},
    'Uruguay - Spanish': {'location_code': 2858, 'language_code': 'es', 'se_domain': 'google.com.uy'},
    'Venezuela - Spanish': {'location_code': 2862, 'language_code': 'es', 'se_domain': 'google.co.ve'},
    'Vietnam - English': {'location_code': 2704, 'language_code': 'en', 'se_domain': 'google.com.vn'},
    'Vietnam - Vietnamese': {'location_code': 2704, 'language_code': 'vi', 'se_domain': 'google.com.vn'},
    'Zimbabwe - English': {'location_code': 2716, 'language_code': 'en', 'se_domain': 'google.co.zw'},
    'Custom': {'location_code': 0, 'language_code': '', 'se_domain': ''}
}

location_preset = widgets.Dropdown(
    options=list(LOCATION_PRESETS.keys()),
    value='🌟 USA - English',
    description='Location/Language:',
    layout=widgets.Layout(width='60%'),
    style={'description_width': '150px'}
)

# Custom location fields (hidden by default)
custom_location_label = widgets.HTML('<strong>Custom Location Settings:</strong>')
language_code = widgets.Text(
    description='Language Code:', 
    placeholder='e.g., fr, en, es', 
    value='en',
    layout=widgets.Layout(width='40%'),
    style={'description_width': '150px'}
)
location_code = widgets.IntText(
    description='Location Code:', 
    placeholder='e.g., 2250 for France', 
    value=2840,
    layout=widgets.Layout(width='40%'),
    style={'description_width': '150px'}
)
se_domain = widgets.Text(
    description='Google Domain:', 
    placeholder='e.g., google.fr, google.ca', 
    value='google.com',
    layout=widgets.Layout(width='40%'),
    style={'description_width': '150px'}
)

# Helper text for location codes
location_help = widgets.HTML("""
<small style='color: #666;'>
Common location codes: USA: 2840, France: 2250, Canada: 2124, UK: 2826, Germany: 2276<br>
Full list: <a href='https://docs.dataforseo.com/v3/appendix/locations' target='_blank'>DataForSEO Location Codes</a>
</small>
""")

# Device selection
device_selector = widgets.RadioButtons(
    options=[('Desktop', 'desktop'), ('Mobile', 'mobile')],
    value='desktop',
    description='Device:',
    layout=widgets.Layout(width='30%'),
    style={'description_width': '80px'}
)

# Add location precision note
location_note = widgets.HTML("""
<small style='color: #666; display: block; margin-top: 5px;'>
💡 <b>Note:</b> DataForSEO returns live results. Differences from your browser can occur due to:
personalization, exact location, search history, or timing. Use incognito mode for comparison.
</small>
""")

# Competitor content settings (for mode 3)
competitor_label = widgets.HTML('<h3>Competitor Content</h3>')
comparison_keyword = widgets.Text(
    description='Keyword (optional):', 
    placeholder='Enter keyword to check ranking', 
    layout=widgets.Layout(width='80%'),
    style={'description_width': '150px'}
)
competitor_source = widgets.RadioButtons(
    options=[('Paste content', 'paste'), ('Enter URL (scrape with JINA AI)', 'scrape')],
    description='Source:',
    layout=widgets.Layout(width='50%'),
    style={'description_width': '100px'}
)
competitor_input = widgets.Textarea(
    description='Content/URL:', 
    placeholder='Paste competitor content here OR enter URL to scrape', 
    layout=widgets.Layout(width='80%', height='200px'),
    style={'description_width': '100px'}
)
competitor_display = widgets.Textarea(
    description='Scraped Content:', 
    placeholder='JINA AI scraped content will appear here', 
    layout=widgets.Layout(width='90%', height='200px'),
    style={'description_width': '120px'},
    disabled=True
)

# API Cost Information
cost_info = widgets.HTML("""
<div style='background: #f0f8ff; padding: 15px; border-radius: 5px; margin-top: 20px;'>
<h4>💰 API Cost Information</h4>
<ul style='margin: 5px 0;'>
<li><b>Google NLP API:</b> ~$0.001 per 1,000 characters analyzed</li>
<li><b>JINA AI:</b> Free tier: 1M tokens/month | Paid: $0.02 per 1,000 requests</li>
<li><b>DataForSEO:</b> ~$0.0006 per SERP request (varies by plan)</li>
</ul>
<p style='margin-top: 10px;'><b>Estimated costs per run:</b></p>
<ul style='margin: 5px 0;'>
<li>Mode 1 (Content only): ~$0.001-0.005 + JINA if scraping</li>
<li>Mode 2 (Benchmark): ~$0.0006 (SERP) + ~$0.10 (5x JINA) + ~$0.025 (6x NLP)</li>
<li>Mode 3 (1-on-1): ~$0.002-0.01 + JINA if scraping</li>
</ul>
</div>
""")

# Action button
analyze_button = widgets.Button(
    description='Extract & Analyze Entities', 
    button_style='success',
    layout=widgets.Layout(width='300px', height='40px')
)

# Output area
output_area = widgets.Output()

# ========== HELPER FUNCTIONS ==========

def scrape_with_jina(url, jina_key):
    """Scrape content from URL using JINA AI"""
    jina_url = f"https://r.jina.ai/{url}"
    headers = {
        'Authorization': f'Bearer {jina_key}',
        'X-Engine': 'browser',
        'X-Return-Format': 'text'
    }
    
    try:
        response = requests.get(jina_url, headers=headers)
        if response.status_code == 200:
            # JINA returns plain text
            return response.text
        else:
            raise Exception(f"JINA AI error: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error scraping with JINA: {str(e)}")

def clean_content_for_nlp(content):
    """Clean content to remove URLs and problematic patterns that might be misidentified as entities"""
    import re
    
    # Remove URLs (both http/https and markdown links)
    content = re.sub(r'https?://[^\s\)]+', '', content)
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Convert [text](url) to just text
    
    # Remove image references that might contain 'blob' or data URIs
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    content = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', content)
    
    # Remove any remaining blob: references
    content = re.sub(r'blob:[^\s]+', '', content)
    
    # Clean up multiple spaces
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()

def extract_meta_from_jina_content(text_content):
    """Extract title and description from JINA text if available"""
    lines = text_content.split('\n')
    title = ""
    description = ""
    
    # Look for title and description patterns in the text
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        line = line.strip()
        if line and not title and len(line) < 200:  # First substantial line often is title
            title = line
        elif ('description' in line.lower() or 'meta' in line.lower()) and i < 10:
            # Look for next line as description
            if i + 1 < len(lines):
                description = lines[i + 1].strip()
    
    return title, description

def scrape_with_jina_enhanced(url, jina_key):
    """Enhanced JINA scraping with meta extraction"""
    content = scrape_with_jina(url, jina_key)
    title, description = extract_meta_from_jina_content(content)
    
    # Combine title, description, and content for entity analysis
    full_content = f"{title}\n\n{description}\n\n{content}"
    
    # Clean the content
    cleaned_content = clean_content_for_nlp(full_content)
    
    return content, cleaned_content  # Return both original and cleaned

def analyze_entities(api_key, content):
    """Analyze entities using Google NLP API"""
    url = f"https://language.googleapis.com/v1/documents:analyzeEntities?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        'document': {
            'type': 'PLAIN_TEXT',
            'content': content,
        },
        'encodingType': 'UTF8',
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Google NLP error: {response.status_code} - {response.text}")
    
    result = response.json()
    entities_data = []
    
    for entity in result.get('entities', []):
        entities_data.append({
            'entity': entity['name'].upper(),
            'type': entity['type'],
            'salience': entity['salience'],
            'mentions': len(entity['mentions'])
        })
    
    df = pd.DataFrame(entities_data)
    
    if df.empty:
        return pd.DataFrame()
    
    # Aggregate entities
    df = df.groupby(['entity', 'type'], as_index=False).agg({
        'salience': 'sum',
        'mentions': 'sum'
    })
    
    # Delorme-style scoring
    df['delorme_score'] = df['salience'] * df['mentions']
    total_score = df['delorme_score'].sum()
    if total_score > 0:
        df['delorme_salience_percent'] = (df['delorme_score'] / total_score) * 100
    else:
        df['delorme_salience_percent'] = 0
    
    df_sorted = df.sort_values(by='delorme_salience_percent', ascending=False)
    return df_sorted

def search_google_serp(keyword, lang_code, loc_code, domain, device, login, password, check_url=None):
    """Search Google using DataForSEO API"""
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/regular"
    
    # Create Basic Auth header
    auth_string = f"{login}:{password}"
    auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    payload = [{
        "language_code": lang_code,
        "location_code": loc_code,
        "keyword": keyword,
        "device": device,
        "se_domain": domain,
        "depth": 100,  # Get more results to ensure we capture top 5 organic
        "calculate_rectangles": False
    }]
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        if "tasks" not in data or len(data["tasks"]) == 0:
            raise Exception("No results from DataForSEO")
        
        task = data["tasks"][0]
        if "result" not in task or len(task["result"]) == 0:
            raise Exception("No results found")
        
        items = task["result"][0].get("items", [])
        organic_results = [item for item in items if item.get("type") == "organic"]
        
        # Check URL rank if provided
        url_rank = None
        if check_url:
            # Normalize the check URL
            check_domain = urlparse(check_url).netloc.lower().replace('www.', '')
            for i, item in enumerate(organic_results):
                result_domain = urlparse(item.get('url', '')).netloc.lower().replace('www.', '')
                if check_domain in result_domain or result_domain in check_domain:
                    url_rank = i + 1  # Organic position (1-based)
                    break
        
        # Get top 5 organic results with correct organic ranking
        top_results = []
        for i, item in enumerate(organic_results[:5]):
            top_results.append({
                'url': item.get('url', ''),
                'title': item.get('title', ''),
                'rank': i + 1,  # Use organic position, not rank_absolute
                'rank_absolute': item.get('rank_absolute', 0)  # Keep for reference
            })
        
        return top_results, url_rank
    
    except Exception as e:
        raise Exception(f"Error searching Google: {str(e)}")

def display_entities_grid(entities_dict, title, scraped_content=None, current_rank=None):
    """Display entities in a 4-column grid format with optional scraped content"""
    html = f"<h4>{title}</h4>"
    
    if not entities_dict:
        html += "<p>No entities found.</p>"
        return html
    
    # Get URL and entities
    url = entities_dict.get('url', '')
    entities = entities_dict.get('entities', [])[:16]  # Top 16 only
    
    if url:
        html += f"<p><strong>URL:</strong> <a href='{url}' target='_blank'>{url}</a>"
        if current_rank:
            html += f"<br><span style='color: #d9534f; font-weight: bold;'>Current Rank: #{current_rank}</span>"
        html += "</p>"
    
    html += "<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0;'>"
    
    for entity in entities:
        html += f"""
        <div style='border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;'>
            <strong>{entity['entity']}</strong><br>
            <small>{entity['type']}</small><br>
            <span style='color: #007bff;'>Salience: {entity['delorme_salience_percent']:.1f}%</span><br>
            <small>Mentions: {entity['mentions']}</small>
        </div>
        """
    
    html += "</div>"
    
    # Add scraped content display if provided
    if scraped_content:
        html += """
        <div style='margin-top: 20px;'>
            <h5>Scraped Content:</h5>
            <div style='border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f8f9fa; max-height: 300px; overflow-y: auto;'>
                <pre style='white-space: pre-wrap; word-wrap: break-word; margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 14px;'>{}</pre>
            </div>
        </div>
        """.format(scraped_content[:3000] + "..." if len(scraped_content) > 3000 else scraped_content)
    
    return html

def compare_entities(my_entities_df, competitor_entities_list):
    """Compare entities and find missing ones"""
    my_entity_names = set()
    if my_entities_df is not None and not my_entities_df.empty:
        my_entity_names = set(my_entities_df['entity'].tolist())
    
    all_competitor_entities = set()
    for comp in competitor_entities_list:
        if comp['entities']:
            all_competitor_entities.update([e['entity'] for e in comp['entities']])
    
    missing_entities = all_competitor_entities - my_entity_names
    
    return list(missing_entities)

# ========== MAIN ANALYSIS FUNCTION ==========

def on_analyze_clicked(b):
    with output_area:
        clear_output()
        
        try:
            # Get common inputs
            google_key = google_nlp_key.value.strip()
            jina_key = jina_api_key.value.strip()
            
            if not google_key:
                print("❌ Please provide Google NLP API Key")
                return
            
            mode = mode_selector.value
            results = {}
            
            # Mode 1: Content only
            if mode == 'content_only':
                print("🔍 Analyzing your content...")
                
                if content_source.value == 'scrape':
                    if not jina_key:
                        print("❌ JINA AI API Key required for scraping")
                        return
                    url = content_input.value.strip()
                    if not url:
                        print("❌ Please provide a URL to scrape")
                        return
                    print(f"📥 Scraping content from: {url}")
                    original_content, cleaned_content = scrape_with_jina_enhanced(url, jina_key)
                    
                    # Show full scraped content
                    content_display.value = original_content
                    content = cleaned_content
                else:
                    content = clean_content_for_nlp(content_input.value.strip())
                    if not content:
                        print("❌ Please provide content to analyze")
                        return
                
                # Analyze entities
                df_entities = analyze_entities(google_key, content)
                
                if df_entities.empty:
                    print("No entities found in the content.")
                    return
                
                # Display results
                entities_data = {
                    'url': content_input.value.strip() if content_source.value == 'scrape' else '',
                    'entities': df_entities.to_dict('records')
                }
                
                display(HTML(display_entities_grid(entities_data, "Your Content Entities")))
            
            # Mode 2: Content + Benchmark
            elif mode == 'content_benchmark':
                dataforseo_user = dataforseo_login.value.strip()
                dataforseo_pass = dataforseo_password.value.strip()
                keyword = benchmark_keyword.value.strip()
                
                if not all([dataforseo_user, dataforseo_pass, keyword]):
                    print("❌ Please provide DataForSEO credentials and keyword")
                    return
                
                # Analyze user content first (if provided)
                my_entities = pd.DataFrame()
                if content_input.value.strip():
                    print("🔍 Analyzing your content...")
                    
                    if content_source.value == 'scrape':
                        if not jina_key:
                            print("❌ JINA AI API Key required for scraping")
                            return
                        original_content, cleaned_content = scrape_with_jina_enhanced(content_input.value.strip(), jina_key)
                        content_display.value = original_content
                        content = cleaned_content
                    else:
                        content = clean_content_for_nlp(content_input.value.strip())
                    
                    my_entities = analyze_entities(google_key, content)
                
                # Get location settings
                preset = location_preset.value
                if preset == 'Custom':
                    lang = language_code.value
                    loc = location_code.value
                    domain = se_domain.value
                else:
                    preset_data = LOCATION_PRESETS[preset]
                    lang = preset_data['language_code']
                    loc = preset_data['location_code']
                    domain = preset_data['se_domain']
                
                # Search Google for top 5 results
                print(f"🔎 Searching Google for: {keyword}")
                print(f"📍 Location: {preset}, Language: {lang}, Domain: {domain}")
                print(f"📱 Device: {device_selector.value}")
                
                # Check if user's URL is provided to find its rank
                check_url = content_input.value.strip() if content_source.value == 'scrape' else None
                
                top_results, user_url_rank = search_google_serp(
                    keyword, 
                    lang, 
                    loc,
                    domain,
                    device_selector.value,
                    dataforseo_user,
                    dataforseo_pass,
                    check_url
                )
                
                # Display user's URL rank if found
                if check_url and user_url_rank:
                    print(f"📊 Your URL ranks #{user_url_rank} for '{keyword}' in {preset}")
                elif check_url:
                    print(f"❌ Your URL was not found in top 100 results for '{keyword}' in {preset}")
                
                # Analyze competitors
                competitor_entities = []
                competitor_contents = {}  # Store scraped contents
                for i, result in enumerate(top_results):
                    print(f"📊 Analyzing competitor {i+1}/5: {result['url']}")
                    
                    if not jina_key:
                        print("⚠️ Skipping - JINA AI API Key required")
                        continue
                    
                    try:
                        # Scrape competitor content
                        original_comp_content, cleaned_comp_content = scrape_with_jina_enhanced(result['url'], jina_key)
                        
                        # Store the scraped content
                        competitor_contents[result['url']] = original_comp_content
                        
                        # Analyze entities
                        comp_entities = analyze_entities(google_key, cleaned_comp_content)
                        
                        competitor_entities.append({
                            'url': result['url'],
                            'title': result['title'],
                            'rank': result['rank'],
                            'entities': comp_entities.head(16).to_dict('records') if not comp_entities.empty else []
                        })
                        
                        time.sleep(1)  # Be nice to APIs
                        
                    except Exception as e:
                        print(f"⚠️ Error analyzing {result['url']}: {str(e)}")
                
                # Display results
                if not my_entities.empty:
                    my_entities_data = {
                        'url': content_input.value.strip() if content_source.value == 'scrape' else '',
                        'entities': my_entities.head(16).to_dict('records')
                    }
                    # Pass user's rank if available
                    display(HTML(display_entities_grid(
                        my_entities_data, 
                        "Your Content Entities",
                        current_rank=user_url_rank if check_url else None
                    )))
                
                # Display competitor results
                display(HTML("<h3>Top 5 Competitor Analysis</h3>"))
                for comp in competitor_entities:
                    # Get the scraped content for this competitor
                    scraped_content = competitor_contents.get(comp['url'], '')
                    display(HTML(display_entities_grid(
                        comp, 
                        f"Rank #{comp['rank']}: {comp['title']}",
                        scraped_content=scraped_content,
                        current_rank=comp['rank']
                    )))
                
                # Show missing entities
                if not my_entities.empty and competitor_entities:
                    missing = compare_entities(my_entities, competitor_entities)
                    if missing:
                        display(HTML("<h3>🎯 Missing Entities (found in competitors but not in your content)</h3>"))
                        display(HTML("<div style='background: #fff3cd; padding: 15px; border-radius: 5px;'>"))
                        display(HTML(", ".join(missing[:20])))  # Show top 20 missing
                        display(HTML("</div>"))
            
            # Mode 3: 1-on-1 Comparison
            elif mode == 'url_analysis':
                print("🔍 Starting 1-on-1 comparison...")
                
                # Check if we need to search for ranking
                dataforseo_user = dataforseo_login.value.strip()
                dataforseo_pass = dataforseo_password.value.strip()
                keyword = comparison_keyword.value.strip()  # Use the comparison keyword field
                
                # Analyze competitor content
                competitor_entities = None
                original_comp_content = None
                comp_rank = None
                
                if competitor_input.value.strip():
                    print("📊 Analyzing competitor content...")
                    
                    if competitor_source.value == 'scrape':
                        if not jina_key:
                            print("❌ JINA AI API Key required for scraping")
                            return
                        comp_url = competitor_input.value.strip()
                        
                        # Check competitor URL rank if DataForSEO credentials and keyword are provided
                        if dataforseo_user and dataforseo_pass and keyword:
                            print(f"🔎 Checking rank for competitor URL...")
                            preset = location_preset.value
                            if preset == 'Custom':
                                lang = language_code.value
                                loc = location_code.value
                                domain = se_domain.value
                            else:
                                preset_data = LOCATION_PRESETS[preset]
                                lang = preset_data['language_code']
                                loc = preset_data['location_code']
                                domain = preset_data['se_domain']
                            
                            _, comp_rank = search_google_serp(
                                keyword, lang, loc, domain, device_selector.value,
                                dataforseo_user, dataforseo_pass, comp_url
                            )
                            
                            if comp_rank:
                                print(f"📊 Competitor URL ranks #{comp_rank} for '{keyword}' in {preset}")
                            else:
                                print(f"❌ Competitor URL not found in top 100 for '{keyword}' in {preset}")
                        
                        original_comp_content, cleaned_comp_content = scrape_with_jina_enhanced(comp_url, jina_key)
                        competitor_display.value = original_comp_content
                        comp_content = cleaned_comp_content
                    else:
                        comp_content = clean_content_for_nlp(competitor_input.value.strip())
                    
                    competitor_entities = analyze_entities(google_key, comp_content)
                
                # Analyze user content if provided
                my_entities = None
                original_my_content = None
                my_rank = None
                
                if content_input.value.strip():
                    print("📊 Analyzing your content...")
                    
                    if content_source.value == 'scrape':
                        if not jina_key:
                            print("❌ JINA AI API Key required for scraping")
                            return
                        
                        my_url = content_input.value.strip()
                        
                        # Check your URL rank if DataForSEO credentials and keyword are provided
                        if dataforseo_user and dataforseo_pass and keyword:
                            print(f"🔎 Checking rank for your URL...")
                            preset = location_preset.value
                            if preset == 'Custom':
                                lang = language_code.value
                                loc = location_code.value
                                domain = se_domain.value
                            else:
                                preset_data = LOCATION_PRESETS[preset]
                                lang = preset_data['language_code']
                                loc = preset_data['location_code']
                                domain = preset_data['se_domain']
                            
                            _, my_rank = search_google_serp(
                                keyword, lang, loc, domain, device_selector.value,
                                dataforseo_user, dataforseo_pass, my_url
                            )
                            
                            if my_rank:
                                print(f"📊 Your URL ranks #{my_rank} for '{keyword}' in {preset}")
                            else:
                                print(f"❌ Your URL not found in top 100 for '{keyword}' in {preset}")
                        
                        original_my_content, my_content = scrape_with_jina_enhanced(my_url, jina_key)
                        content_display.value = original_my_content
                    else:
                        my_content = clean_content_for_nlp(content_input.value.strip())
                    
                    my_entities = analyze_entities(google_key, my_content)
                
                # Display results based on what was provided
                if competitor_entities is not None and not competitor_entities.empty:
                    comp_data = {
                        'url': competitor_input.value.strip() if competitor_source.value == 'scrape' else '',
                        'entities': competitor_entities.head(16).to_dict('records')
                    }
                    display(HTML(display_entities_grid(
                        comp_data, 
                        "Competitor Content Entities",
                        scraped_content=original_comp_content,
                        current_rank=comp_rank
                    )))
                
                if my_entities is not None and not my_entities.empty:
                    my_data = {
                        'url': content_input.value.strip() if content_source.value == 'scrape' else '',
                        'entities': my_entities.head(16).to_dict('records')
                    }
                    display(HTML(display_entities_grid(
                        my_data, 
                        "Your Content Entities",
                        scraped_content=original_my_content,
                        current_rank=my_rank
                    )))
                
                # Compare if both are provided
                if (my_entities is not None and not my_entities.empty and 
                    competitor_entities is not None and not competitor_entities.empty):
                    missing = compare_entities(my_entities, [comp_data])
                    if missing:
                        display(HTML("<h3>🎯 Missing Entities (in competitor but not in your content)</h3>"))
                        display(HTML("<div style='background: #fff3cd; padding: 15px; border-radius: 5px;'>"))
                        display(HTML(", ".join(missing[:20])))
                        display(HTML("</div>"))
            
            print("\n✅ Analysis complete!")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

# ========== UI LAYOUT ==========

def update_ui_visibility(*args):
    """Update UI visibility based on selected mode"""
    mode = mode_selector.value
    
    # Always show API keys
    api_keys_box.layout.display = 'block'
    
    # Show/hide content display based on scraping mode
    if content_source.value == 'scrape':
        content_display.layout.display = 'block'
    else:
        content_display.layout.display = 'none'
        
    # Show/hide competitor display based on scraping mode
    if hasattr(competitor_source, 'value') and competitor_source.value == 'scrape':
        competitor_display.layout.display = 'block'
    else:
        competitor_display.layout.display = 'none'
    
    # Show/hide sections based on mode
    if mode == 'content_only':
        content_box.layout.display = 'block'
        benchmark_box.layout.display = 'none'
        competitor_box.layout.display = 'none'
        dataforseo_login.layout.display = 'none'
        dataforseo_password.layout.display = 'none'
    elif mode == 'content_benchmark':
        content_box.layout.display = 'block'
        benchmark_box.layout.display = 'block'
        competitor_box.layout.display = 'none'
        dataforseo_login.layout.display = 'block'
        dataforseo_password.layout.display = 'block'
    elif mode == 'url_analysis':
        content_box.layout.display = 'block'  # For comparison
        benchmark_box.layout.display = 'none'
        competitor_box.layout.display = 'block'
        # Show DataForSEO credentials only if keyword is entered
        if comparison_keyword.value.strip():
            dataforseo_login.layout.display = 'block'
            dataforseo_password.layout.display = 'block'
        else:
            dataforseo_login.layout.display = 'none'
            dataforseo_password.layout.display = 'none'

def update_custom_location_visibility(*args):
    """Show/hide custom location fields based on preset selection"""
    if location_preset.value == 'Custom':
        custom_location_box.layout.display = 'block'
    else:
        custom_location_box.layout.display = 'none'

# Connect observers
mode_selector.observe(update_ui_visibility, 'value')
content_source.observe(update_ui_visibility, 'value')
location_preset.observe(update_custom_location_visibility, 'value')
comparison_keyword.observe(update_ui_visibility, 'value')

# Create layout boxes
api_keys_box = widgets.VBox([
    api_keys_label,
    google_nlp_key,
    jina_api_key,
    dataforseo_login,
    dataforseo_password
])

content_box = widgets.VBox([
    content_label,
    content_source,
    content_input,
    content_display  # Add the content display area
])

# Create custom location box
custom_location_box = widgets.VBox([
    custom_location_label,
    widgets.HBox([language_code, location_code]),
    se_domain,
    location_help
])

benchmark_box = widgets.VBox([
    benchmark_label,
    benchmark_keyword,
    location_preset,
    custom_location_box,
    device_selector,
    location_note
])

competitor_box = widgets.VBox([
    competitor_label,
    comparison_keyword,
    location_preset,
    custom_location_box,
    competitor_source,
    competitor_input,
    competitor_display
])

# Connect competitor source observer after it's created
competitor_source.observe(update_ui_visibility, 'value')

# Connect button
analyze_button.on_click(on_analyze_clicked)

# Display the complete UI
display(widgets.VBox([
    widgets.HTML('<h2>🔍 Enhanced Delorme Entities Extractor</h2>'),
    mode_selector,
    api_keys_box,
    content_box,
    benchmark_box,
    competitor_box,
    cost_info,
    analyze_button,
    output_area
]))

# Initialize UI visibility
update_ui_visibility()
update_custom_location_visibility()