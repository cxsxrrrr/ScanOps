"""
Robots.txt and sitemap.xml discovery and analysis.

Parses robots.txt for disallowed paths (information disclosure)
and sitemap.xml for hidden URLs. Probes the paths found.
"""
import re
import logging
import requests as req_lib
from urllib.parse import urljoin

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10


def check_discovery(response, parsed_url, findings):
    """Discover and analyze robots.txt and sitemap.xml."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    _check_robots_txt(session, base_url, findings)
    _check_sitemap_xml(session, base_url, findings)


def _check_robots_txt(session, base_url, findings):
    """Parse robots.txt for information disclosure."""
    try:
        resp = session.get(
            f'{base_url}/robots.txt',
            timeout=PROBE_TIMEOUT,
            allow_redirects=True,
            verify=False,
        )
    except req_lib.exceptions.RequestException:
        return

    if resp.status_code != 200 or not resp.text:
        return

    content = resp.text
    lines = content.split('\n')

    disallowed_paths = []
    sensitive_disallowed = []

    sensitive_keywords = [
        'admin', 'login', 'secret', 'private', 'backup', 'config',
        'database', 'db', 'internal', 'staging', 'test', 'dev',
        'api', 'temp', 'tmp', 'old', 'debug', 'console', 'panel',
        'dashboard', 'management', 'install', 'setup', 'migration',
    ]

    for line in lines:
        line = line.strip()
        if line.lower().startswith('disallow:'):
            path = line.split(':', 1)[1].strip()
            if path and path != '/':
                disallowed_paths.append(path)
                path_lower = path.lower()
                for keyword in sensitive_keywords:
                    if keyword in path_lower:
                        sensitive_disallowed.append(path)
                        break

    if disallowed_paths:
        findings.append({
            'title': f'Robots.txt Disallowed Paths ({len(disallowed_paths)})',
            'severity': 'INFO',
            'category': 'info_disclosure',
            'description': (
                f'The robots.txt file reveals {len(disallowed_paths)} disallowed '
                f'path(s). While robots.txt is meant to guide search engines, '
                f'it also reveals the structure of private areas to attackers.'
            ),
            'recommendation': (
                'Do not rely on robots.txt for access control. Use '
                'authentication and authorization to protect sensitive paths. '
                'Consider removing sensitive paths from robots.txt.'
            ),
            'evidence': f'Disallowed paths: {"; ".join(disallowed_paths[:10])}',
        })

    if sensitive_disallowed:
        findings.append({
            'title': f'Sensitive Paths in Robots.txt ({len(sensitive_disallowed)})',
            'severity': 'MEDIUM',
            'category': 'info_disclosure',
            'description': (
                f'The robots.txt file reveals {len(sensitive_disallowed)} '
                f'sensitive path(s) that should not be publicly known. '
                f'Attackers specifically check robots.txt to find these areas.'
            ),
            'recommendation': (
                'Remove sensitive paths from robots.txt. Protect these '
                'areas with proper authentication instead of relying on '
                'robots.txt obscurity.'
            ),
            'evidence': f'Sensitive paths: {"; ".join(sensitive_disallowed[:10])}',
        })


def _check_sitemap_xml(session, base_url, findings):
    """Parse sitemap.xml for hidden URL discovery."""
    try:
        resp = session.get(
            f'{base_url}/sitemap.xml',
            timeout=PROBE_TIMEOUT,
            allow_redirects=True,
            verify=False,
        )
    except req_lib.exceptions.RequestException:
        return

    if resp.status_code != 200 or not resp.text:
        return

    content = resp.text
    if '<urlset' not in content.lower() and '<sitemapindex' not in content.lower():
        return

    urls = re.findall(r'<loc>(.*?)</loc>', content, re.IGNORECASE)

    admin_urls = []
    api_urls = []
    interesting_urls = []

    for url in urls:
        url_lower = url.lower()
        if any(kw in url_lower for kw in ['admin', 'dashboard', 'panel', 'manage']):
            admin_urls.append(url)
        elif any(kw in url_lower for kw in ['api', 'graphql', 'rest']):
            api_urls.append(url)
        elif any(kw in url_lower for kw in ['upload', 'download', 'export', 'debug', 'log']):
            interesting_urls.append(url)

    total_urls = len(urls)
    if total_urls > 0:
        findings.append({
            'title': f'Sitemap.xml Discovered ({total_urls} URLs)',
            'severity': 'INFO',
            'category': 'info_disclosure',
            'description': (
                f'The sitemap.xml file contains {total_urls} URLs. '
                f'This reveals the site structure and hidden pages.'
            ),
            'recommendation': (
                'Ensure only public pages are included in sitemap.xml. '
                'Do not include admin, debug, or private pages.'
            ),
            'evidence': f'Sitemap contains {total_urls} URLs',
        })

    if admin_urls:
        findings.append({
            'title': f'Admin/Premium URLs in Sitemap ({len(admin_urls)})',
            'severity': 'MEDIUM',
            'category': 'info_disclosure',
            'description': (
                f'The sitemap contains {len(admin_urls)} admin/management '
                f'URL(s). Exposing admin URLs helps attackers find attack '
                f'surface more easily.'
            ),
            'recommendation': (
                'Remove admin and management URLs from sitemap.xml. '
                'Protect them with authentication and authorization.'
            ),
            'evidence': f'Admin URLs: {"; ".join(admin_urls[:5])}',
        })

    if api_urls:
        findings.append({
            'title': f'API URLs in Sitemap ({len(api_urls)})',
            'severity': 'LOW',
            'category': 'api',
            'description': (
                f'The sitemap contains {len(api_urls)} API endpoint URL(s). '
                f'Public API documentation helps attackers understand the API.'
            ),
            'recommendation': (
                'Remove API endpoints from the public sitemap unless they '
                'are intentionally public. Document APIs separately with '
                'proper authentication.'
            ),
            'evidence': f'API URLs: {"; ".join(api_urls[:5])}',
        })


DISCOVERY_CHECKS = [check_discovery]