"""
Passive application-level security checks.

Detects HTTP request smuggling, cache poisoning, insecure deserialization,
file upload issues, prototype pollution, GraphQL exposure, race conditions,
API security, subdomain takeover, cache deception, and LLM endpoint exposure.
"""
import re
import logging
import subprocess
from urllib.parse import urlparse

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

# Known services vulnerable to subdomain takeover via dangling CNAME
TAKEOVER_FINGERPRINTS = [
    'amazonaws.com', 'heroku.com', 'herokuapp.com',
    'github.io', 'ghost.io', 'surge.sh',
    'bitbucket.io', 'azurewebsites.net',
    'cloudfront.net', 'pantheon.io',
    'shopify.com', 'tumblr.com',
    'wpengine.com', 'zendesk.com',
    'readme.io', 'fastly.net',
]

# Vulnerable JavaScript libraries (known CVEs)
VULNERABLE_JS_LIBS = re.compile(
    r'(?:'
    r'jquery[/-](?:1\.\d+|2\.[012])\.'
    r'|angular(?:\.min)?\.js/1\.[0-5]\.'
    r'|lodash(?:\.min)?\.js/[34]\.'
    r'|prototype\.js'
    r'|dojo/1\.[0-9]\.'
    r'|moment(?:\.min)?\.js/2\.(?:[0-9]|1[0-8])\.'
    r')',
    re.IGNORECASE,
)

# Serialized object patterns
SERIALIZED_PATTERNS = re.compile(
    r'(?:'
    r'rO0ABX'           # Java serialized object (base64)
    r'|O:\d+:"'         # PHP serialized object
    r'|a:\d+:\{'        # PHP serialized array
    r'|AAEAAAD'         # .NET BinaryFormatter (base64)
    r'|__pickle__'      # Python pickle
    r')',
)


def _get_body(response):
    """Return the response body truncated to MAX_BODY_SIZE."""
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_http_smuggling(response, parsed_url, findings):
    """Detect HTTP request smuggling indicators."""
    headers = response.headers

    has_cl = 'Content-Length' in headers
    transfer_encoding = headers.get('Transfer-Encoding', '').lower()
    has_te = bool(transfer_encoding)

    # Both Content-Length and Transfer-Encoding present (CL.TE / TE.CL)
    if has_cl and has_te:
        findings.append({
            'title': 'Potential HTTP Request Smuggling',
            'severity': 'HIGH',
            'category': 'http_smuggling',
            'description': (
                'Both Content-Length and Transfer-Encoding headers are present '
                'in the response. This inconsistency between front-end and '
                'back-end servers can enable request smuggling attacks.'
            ),
            'recommendation': (
                'Ensure only one of Content-Length or Transfer-Encoding is used. '
                'Configure the front-end proxy to normalize request headers.'
            ),
            'evidence': (
                f'Content-Length: {headers.get("Content-Length")}, '
                f'Transfer-Encoding: {transfer_encoding}'
            ),
        })


def check_cache_poisoning(response, parsed_url, findings):
    """Detect web cache poisoning indicators."""
    headers = response.headers

    # Check for cacheable responses that reflect unkeyed headers
    cache_indicators = ['X-Cache', 'CF-Cache-Status', 'Age',
                        'X-Varnish', 'X-Cache-Hits']
    is_cached = any(h in headers for h in cache_indicators)

    vary = headers.get('Vary', '')

    if is_cached and not vary:
        findings.append({
            'title': 'Cacheable Response Without Vary Header',
            'severity': 'MEDIUM',
            'category': 'cache_poisoning',
            'description': (
                'The response is served from a cache but does not include a '
                'Vary header. Unkeyed headers may poison cached responses '
                'served to other users.'
            ),
            'recommendation': (
                'Add a Vary header specifying which request headers affect '
                'the response. Audit cache keys to include all relevant inputs.'
            ),
            'evidence': (
                f'Cache headers present: '
                f'{", ".join(h for h in cache_indicators if h in headers)}'
            ),
        })


def check_deserialization(response, parsed_url, findings):
    """Detect serialized objects in responses and cookies."""
    body = _get_body(response)

    # Check response body
    match = SERIALIZED_PATTERNS.search(body)
    if match:
        findings.append({
            'title': 'Serialized Object Detected in Response',
            'severity': 'HIGH',
            'category': 'deserialization',
            'description': (
                'The response contains patterns characteristic of serialized '
                'objects (Java, PHP, .NET, or Python). If user-controlled data '
                'is deserialized, this can lead to remote code execution.'
            ),
            'recommendation': (
                'Avoid deserializing untrusted data. Use safe formats like '
                'JSON. Implement integrity checks on serialized data.'
            ),
            'evidence': f'Serialization pattern: {match.group()[:100]}',
        })

    # Check cookies for serialized data
    cookies_header = response.headers.get('Set-Cookie', '')
    if SERIALIZED_PATTERNS.search(cookies_header):
        findings.append({
            'title': 'Serialized Object in Cookie',
            'severity': 'HIGH',
            'category': 'deserialization',
            'description': (
                'A cookie contains serialized object data. An attacker '
                'could craft a malicious serialized payload in the cookie.'
            ),
            'recommendation': (
                'Use signed, encrypted cookies with simple data formats. '
                'Never deserialize raw cookie values.'
            ),
            'evidence': 'Serialized data pattern detected in Set-Cookie header.',
        })


