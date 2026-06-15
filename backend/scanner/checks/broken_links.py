"""
Broken link hijacking detection.

Discovers external links in the page and checks if they return
error responses (404/5xx). Broken links can be claimed by attackers
for phishing or malware distribution.
"""
import re
import logging
import requests as req_lib
from urllib.parse import urljoin, urlparse

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000
LINK_TIMEOUT = 8
MAX_LINKS = 30

LINK_PATTERN = re.compile(
    r'<(?:a|area|link)\s[^>]*(?:href|src)\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

SOCIAL_DOMAINS = {
    'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
    'linkedin.com', 'youtube.com', 'github.com', 'twitch.tv',
    'tiktok.com', 'reddit.com', 'pinterest.com', 'medium.com',
    't.me', 'discord.gg', 'discord.com',
}

EXTENSION_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.css', '.js'}


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_broken_links(response, parsed_url, findings):
    """Detect external links that may be broken and vulnerable to hijacking."""
    body = _get_body(response)
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'

    links = LINK_PATTERN.findall(body)
    if not links:
        return

    external_links = set()
    for href in links:
        href = href.strip()
        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:')):
            continue
        if href.startswith('/'):
            continue
        if href.startswith(base_url):
            continue

        try:
            parsed_href = urlparse(href)
            if parsed_href.scheme in ('http', 'https') and parsed_href.netloc != parsed_url.netloc:
                external_links.add(href)
        except Exception:
            continue

    if not external_links:
        return

    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    broken_social = []
    broken_other = []

    for href in sorted(external_links)[:MAX_LINKS]:
        try:
            resp = session.head(href, timeout=LINK_TIMEOUT, allow_redirects=True, verify=False)
            status = resp.status_code
        except req_lib.exceptions.RequestException:
            try:
                resp = session.get(href, timeout=LINK_TIMEOUT, allow_redirects=True, verify=False)
                status = resp.status_code
            except req_lib.exceptions.RequestException:
                status = 0

        if status == 0 or status >= 400:
            parsed_href = urlparse(href)
            domain = parsed_href.netloc.lower()

            if any(social in domain for social in SOCIAL_DOMAINS):
                broken_social.append(href)
            else:
                broken_other.append(href)

    if broken_social:
        for link in broken_social:
            domain = urlparse(link).netloc.lower()
            platform = next((s for s in SOCIAL_DOMAINS if s in domain), 'unknown')
            findings.append({
                'title': f'Broken Social Media Link — {platform}',
                'severity': 'HIGH',
                'category': 'broken_link_hijacking',
                'description': (
                    f'A link to {domain} returns an error, meaning the account/page '
                    f'may no longer exist. An attacker could register this account '
                    f'and redirect users to malicious content (broken link hijacking).'
                ),
                'recommendation': (
                    'Remove or update broken social media links. Regularly audit '
                    'external links and verify account ownership.'
                ),
                'evidence': f'Broken link: {link}',
            })

    if broken_other:
        findings.append({
            'title': f'Broken External Links ({len(broken_other)})',
            'severity': 'LOW',
            'category': 'broken_link_hijacking',
            'description': (
                f'{len(broken_other)} external link(s) return error responses. '
                f'Broken links degrade user experience and may be vulnerable to '
                f'link hijacking if the domain expires.'
            ),
            'recommendation': (
                'Regularly audit external links. Remove or update broken links. '
                'Consider using rel="nofollow noopener" for external links.'
            ),
            'evidence': f'Broken links: {"; ".join(broken_other[:5])}',
        })


BROKEN_LINKS_CHECKS = [check_broken_links]