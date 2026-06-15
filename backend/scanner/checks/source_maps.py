"""
Source map exposure detection.

Detects accessible .js.map and .css.map files that expose
original source code, internal paths, and application structure.
"""
import re
import logging
import requests as req_lib

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000
PROBE_TIMEOUT = 10


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_source_maps(response, parsed_url, findings):
    """Detect exposed source maps and references to them."""
    body = _get_body(response)

    _check_source_map_references(body, parsed_url, findings)
    _check_webpack_source(body, parsed_url, findings)


def _check_source_map_references(body, parsed_url, findings):
    """Detect references to .map files in scripts and stylesheets."""
    js_map_refs = re.findall(
        r'(?:src|href)\s*=\s*["\']([^"\']+\.js)(?:["\'])',
        body,
        re.IGNORECASE,
    )
    css_map_refs = re.findall(
        r'(?:href)\s*=\s*["\']([^"\']+\.css)(?:["\'])',
        body,
        re.IGNORECASE,
    )

    map_urls = []
    for js_url in js_map_refs[:20]:
        if js_url.startswith('http'):
            map_urls.append(js_url + '.map')
        else:
            from urllib.parse import urljoin
            map_urls.append(urljoin(f'{parsed_url.scheme}://{parsed_url.netloc}', js_url + '.map'))

    for css_url in css_map_refs[:10]:
        if css_url.startswith('http'):
            map_urls.append(css_url + '.map')
        else:
            from urllib.parse import urljoin
            map_urls.append(urljoin(f'{parsed_url.scheme}://{parsed_url.netloc}', css_url + '.map'))

    accessible_maps = []
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    for map_url in map_urls[:15]:
        try:
            resp = session.get(map_url, timeout=PROBE_TIMEOUT, allow_redirects=True, verify=False)
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                if 'json' in content_type or 'javascript' in content_type or 'map' in content_type:
                    try:
                        data = resp.json()
                        if 'sources' in data or 'version' in data:
                            accessible_maps.append(map_url)
                            if len(accessible_maps) >= 5:
                                break
                    except Exception:
                        if len(resp.text) > 50 and ('sources' in resp.text or 'mappings' in resp.text):
                            accessible_maps.append(map_url)
                            if len(accessible_maps) >= 5:
                                break
        except req_lib.exceptions.RequestException:
            continue

    if accessible_maps:
        findings.append({
            'title': f'Source Maps Exposed ({len(accessible_maps)} found)',
            'severity': 'MEDIUM',
            'category': 'info_disclosure',
            'description': (
                f'{len(accessible_maps)} JavaScript/CSS source map files '
                f'are publicly accessible. Source maps expose the original '
                f'source code, internal file paths, variable names, and '
                f'application structure — giving attackers detailed knowledge '
                f'of the codebase.'
            ),
            'recommendation': (
                'Remove source map files from production deployments. '
                'Configure your build process to generate maps only in '
                'development. Add server rules to deny access to .map files.'
            ),
            'evidence': f'Accessible source maps: {"; ".join(accessible_maps[:5])}',
        })

    sourceMappingURL_pattern = re.findall(
        r'//#\s*sourceMappingURL\s*=\s*(\S+)',
        body,
    )
    if sourceMappingURL_pattern and not accessible_maps:
        findings.append({
            'title': 'Source Map References Found in Code',
            'severity': 'LOW',
            'category': 'info_disclosure',
            'description': (
                'The page source contains sourceMappingURL references. '
                'While the maps may not be directly accessible, their '
                'presence in production code indicates a build process '
                'that may leak source maps.'
            ),
            'recommendation': (
                'Remove sourceMappingURL comments from production builds. '
                'Most bundlers have options to strip these automatically.'
            ),
            'evidence': f'Source map references: {"; ".join(sourceMappingURL_pattern[:3])}',
        })


def _check_webpack_source(body, parsed_url, findings):
    """Detect webpack:// source references that expose internal structure."""
    webpack_refs = re.findall(r'webpack://([^"\']+)', body)
    if webpack_refs:
        unique_paths = list(set(webpack_refs))[:8]
        findings.append({
            'title': 'Webpack Source References Detected',
            'severity': 'LOW',
            'category': 'info_disclosure',
            'description': (
                'The page contains webpack:// source references that expose '
                'internal project structure, including package names and '
                'file paths. This helps attackers understand the codebase.'
            ),
            'recommendation': (
                'Configure your bundler to not include webpack:// paths in '
                'production builds. Use TerserPlugin with output.pathinfo=false.'
            ),
            'evidence': f'Webpack paths: {"; ".join(unique_paths)}',
        })


SOURCE_MAP_CHECKS = [check_source_maps]