def check_file_upload(response, parsed_url, findings):
    """Detect file upload forms without proper restrictions."""
    body = _get_body(response)

    file_inputs = re.findall(
        r'<input[^>]*type\s*=\s*["\']file["\'][^>]*>',
        body,
        re.IGNORECASE,
    )

    for file_input in file_inputs:
        has_accept = 'accept=' in file_input.lower()
        if not has_accept:
            findings.append({
                'title': 'File Upload Without Type Restriction',
                'severity': 'MEDIUM',
                'category': 'file_upload',
                'description': (
                    'A file upload field does not specify accepted file types. '
                    'Without server-side validation, attackers could upload '
                    'malicious files (web shells, executables).'
                ),
                'recommendation': (
                    'Add an accept attribute to restrict file types client-side. '
                    'Always validate file type, size, and content server-side. '
                    'Store uploads outside the web root.'
                ),
                'evidence': 'File input without accept attribute.',
            })
            break


def check_prototype_pollution(response, parsed_url, findings):
    """Detect known vulnerable JavaScript libraries."""
    body = _get_body(response)

    matches = VULNERABLE_JS_LIBS.findall(body)
    if matches:
        unique = list(set(matches))[:5]
        findings.append({
            'title': 'Potentially Vulnerable JavaScript Libraries',
            'severity': 'MEDIUM',
            'category': 'prototype_pollution',
            'description': (
                'The page references JavaScript libraries with versions known '
                'to have prototype pollution or other security vulnerabilities.'
            ),
            'recommendation': (
                'Update all JavaScript libraries to their latest stable versions. '
                'Audit third-party dependencies regularly.'
            ),
            'evidence': f'Vulnerable library patterns: {", ".join(unique)}',
        })


def check_graphql(response, parsed_url, findings):
    """Detect exposed GraphQL endpoints with introspection."""
    body = _get_body(response)

    graphql_indicators = [
        '"__schema"', '"__type"', 'graphql', 'GraphQL',
        '"data":{', '"errors":[',
    ]

    # Check if the page itself references GraphQL
    graphql_refs = [ind for ind in graphql_indicators if ind in body]

    if graphql_refs:
        findings.append({
            'title': 'GraphQL Endpoint Detected',
            'severity': 'INFO',
            'category': 'graphql',
            'description': (
                'The response contains GraphQL-related content. If '
                'introspection is enabled, the full API schema may be exposed.'
            ),
            'recommendation': (
                'Disable GraphQL introspection in production. '
                'Implement query depth limiting and rate limiting.'
            ),
            'evidence': f'GraphQL indicators: {", ".join(graphql_refs[:3])}',
        })

    # Introspection specifically enabled
    if '"__schema"' in body or '"__type"' in body:
        findings.append({
            'title': 'GraphQL Introspection May Be Enabled',
            'severity': 'MEDIUM',
            'category': 'graphql',
            'description': (
                'GraphQL introspection data was found in the response. '
                'This exposes the complete API schema to attackers.'
            ),
            'recommendation': (
                'Disable introspection in production by setting '
                'introspection: false in your GraphQL server configuration.'
            ),
            'evidence': 'Introspection schema data found in response.',
        })


def check_api_security(response, parsed_url, findings):
    """Detect exposed API documentation and version info."""
    body = _get_body(response)

    # Exposed API documentation
    api_doc_patterns = [
        'swagger-ui', 'Swagger UI', 'swagger.json', 'swagger.yaml',
        'openapi.json', 'openapi.yaml',
        'api-docs', 'redoc',
    ]

    found_docs = [p for p in api_doc_patterns if p in body]
    if found_docs:
        findings.append({
            'title': 'API Documentation Publicly Exposed',
            'severity': 'MEDIUM',
            'category': 'api',
            'description': (
                'Public API documentation was detected. While helpful for '
                'developers, exposed docs give attackers a complete map '
                'of available endpoints and parameters.'
            ),
            'recommendation': (
                'Restrict API documentation access to authenticated users '
                'or internal networks. Use API keys and rate limiting.'
            ),
            'evidence': f'API doc references: {", ".join(found_docs[:5])}',
        })

    # API version disclosure in headers
    api_version_headers = ['X-API-Version', 'API-Version', 'X-Version']
    for header in api_version_headers:
        if header in response.headers:
            findings.append({
                'title': 'API Version Disclosed in Headers',
                'severity': 'LOW',
                'category': 'api',
                'description': (
                    f'The {header} header reveals the API version. '
                    f'This helps attackers identify known vulnerabilities.'
                ),
                'recommendation': 'Remove API version headers from responses.',
                'evidence': f'{header}: {response.headers[header]}',
            })
            break


