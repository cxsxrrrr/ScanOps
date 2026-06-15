"""
Passive technology fingerprinting module (Wappalyzer-style).

Detects technologies from HTTP headers, HTML content, scripts, cookies,
and meta tags. Extracts versions and checks against a built-in database
of known vulnerable versions.
"""
import re
import logging
from packaging import version as pkg_version

logger = logging.getLogger('scanner')

MAX_BODY = 300_000

# ======================================================================
# Technology detection rules
# ======================================================================
# Each rule: { 'name', 'category', 'detect': callable(headers, body, cookies) -> version|True|None }

def _header_value(headers, name):
    """Get header value case-insensitively."""
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return ''


TECH_RULES = [
    # ------- Web Servers -------
    {
        'name': 'Apache',
        'category': 'Web Server',
        'detect': lambda h, b, c: _match_header(h, 'Server', r'Apache(?:/([\d.]+))?'),
    },
    {
        'name': 'Nginx',
        'category': 'Web Server',
        'detect': lambda h, b, c: _match_header(h, 'Server', r'nginx(?:/([\d.]+))?'),
    },
    {
        'name': 'Microsoft IIS',
        'category': 'Web Server',
        'detect': lambda h, b, c: _match_header(h, 'Server', r'Microsoft-IIS(?:/([\d.]+))?'),
    },
    {
        'name': 'LiteSpeed',
        'category': 'Web Server',
        'detect': lambda h, b, c: _match_header(h, 'Server', r'LiteSpeed(?:/([\d.]+))?'),
    },
    {
        'name': 'OpenResty',
        'category': 'Web Server',
        'detect': lambda h, b, c: _match_header(h, 'Server', r'openresty(?:/([\d.]+))?'),
    },

    # ------- Languages / Runtimes -------
    {
        'name': 'PHP',
        'category': 'Language',
        'detect': lambda h, b, c: (
            _match_header(h, 'X-Powered-By', r'PHP(?:/([\d.]+))?')
            or _cookie_detect(c, 'PHPSESSID', 'PHP')
        ),
    },
    {
        'name': 'ASP.NET',
        'category': 'Framework',
        'detect': lambda h, b, c: (
            _match_header(h, 'X-Powered-By', r'ASP\.NET')
            or _match_header(h, 'X-AspNet-Version', r'([\d.]+)')
            or _cookie_detect(c, 'ASP.NET_SessionId', 'ASP.NET')
        ),
    },
    {
        'name': 'Java',
        'category': 'Language',
        'detect': lambda h, b, c: _cookie_detect(c, 'JSESSIONID', 'Java'),
    },
    {
        'name': 'Python',
        'category': 'Language',
        'detect': lambda h, b, c: _match_header(h, 'Server', r'Python(?:/([\d.]+))?'),
    },
    {
        'name': 'Node.js',
        'category': 'Runtime',
        'detect': lambda h, b, c: _match_header(h, 'X-Powered-By', r'Express|Node\.?js(?:/([\d.]+))?'),
    },

    # ------- JavaScript Libraries -------
    {
        'name': 'jQuery',
        'category': 'JS Library',
        'detect': lambda h, b, c: _match_body(b, r'jquery[.-]?([\d.]+)(?:\.min)?\.js'),
    },
    {
        'name': 'jQuery UI',
        'category': 'JS Library',
        'detect': lambda h, b, c: _match_body(b, r'jquery-ui[.-]?([\d.]+)(?:\.min)?\.js'),
    },
    {
        'name': 'Bootstrap',
        'category': 'CSS Framework',
        'detect': lambda h, b, c: _match_body(b, r'bootstrap[.-]?([\d.]+)(?:\.min)?\.(?:js|css)'),
    },
    {
        'name': 'Angular',
        'category': 'JS Framework',
        'detect': lambda h, b, c: (
            _match_body(b, r'angular[.-]?([\d.]+)(?:\.min)?\.js')
            or ('ng-app' in b and True)
            or ('ng-version="' in b and _match_body(b, r'ng-version="([\d.]+)"'))
        ),
    },
    {
        'name': 'AngularJS',
        'category': 'JS Framework',
        'detect': lambda h, b, c: _match_body(b, r'angular[.-]?(1\.[\d.]+)(?:\.min)?\.js'),
    },
    {
        'name': 'React',
        'category': 'JS Framework',
        'detect': lambda h, b, c: (
            _match_body(b, r'react(?:\.production)?[.-]?([\d.]+)(?:\.min)?\.js')
            or ('data-reactroot' in b and True)
            or ('__NEXT_DATA__' in b and True)
        ),
    },
    {
        'name': 'Vue.js',
        'category': 'JS Framework',
        'detect': lambda h, b, c: (
            _match_body(b, r'vue[.-]?([\d.]+)(?:\.min)?\.js')
            or ('data-v-' in b and True)
            or ('[data-v-' in b and True)
        ),
    },
    {
        'name': 'Lodash',
        'category': 'JS Library',
        'detect': lambda h, b, c: _match_body(b, r'lodash[.-]?([\d.]+)(?:\.min)?\.js'),
    },
    {
        'name': 'Moment.js',
        'category': 'JS Library',
        'detect': lambda h, b, c: _match_body(b, r'moment[.-]?([\d.]+)(?:\.min)?\.js'),
    },
    {
        'name': 'Underscore.js',
        'category': 'JS Library',
        'detect': lambda h, b, c: _match_body(b, r'underscore[.-]?([\d.]+)(?:\.min)?\.js'),
    },

    # ------- CMS -------
    {
        'name': 'WordPress',
        'category': 'CMS',
        'detect': lambda h, b, c: (
            _match_body(b, r'<meta[^>]+content="WordPress\s+([\d.]+)"')
            or ('wp-content/' in b and True)
        ),
    },
    {
        'name': 'Drupal',
        'category': 'CMS',
        'detect': lambda h, b, c: (
            _match_body(b, r'Drupal\s+([\d.]+)')
            or _match_header(h, 'X-Generator', r'Drupal\s*([\d.]+)?')
            or ('sites/default/files' in b and True)
            or _match_body(b, r'drupal\.js')
        ),
    },
    {
        'name': 'Joomla',
        'category': 'CMS',
        'detect': lambda h, b, c: (
            _match_body(b, r'<meta[^>]+content="Joomla[!]?\s*([\d.]+)?"')
            or ('/media/jui/' in b and True)
            or ('/components/com_' in b and True)
        ),
    },
    {
        'name': 'Shopify',
        'category': 'E-Commerce',
        'detect': lambda h, b, c: (
            'cdn.shopify.com' in b
            or 'Shopify.theme' in b
        ) and True,
    },
    {
        'name': 'Magento',
        'category': 'E-Commerce',
        'detect': lambda h, b, c: (
            '/skin/frontend/' in b
            or '/static/frontend/' in b
            or 'Mage.Cookies' in b
        ) and True,
    },
    {
        'name': 'Wix',
        'category': 'Website Builder',
        'detect': lambda h, b, c: ('X-Wix-' in str(h) or 'wix.com' in b) and True,
    },

    # ------- Frameworks -------
    {
        'name': 'Django',
        'category': 'Framework',
        'detect': lambda h, b, c: (
            _cookie_detect(c, 'csrftoken', 'Django')
            or _cookie_detect(c, 'django', 'Django')
        ),
    },
    {
        'name': 'Laravel',
        'category': 'Framework',
        'detect': lambda h, b, c: (
            _cookie_detect(c, 'laravel_session', 'Laravel')
            or _cookie_detect(c, 'XSRF-TOKEN', 'Laravel')
        ),
    },
    {
        'name': 'Ruby on Rails',
        'category': 'Framework',
        'detect': lambda h, b, c: (
            _match_header(h, 'X-Powered-By', r'Phusion Passenger')
            or _cookie_detect(c, '_rails_session', 'Rails')
            or _match_header(h, 'X-Runtime', r'[\d.]+')
        ),
    },
    {
        'name': 'Express',
        'category': 'Framework',
        'detect': lambda h, b, c: _match_header(h, 'X-Powered-By', r'Express'),
    },
    {
        'name': 'Spring',
        'category': 'Framework',
        'detect': lambda h, b, c: _cookie_detect(c, 'JSESSIONID', 'Spring') if 'X-Application-Context' in str(h) else None,
    },

    # ------- Analytics / CDN -------
    {
        'name': 'Google Analytics',
        'category': 'Analytics',
        'detect': lambda h, b, c: (
            'google-analytics.com/analytics.js' in b
            or 'gtag(' in b
            or 'googletagmanager.com' in b
        ) and True,
    },
    {
        'name': 'Cloudflare',
        'category': 'CDN',
        'detect': lambda h, b, c: (
            'cloudflare' in _header_value(h, 'Server').lower()
            or _header_value(h, 'cf-ray') != ''
        ) and True,
    },
    {
        'name': 'Font Awesome',
        'category': 'Font',
        'detect': lambda h, b, c: _match_body(b, r'font-awesome[.-]?([\d.]+)?(?:\.min)?\.css'),
    },
    {
        'name': 'Google Fonts',
        'category': 'Font',
        'detect': lambda h, b, c: 'fonts.googleapis.com' in b and True,
    },
]


