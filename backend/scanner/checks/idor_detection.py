"""
Insecure Direct Object Reference (IDOR) detection.

Detects predictable resource identifiers in URLs and forms that may
enable IDOR attacks. Identifies sequential or guessable ID patterns.
"""
import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

ID_PATTERNS = [
    (re.compile(r'[?&](?:id|user_id|uid|account_id|customer_id|member_id|profile_id)\s*=\s*(\d+)', re.I), 'numeric'),
    (re.compile(r'[?&](?:order_id|order|invoice_id|transaction_id|payment_id)\s*=\s*(\d+)', re.I), 'numeric'),
    (re.compile(r'[?&](?:file_id|document_id|doc_id|attachment_id|resource_id)\s*=\s*(\d+)', re.I), 'numeric'),
    (re.compile(r'[?&](?:post_id|article_id|comment_id|thread_id|page_id)\s*=\s*(\d+)', re.I), 'numeric'),
    (re.compile(r'/api/(?:v\d+/)?(?:users?|accounts?|profiles?|customers?)/(\d+)', re.I), 'rest_path'),
    (re.compile(r'/api/(?:v\d+/)?(?:orders?|invoices?|transactions?|payments?)/(\d+)', re.I), 'rest_path'),
    (re.compile(r'/api/(?:v\d+/)?(?:files?|documents?|attachments?|resources?)/(\d+)', re.I), 'rest_path'),
]

GUID_PATTERN = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)

SEQUENTIAL_THRESHOLD = 3


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_idor(response, parsed_url, findings):
    """Detect IDOR-vulnerable patterns in URLs and page content."""
    url = parsed_url.geturl()
    body = _get_body(response)

    _check_url_ids(url, parsed_url, findings)
    _check_page_links(body, parsed_url, findings)


def _check_url_ids(url, parsed_url, findings):
    """Check the current URL for predictable ID parameters."""
    found_patterns = []
    numeric_values = []

    for pattern, id_type in ID_PATTERNS:
        matches = pattern.findall(url)
        for match in matches:
            found_patterns.append((pattern.pattern, id_type))
            try:
                if int(match) < 10000:
                    numeric_values.append(int(match))
            except (ValueError, TypeError):
                pass

    if not numeric_values:
        return

    low_values = [v for v in numeric_values if v < 1000]

    if low_values:
        findings.append({
            'title': 'Predictable Resource Identifier in URL',
            'severity': 'MEDIUM',
            'category': 'idor',
            'description': (
                f'The URL contains low numeric identifiers ({low_values}). '
                f'Low or sequential IDs enable IDOR attacks where an attacker '
                f'can access other users\' resources by incrementing the ID.'
            ),
            'recommendation': (
                'Use UUIDs or other non-guessable identifiers instead of '
                'sequential numeric IDs. Implement authorization checks on '
                'every request to verify the user owns the requested resource.'
            ),
            'evidence': f'Predictable IDs found: {low_values}',
        })


def _check_page_links(body, parsed_url, findings):
    """Analyze page links for sequential ID patterns."""
    href_ids = re.findall(
        r'href=["\'][^"\']*[?&](?:id|user_id|uid|order_id|doc_id)=(\d+)',
        body,
        re.IGNORECASE,
    )

    api_ids = re.findall(
        r'/api/v\d+/\w+/(\d+)',
        body,
    )

    all_ids = []
    for id_str in href_ids + api_ids:
        try:
            val = int(id_str)
            all_ids.append(val)
        except ValueError:
            pass

    if len(all_ids) < 2:
        return

    all_ids = sorted(set(all_ids))

    sequential_groups = []
    current_group = [all_ids[0]]

    for i in range(1, len(all_ids)):
        if all_ids[i] - all_ids[i - 1] == 1:
            current_group.append(all_ids[i])
        else:
            if len(current_group) >= SEQUENTIAL_THRESHOLD:
                sequential_groups.append(current_group[:])
            current_group = [all_ids[i]]

    if len(current_group) >= SEQUENTIAL_THRESHOLD:
        sequential_groups.append(current_group)

    if sequential_groups and len(all_ids) >= 3:
        max_id = max(all_ids)
        findings.append({
            'title': f'Sequential Resource IDs Detected ({len(all_ids)} resources)',
            'severity': 'MEDIUM',
            'category': 'idor',
            'description': (
                f'{len(all_ids)} resources use sequential numeric IDs (range '
                f'{min(all_ids)}-{max_id}). Sequential IDs enable IDOR attacks '
                f'where attackers can enumerate and access unauthorized resources.'
            ),
            'recommendation': (
                'Replace sequential numeric IDs with UUIDs. Implement proper '
                'authorization checks so users can only access their own resources.'
            ),
            'evidence': f'ID range: {min(all_ids)}-{max_id}, {len(sequential_groups)} sequential group(s)',
        })

    guid_count = len(GUID_PATTERN.findall(body))
    if guid_count > 0 and len(all_ids) == 0:
        pass


IDOR_CHECKS = [check_idor]