def check_subdomain_takeover(response, parsed_url, findings, hostname=None):
    """Detect dangling CNAME records pointing to decommissioned services."""
    target_hostname = hostname or parsed_url.hostname
    if not target_hostname:
        return

    try:
        result = subprocess.run(
            ['nslookup', '-type=cname', target_hostname],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.lower()

        for fingerprint in TAKEOVER_FINGERPRINTS:
            if fingerprint in output:
                findings.append({
                    'title': 'Potential Subdomain Takeover Risk',
                    'severity': 'HIGH',
                    'category': 'subdomain_takeover',
                    'description': (
                        f'A CNAME record points to {fingerprint}, which may '
                        f'be vulnerable to subdomain takeover if the service '
                        f'is no longer active.'
                    ),
                    'recommendation': (
                        'Verify that the CNAME target is still actively claimed. '
                        'Remove DNS records pointing to decommissioned services.'
                    ),
                    'evidence': f'CNAME pointing to {fingerprint} for {target_hostname}',
                })
                break

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning(f"Subdomain takeover check failed for {target_hostname}: {exc}")


def check_cache_deception(response, parsed_url, findings):
    """Detect web cache deception indicators."""
    headers = response.headers
    cache_control = headers.get('Cache-Control', '').lower()

    # Authenticated response that is cacheable
    has_auth_header = 'Set-Cookie' in headers or 'Authorization' in headers
    is_cacheable = (
        'public' in cache_control
        or ('max-age' in cache_control and 'private' not in cache_control
            and 'no-store' not in cache_control)
    )

    if has_auth_header and is_cacheable:
        findings.append({
            'title': 'Potential Web Cache Deception',
            'severity': 'MEDIUM',
            'category': 'cache_deception',
            'description': (
                'An authenticated response is marked as cacheable. '
                'Attackers may trick a victim into visiting a crafted URL '
                'that caches their authenticated data for public retrieval.'
            ),
            'recommendation': (
                'Set Cache-Control: private, no-store on authenticated '
                'responses. Ensure caches do not store sensitive data.'
            ),
            'evidence': (
                f'Cache-Control: {cache_control}, '
                f'Authentication headers present'
            ),
        })


def check_llm(response, parsed_url, findings):
    """Detect exposed LLM/AI chatbot endpoints."""
    body = _get_body(response)

    llm_indicators = [
        'openai.com/v1', '/api/chat', '/api/completions',
        'anthropic.com', 'generativelanguage.googleapis.com',
        '/v1/chat/completions', 'api-key',
    ]

    found = [ind for ind in llm_indicators if ind in body]
    if found:
        findings.append({
            'title': 'LLM/AI API Endpoint References Detected',
            'severity': 'MEDIUM',
            'category': 'llm',
            'description': (
                'The response contains references to LLM or AI API endpoints. '
                'If API keys or backend prompts are exposed, attackers could '
                'abuse the AI service or extract sensitive data.'
            ),
            'recommendation': (
                'Proxy AI API calls through your backend — never expose '
                'API keys in client-side code. Implement rate limiting '
                'and input validation on AI endpoints.'
            ),
            'evidence': f'AI references found: {", ".join(found[:3])}',
        })

    # Check for exposed API keys in page source
    api_key_patterns = re.findall(
        r'(?:sk-[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_-]{33})',
        body,
    )
    if api_key_patterns:
        findings.append({
            'title': 'AI API Key Exposed in Page Source',
            'severity': 'CRITICAL',
            'category': 'llm',
            'description': (
                'An API key for an AI/LLM service was found in the page '
                'source. This allows attackers to use the service at the '
                'owner\'s expense or access sensitive data.'
            ),
            'recommendation': (
                'Remove API keys from client-side code immediately. '
                'Use server-side proxying for all API calls. '
                'Rotate compromised keys.'
            ),
            'evidence': f'API key pattern found (redacted for security).',
        })


# Export list of all application security check functions
APP_SECURITY_CHECKS = [
    check_http_smuggling,
    check_cache_poisoning,
    check_deserialization,
    check_file_upload,
    check_prototype_pollution,
    check_graphql,
    check_api_security,
    check_subdomain_takeover,
    check_cache_deception,
    check_llm,
]