# ======================================================================
# Detection helpers
# ======================================================================

def _match_header(headers, header_name, pattern):
    """Match a regex pattern against a header value. Returns version or True."""
    value = _header_value(headers, header_name)
    if not value:
        return None
    match = re.search(pattern, value, re.IGNORECASE)
    if match:
        groups = match.groups()
        if groups and groups[0]:
            return groups[0]
        return True
    return None


def _match_body(body, pattern):
    """Match a regex pattern in the response body. Returns version or True."""
    match = re.search(pattern, body, re.IGNORECASE)
    if match:
        groups = match.groups()
        if groups and groups[0]:
            return groups[0]
        return True
    return None


def _cookie_detect(cookies, cookie_name, tech_name):
    """Detect technology by cookie name. Returns True or None."""
    cookie_str = str(cookies).lower()
    if cookie_name.lower() in cookie_str:
        return True
    return None


# ======================================================================
# Known vulnerable versions database
# ======================================================================
# Format: { 'Technology': [ { 'below': 'version', 'severity': 'HIGH|MEDIUM',
#            'cves': 'CVE-...', 'description': '...' } ] }
# 'below' means any version BELOW this is considered vulnerable.

KNOWN_VULNERABILITIES = {
    'Apache': [
        {
            'below': '2.4.58',
            'severity': 'HIGH',
            'cves': 'CVE-2023-45802, CVE-2023-43622',
            'description': 'HTTP/2 DoS and request smuggling vulnerabilities.',
        },
        {
            'below': '2.4.52',
            'severity': 'CRITICAL',
            'cves': 'CVE-2021-44790, CVE-2021-44224',
            'description': 'Buffer overflow and SSRF in mod_lua and mod_proxy.',
        },
    ],
    'Nginx': [
        {
            'below': '1.25.4',
            'severity': 'MEDIUM',
            'cves': 'CVE-2024-24989, CVE-2024-24990',
            'description': 'HTTP/3 QUIC vulnerability in NGINX.',
        },
        {
            'below': '1.22.0',
            'severity': 'HIGH',
            'cves': 'CVE-2022-41741, CVE-2022-41742',
            'description': 'Memory corruption in mp4 module.',
        },
    ],
    'Microsoft IIS': [
        {
            'below': '10.0',
            'severity': 'HIGH',
            'cves': 'CVE-2021-31166',
            'description': 'HTTP Protocol Stack remote code execution.',
        },
    ],
    'PHP': [
        {
            'below': '7.4.0',
            'severity': 'CRITICAL',
            'cves': 'Multiple CVEs',
            'description': 'PHP 7.3 and earlier are end-of-life with unpatched vulnerabilities.',
        },
        {
            'below': '8.1.0',
            'severity': 'HIGH',
            'cves': 'CVE-2023-3823, CVE-2023-3824',
            'description': 'XML external entity and buffer overflow vulnerabilities.',
        },
        {
            'below': '8.3.4',
            'severity': 'HIGH',
            'cves': 'CVE-2024-2756, CVE-2024-3096',
            'description': 'Cookie bypass and password_verify() issues.',
        },
    ],
    'jQuery': [
        {
            'below': '3.5.0',
            'severity': 'MEDIUM',
            'cves': 'CVE-2020-11022, CVE-2020-11023',
            'description': 'Cross-site scripting (XSS) via htmlPrefilter regex.',
        },
        {
            'below': '3.0.0',
            'severity': 'HIGH',
            'cves': 'CVE-2019-11358, CVE-2015-9251',
            'description': 'Prototype pollution and XSS via cross-domain Ajax requests.',
        },
        {
            'below': '1.12.0',
            'severity': 'HIGH',
            'cves': 'CVE-2015-9251, CVE-2012-6708',
            'description': 'Multiple XSS vulnerabilities in selector-based input handling.',
        },
    ],
    'jQuery UI': [
        {
            'below': '1.13.2',
            'severity': 'MEDIUM',
            'cves': 'CVE-2022-31160',
            'description': 'XSS vulnerability in the checkboxradio widget.',
        },
        {
            'below': '1.12.0',
            'severity': 'HIGH',
            'cves': 'CVE-2021-41184, CVE-2021-41183, CVE-2021-41182',
            'description': 'XSS in various widgets including dialog and datepicker.',
        },
    ],
    'AngularJS': [
        {
            'below': '1.8.0',
            'severity': 'HIGH',
            'cves': 'CVE-2022-25869',
            'description': 'XSS via $sanitize bypass. AngularJS is end-of-life.',
        },
        {
            'below': '1.6.0',
            'severity': 'CRITICAL',
            'cves': 'Multiple CVEs',
            'description': 'Sandbox escape, XSS, and prototype pollution. AngularJS 1.x is EOL.',
        },
    ],
    'Bootstrap': [
        {
            'below': '5.3.3',
            'severity': 'MEDIUM',
            'cves': 'CVE-2024-6484, CVE-2024-6485',
            'description': 'XSS in carousel and tooltip components.',
        },
        {
            'below': '4.3.1',
            'severity': 'MEDIUM',
            'cves': 'CVE-2019-8331',
            'description': 'XSS in data-template, data-content, and data-title attributes.',
        },
        {
            'below': '3.4.0',
            'severity': 'HIGH',
            'cves': 'CVE-2018-14040, CVE-2018-14042',
            'description': 'Multiple XSS vulnerabilities in collapse and tooltip.',
        },
    ],
    'Lodash': [
        {
            'below': '4.17.21',
            'severity': 'HIGH',
            'cves': 'CVE-2021-23337, CVE-2020-28500',
            'description': 'Command injection and ReDoS vulnerabilities.',
        },
        {
            'below': '4.17.12',
            'severity': 'CRITICAL',
            'cves': 'CVE-2019-10744',
            'description': 'Prototype pollution via defaultsDeep function.',
        },
    ],
    'Moment.js': [
        {
            'below': '2.29.4',
            'severity': 'HIGH',
            'cves': 'CVE-2022-31129',
            'description': 'ReDoS vulnerability in string parsing. Moment.js is now in maintenance mode.',
        },
    ],
    'Drupal': [
        {
            'below': '10.2.3',
            'severity': 'MEDIUM',
            'cves': 'SA-CORE-2024-001',
            'description': 'Access bypass and cache poisoning vulnerabilities.',
        },
        {
            'below': '9.0.0',
            'severity': 'CRITICAL',
            'cves': 'Multiple CVEs including Drupalgeddon',
            'description': 'Drupal 8 and earlier are end-of-life with critical RCE vulnerabilities.',
        },
    ],
    'Joomla': [
        {
            'below': '5.0.3',
            'severity': 'HIGH',
            'cves': 'CVE-2024-21722, CVE-2024-21723',
            'description': 'Session fixation and URL redirect vulnerabilities.',
        },
        {
            'below': '4.0.0',
            'severity': 'CRITICAL',
            'cves': 'Multiple CVEs',
            'description': 'Joomla 3.x is end-of-life with multiple known vulnerabilities.',
        },
    ],
    'Underscore.js': [
        {
            'below': '1.13.6',
            'severity': 'HIGH',
            'cves': 'CVE-2021-23358',
            'description': 'Arbitrary code execution via template function.',
        },
    ],
    'LiteSpeed': [
        {
            'below': '6.1',
            'severity': 'HIGH',
            'cves': 'CVE-2023-5601',
            'description': 'HTTP/2 rapid reset vulnerability.',
        },
    ],
    'Node.js': [
        {
            'below': '20.11.1',
            'severity': 'HIGH',
            'cves': 'CVE-2024-22019, CVE-2024-21896',
            'description': 'HTTP request smuggling and path traversal attacks.',
        },
        {
            'below': '18.0.0',
            'severity': 'HIGH',
            'cves': 'Multiple CVEs',
            'description': 'Node.js 16 and earlier are end-of-life.',
        },
    ],
    'Font Awesome': [
        {
            'below': '5.0.0',
            'severity': 'LOW',
            'cves': 'N/A',
            'description': 'Font Awesome 4.x is end-of-life and no longer receives updates.',
        },
    ],
}


