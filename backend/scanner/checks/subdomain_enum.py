"""
Passive subdomain enumeration module.

Discovers subdomains using two non-intrusive techniques:
1. Certificate Transparency logs via crt.sh
2. DNS resolution of a common subdomain wordlist
"""
import re
import json
import socket
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger('scanner')

# Maximum subdomains to return
MAX_SUBDOMAINS = 20

# Timeout for individual DNS lookups
DNS_TIMEOUT = 3

# Common subdomain names to check via DNS resolution
COMMON_SUBDOMAINS = [
    'www', 'mail', 'ftp', 'smtp', 'pop', 'imap', 'webmail',
    'api', 'dev', 'staging', 'stage', 'test', 'testing', 'qa',
    'admin', 'panel', 'dashboard', 'portal', 'cms', 'cpanel',
    'blog', 'shop', 'store', 'app', 'mobile', 'm',
    'cdn', 'static', 'assets', 'media', 'images', 'img',
    'ns1', 'ns2', 'dns', 'dns1', 'dns2',
    'mx', 'mx1', 'mx2', 'relay',
    'vpn', 'remote', 'gateway', 'proxy',
    'db', 'database', 'mysql', 'postgres', 'mongo', 'redis',
    'git', 'gitlab', 'github', 'bitbucket', 'jenkins', 'ci', 'cd',
    'docs', 'doc', 'wiki', 'help', 'support', 'status',
    'auth', 'sso', 'login', 'oauth', 'id', 'identity',
    'monitor', 'grafana', 'kibana', 'prometheus', 'nagios',
    'backup', 'bak', 'old', 'legacy', 'archive',
    'intranet', 'internal', 'corp', 'office',
    'beta', 'alpha', 'preview', 'sandbox', 'demo',
    'ws', 'websocket', 'socket', 'realtime',
    'search', 'elastic', 'elasticsearch', 'solr',
    'chat', 'slack', 'meet', 'video',
    'crm', 'erp', 'hr', 'jira', 'confluence',
    'cloud', 'aws', 'azure', 'gcp',
    's3', 'storage', 'files', 'upload',
    'api-v1', 'api-v2', 'api2', 'graphql',
    'autodiscover', 'autoconfig',
    'prod', 'production', 'live',
    'web', 'web1', 'web2', 'server', 'host',
]


def _extract_root_domain(hostname):
    """
    Extract the registrable root domain from a hostname.

    Examples:
        'www.example.com'     -> 'example.com'
        'sub.deep.example.co' -> 'example.co'  (simple heuristic)
        'example.com'         -> 'example.com'
    """
    parts = hostname.rstrip('.').split('.')
    if len(parts) <= 2:
        return hostname
    return '.'.join(parts[-2:])


def enumerate_subdomains_crtsh(domain, timeout=15):
    """
    Query Certificate Transparency logs via crt.sh to find subdomains.

    Returns a set of unique subdomain hostnames.
    """
    subdomains = set()
    url = f'https://crt.sh/?q=%.{domain}&output=json'

    try:
        resp = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'AuditoriaWeb-Scanner/1.0',
        })
        if resp.status_code != 200:
            logger.warning(f"crt.sh returned status {resp.status_code} for {domain}")
            return subdomains

        data = resp.json()
        for entry in data:
            name_value = entry.get('name_value', '')
            # crt.sh returns multi-line name_value with newlines
            for name in name_value.split('\n'):
                name = name.strip().lower()
                # Skip wildcard entries and empty values
                if name and not name.startswith('*') and domain in name:
                    subdomains.add(name)

    except (requests.exceptions.RequestException, json.JSONDecodeError) as exc:
        logger.warning(f"crt.sh enumeration failed for {domain}: {exc}")

    return subdomains


def _resolve_subdomain(subdomain):
    """Try to resolve a subdomain. Returns (subdomain, ip) or None."""
    try:
        socket.setdefaulttimeout(DNS_TIMEOUT)
        results = socket.getaddrinfo(subdomain, None)
        if results:
            ip = results[0][4][0]
            return (subdomain, ip)
    except (socket.gaierror, socket.timeout, OSError):
        pass
    return None


def enumerate_subdomains_wordlist(domain, max_workers=10):
    """
    Resolve common subdomain names via DNS to check which exist.

    Returns a set of (subdomain, ip) tuples.
    """
    alive = set()
    candidates = [f'{name}.{domain}' for name in COMMON_SUBDOMAINS]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_resolve_subdomain, sub): sub
            for sub in candidates
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                alive.add(result)

    return alive


def discover_subdomains(hostname):
    """
    Run all subdomain enumeration techniques and return a combined list.

    Returns:
        list of dicts: [{'subdomain': 'dev.example.com', 'ip': '1.2.3.4', 'source': 'crt.sh'}, ...]
    """
    domain = _extract_root_domain(hostname)
    logger.info(f"Starting subdomain enumeration for {domain}")

    results = {}

    # 1. Certificate Transparency
    crtsh_subs = enumerate_subdomains_crtsh(domain)
    logger.info(f"crt.sh found {len(crtsh_subs)} subdomains for {domain}")

    # Resolve crt.sh results to check they're alive
    for sub in crtsh_subs:
        if sub == domain or sub == hostname:
            continue
        resolved = _resolve_subdomain(sub)
        if resolved:
            results[resolved[0]] = {
                'subdomain': resolved[0],
                'ip': resolved[1],
                'source': 'crt.sh',
            }
        if len(results) >= MAX_SUBDOMAINS:
            break

    # 2. DNS wordlist
    if len(results) < MAX_SUBDOMAINS:
        wordlist_subs = enumerate_subdomains_wordlist(domain)
        logger.info(f"DNS wordlist found {len(wordlist_subs)} alive subdomains for {domain}")

        for sub, ip in wordlist_subs:
            if sub not in results and sub != hostname and sub != domain:
                results[sub] = {
                    'subdomain': sub,
                    'ip': ip,
                    'source': 'dns_wordlist',
                }
            if len(results) >= MAX_SUBDOMAINS:
                break

    final = list(results.values())
    logger.info(f"Total unique subdomains discovered for {domain}: {len(final)}")
    return final