# ======================================================================
# Main entry point
# ======================================================================

def _is_version_below(detected, threshold):
    """Compare version strings. Returns True if detected < threshold."""
    try:
        return pkg_version.parse(detected) < pkg_version.parse(threshold)
    except Exception:
        # Fallback to simple tuple comparison
        try:
            d = tuple(int(x) for x in detected.split('.'))
            t = tuple(int(x) for x in threshold.split('.'))
            return d < t
        except (ValueError, AttributeError):
            return False


def fingerprint_technologies(response):
    """
    Detect all technologies from response headers, body, and cookies.

    Returns list of dicts: [{'name': 'jQuery', 'version': '3.3.1', 'category': 'JS Library'}, ...]
    """
    headers = response.headers
    body = response.text[:MAX_BODY] if hasattr(response, 'text') else ''
    cookies = str(response.cookies) if hasattr(response, 'cookies') else ''

    detected = []

    for rule in TECH_RULES:
        try:
            result = rule['detect'](headers, body, cookies)
            if result:
                version = result if isinstance(result, str) else None
                detected.append({
                    'name': rule['name'],
                    'version': version,
                    'category': rule['category'],
                })
        except Exception as exc:
            logger.debug(f"Tech detection rule '{rule['name']}' error: {exc}")

    return detected


def check_technologies(response, parsed_url, findings):
    """
    Detect technologies and check for known vulnerabilities.

    This is the main entry point called by the scan engine.
    """
    techs = fingerprint_technologies(response)

    if not techs:
        return

    # Build summary line
    tech_summary_parts = []
    for t in techs:
        if t['version']:
            tech_summary_parts.append(f"{t['name']} {t['version']}")
        else:
            tech_summary_parts.append(t['name'])

    findings.append({
        'title': f'Technologies Detected ({len(techs)})',
        'severity': 'INFO',
        'category': 'technology',
        'description': (
            f'{len(techs)} technologies identified via passive fingerprinting: '
            f'{", ".join(tech_summary_parts)}.'
        ),
        'recommendation': (
            'Keep all technologies updated to the latest stable versions. '
            'Remove unnecessary version disclosures from headers.'
        ),
        'evidence': f'Technologies: {", ".join(tech_summary_parts)}',
    })

    # Check each versioned technology against known vulnerabilities
    for tech in techs:
        if not tech['version']:
            continue

        vulns = KNOWN_VULNERABILITIES.get(tech['name'], [])
        for vuln in vulns:
            if _is_version_below(tech['version'], vuln['below']):
                findings.append({
                    'title': f'Vulnerable {tech["name"]} {tech["version"]}',
                    'severity': vuln['severity'],
                    'category': 'technology',
                    'description': (
                        f'{tech["name"]} version {tech["version"]} is vulnerable. '
                        f'{vuln["description"]} '
                        f'(Affects versions below {vuln["below"]})'
                    ),
                    'recommendation': (
                        f'Update {tech["name"]} to version {vuln["below"]} or later. '
                        f'CVEs: {vuln["cves"]}.'
                    ),
                    'evidence': (
                        f'Detected: {tech["name"]} {tech["version"]}, '
                        f'vulnerable below {vuln["below"]}'
                    ),
                })
                break  # Report only the most critical vulnerability match
