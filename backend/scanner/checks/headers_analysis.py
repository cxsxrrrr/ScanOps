"""
Deep Content-Security-Policy and cross-origin isolation header analysis.

Parses CSP directives for weaknesses and checks for missing
cross-origin isolation headers (COOP, CORP, COEP).
"""
import re
import logging

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_csp_deep(response, parsed_url, findings):
    """Deep analysis of Content-Security-Policy for weaknesses."""
    csp = response.headers.get('Content-Security-Policy', '')

    if not csp:
        return

    directives = _parse_csp(csp)
    _check_csp_unsafe_inline(directives, csp, findings)
    _check_csp_unsafe_eval(directives, findings)
    _check_csp_wildcard(directives, findings)
    _check_csp_missing_directives(directives, findings)
    _check_csp_form_action(directives, findings)
    _check_csp_base_uri(directives, findings)
    _check_csp_object_src(directives, findings)


def check_cross_origin_headers(response, parsed_url, findings):
    """Check for missing cross-origin isolation headers."""
    headers = response.headers

    coop = headers.get('Cross-Origin-Opener-Policy', '')
    corp = headers.get('Cross-Origin-Resource-Policy', '')
    coep = headers.get('Cross-Origin-Embedder-Policy', '')

    if not coop:
        findings.append({
            'title': 'Missing Cross-Origin-Opener-Policy Header',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                'The Cross-Origin-Opener-Policy (COOP) header is missing. '
                'Without COOP, cross-origin windows can access each other\'s '
                'context, enabling side-channel attacks like Spectre.'
            ),
            'recommendation': (
                'Set Cross-Origin-Opener-Policy: same-origin to isolate '
                'your browsing context from cross-origin openers.'
            ),
            'evidence': 'Cross-Origin-Opener-Policy header not present',
        })
    elif coop.lower() in ('unsafe-none', 'same-origin-allow-popups'):
        findings.append({
            'title': f'Weak Cross-Origin-Opener-Policy: {coop}',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                f'COOP is set to "{coop}", which does not provide full '
                f'cross-origin isolation. This may allow side-channel attacks.'
            ),
            'recommendation': (
                'Set Cross-Origin-Opener-Policy: same-origin for maximum '
                'cross-origin isolation.'
            ),
            'evidence': f'Cross-Origin-Opener-Policy: {coop}',
        })

    if not corp:
        findings.append({
            'title': 'Missing Cross-Origin-Resource-Policy Header',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                'The Cross-Origin-Resource-Policy (CORP) header is missing. '
                'Without CORP, cross-origin sites can embed resources, '
                'potentially enabling cross-origin information leaks.'
            ),
            'recommendation': (
                'Set Cross-Origin-Resource-Policy: same-origin to prevent '
                'cross-origin resource embedding.'
            ),
            'evidence': 'Cross-Origin-Resource-Policy header not present',
        })

    if not coep:
        findings.append({
            'title': 'Missing Cross-Origin-Embedder-Policy Header',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                'The Cross-Origin-Embedder-Policy (COEP) header is missing. '
                'Without COEP, the page cannot use SharedArrayBuffer and is '
                'vulnerable to cross-origin resource attacks.'
            ),
            'recommendation': (
                'Set Cross-Origin-Embedder-Policy: require-corp to enable '
                'cross-origin isolation. Requires CORP headers on all resources.'
            ),
            'evidence': 'Cross-Origin-Embedder-Policy header not present',
        })


def check_permissions_policy(response, parsed_url, findings):
    """Analyze Permissions-Policy header for overly permissive directives."""
    pp = response.headers.get('Permissions-Policy', '')
    if not pp:
        return

    dangerous_allows = []
    permissive_features = [
        'geolocation', 'camera', 'microphone', 'fullscreen',
        'payment', 'usb', 'magnetometer', 'gyroscope', 'accelerometer',
    ]

    for feature in permissive_features:
        pattern = rf'{feature}\s*=\s*\[\s*\*\s*\]'
        if re.search(pattern, pp, re.IGNORECASE):
            dangerous_allows.append(feature)

    if dangerous_allows:
        findings.append({
            'title': 'Permissive Permissions-Policy Directives',
            'severity': 'MEDIUM',
            'category': 'headers',
            'description': (
                f'The Permissions-Policy allows wildcard (*) access to: '
                f'{", ".join(dangerous_allows)}. This grants these '
                f'permissions to any origin, including malicious iframes.'
            ),
            'recommendation': (
                'Restrict Permissions-Policy directives to specific origins. '
                'E.g., geolocation=(self "https://trusted.example.com")'
            ),
            'evidence': f'Wildcards allowed for: {", ".join(dangerous_allows)}',
        })


def _parse_csp(csp):
    """Parse CSP string into directive dict."""
    directives = {}
    for part in csp.split(';'):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        if tokens:
            directive = tokens[0].lower()
            values = tokens[1:]
            directives[directive] = values
    return directives


def _check_csp_unsafe_inline(directives, csp, findings):
    """Check for 'unsafe-inline' in script-src or style-src."""
    for d in ('script-src', 'default-src'):
        if d in directives and "'unsafe-inline'" in directives[d]:
            findings.append({
                'title': 'CSP Allows Unsafe Inline Scripts',
                'severity': 'HIGH',
                'category': 'headers',
                'description': (
                    'The Content-Security-Policy contains \'unsafe-inline\' '
                    'in the script-src (or default-src) directive. This '
                    'effectively negates XSS protection provided by CSP.'
                ),
                'recommendation': (
                    'Remove \'unsafe-inline\' and use nonce-based or '
                    'hash-based CSP for inline scripts. Use \'unsafe-inline\' '
                    'only as a fallback for older browsers with nonce hashes.'
                ),
                'evidence': f'CSP directive contains unsafe-inline: {d}',
            })
            break

    for d in ('style-src', 'default-src'):
        if d in directives and "'unsafe-inline'" in directives[d]:
            findings.append({
                'title': 'CSP Allows Unsafe Inline Styles',
                'severity': 'LOW',
                'category': 'headers',
                'description': (
                    'The Content-Security-Policy contains \'unsafe-inline\' '
                    'in the style-src directive. This can enable CSS-based '
                    'data exfiltration attacks.'
                ),
                'recommendation': (
                    'Remove \'unsafe-inline\' from style-src. Use nonces '
                    'or hashes for inline styles.'
                ),
                'evidence': f'CSP style-src contains unsafe-inline',
            })
            break


def _check_csp_unsafe_eval(directives, findings):
    """Check for 'unsafe-eval' in CSP."""
    for d in ('script-src', 'default-src'):
        if d in directives and "'unsafe-eval'" in directives[d]:
            findings.append({
                'title': 'CSP Allows Unsafe Eval',
                'severity': 'MEDIUM',
                'category': 'headers',
                'description': (
                    'The Content-Security-Policy contains \'unsafe-eval\' '
                    'which allows eval() and similar functions. This weakens '
                    'XSS protection significantly.'
                ),
                'recommendation': (
                    'Remove \'unsafe-eval\' from CSP. Refactor code to '
                    'avoid eval(), new Function(), and setTimeout with strings.'
                ),
                'evidence': f'CSP directive contains unsafe-eval',
            })
            break


def _check_csp_wildcard(directives, findings):
    """Check for wildcard sources in CSP directives."""
    dangerous_wildcards = []
    for d in ('script-src', 'default-src', 'connect-src', 'frame-src', 'form-action'):
        if d in directives:
            if '*' in directives[d] and "'self'" not in directives[d]:
                dangerous_wildcards.append(d)

    if dangerous_wildcards:
        findings.append({
            'title': 'CSP Contains Wildcard (*) Source',
            'severity': 'HIGH',
            'category': 'headers',
            'description': (
                f'The Content-Security-Policy uses wildcard (*) sources in: '
                f'{", ".join(dangerous_wildcards)}. This allows loading '
                f'resources from any origin, severely weakening CSP protection.'
            ),
            'recommendation': (
                'Replace wildcard (*) sources with specific trusted domains. '
                'Use \'self\' and explicit origins for each directive.'
            ),
            'evidence': f'Wildcard in directives: {", ".join(dangerous_wildcards)}',
        })


def _check_csp_missing_directives(directives, findings):
    """Check for important missing CSP directives."""
    missing = []

    if 'default-src' not in directives:
        missing.append('default-src')
    if 'script-src' not in directives and 'default-src' not in directives:
        missing.append('script-src')
    if 'img-src' not in directives:
        missing.append('img-src')
    if 'connect-src' not in directives:
        missing.append('connect-src')
    if 'frame-src' not in directives and 'child-src' not in directives:
        missing.append('frame-src')

    if missing and 'default-src' not in missing:
        findings.append({
            'title': 'CSP Missing Important Directives',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                f'The Content-Security-Policy is missing these directives: '
                f'{", ".join(missing)}. Missing directives may fall back to '
                f'default-src, which could be more permissive than intended.'
            ),
            'recommendation': (
                'Add explicit directives for script-src, img-src, '
                'connect-src, and frame-src to control resource loading.'
            ),
            'evidence': f'Missing directives: {", ".join(missing)}',
        })


def _check_csp_form_action(directives, findings):
    """Check if CSP has form-action directive to prevent form hijacking."""
    if 'form-action' not in directives and 'default-src' not in directives:
        return

    if 'form-action' not in directives:
        findings.append({
            'title': 'CSP Missing form-action Directive',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                'The Content-Security-Policy does not include a form-action '
                'directive. Without it, forms can submit data to any URL, '
                'enabling phishing attacks via form hijacking.'
            ),
            'recommendation': (
                'Add form-action \'self\' to restrict form submissions '
                'to same-origin destinations.'
            ),
            'evidence': 'form-action directive not present in CSP',
        })
    elif '*' in directives.get('form-action', []):
        findings.append({
            'title': 'CSP form-action Allows Wildcard',
            'severity': 'MEDIUM',
            'category': 'headers',
            'description': (
                'The CSP form-action directive allows submission to any URL (*). '
                'This enables phishing attacks via form hijacking.'
            ),
            'recommendation': (
                'Replace form-action * with form-action \'self\' or '
                'specific trusted origins.'
            ),
            'evidence': 'form-action: * in CSP',
        })


def _check_csp_base_uri(directives, findings):
    """Check if CSP restricts base-uri to prevent base tag injection."""
    if 'base-uri' not in directives:
        findings.append({
            'title': 'CSP Missing base-uri Directive',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                'The Content-Security-Policy does not include a base-uri '
                'directive. An attacker could inject a <base> tag to '
                'hijack relative URLs and redirect requests.'
            ),
            'recommendation': "Add base-uri 'self' or base-uri 'none' to CSP.",
            'evidence': 'base-uri directive not present in CSP',
        })


def _check_csp_object_src(directives, findings):
    """Check if CSP restricts object-src to prevent plugin content."""
    if 'object-src' not in directives:
        default_src = directives.get('default-src', [])
        if '*' in default_src:
            findings.append({
                'title': 'CSP Missing object-uri (Plugins Unrestricted)',
                'severity': 'MEDIUM',
                'category': 'headers',
                'description': (
                    'The Content-Security-Policy does not include an '
                    'object-src directive and default-src uses a wildcard. '
                    'Flash, Java applets, and other plugins can be loaded '
                    'from any origin.'
                ),
                'recommendation': "Add object-src 'none' to prevent plugin content.",
                'evidence': 'object-src directive not present, default-src is wildcard',
            })


def check_hsts_deep(response, parsed_url, findings):
    """Deep analysis of HSTS header for misconfigurations."""
    hsts = response.headers.get('Strict-Transport-Security', '')

    if not hsts:
        return

    max_age_match = re.search(r'max-age=(\d+)', hsts, re.IGNORECASE)
    if max_age_match:
        max_age = int(max_age_match.group(1))
        one_year = 31536000
        six_months = 15768000

        if max_age < six_months:
            findings.append({
                'title': f'HSTS max-age Too Short ({max_age}s)',
                'severity': 'MEDIUM',
                'category': 'headers',
                'description': (
                    f'The HSTS max-age is only {max_age} seconds '
                    f'({max_age // 86400} days). Browsers will forget the '
                    f'HSTS policy quickly, leaving users vulnerable.'
                ),
                'recommendation': (
                    'Set HSTS max-age to at least 31536000 (1 year). '
                    'Consider using 63072000 (2 years) for better protection.'
                ),
                'evidence': f'Strict-Transport-Security: {hsts}',
            })
        elif max_age < one_year:
            findings.append({
                'title': f'HSTS max-age Below 1 Year ({max_age}s)',
                'severity': 'LOW',
                'category': 'headers',
                'description': (
                    f'The HSTS max-age is {max_age} seconds '
                    f'({max_age // 86400} days). While functional, '
                    f'the recommended minimum is 1 year (31536000).'
                ),
                'recommendation': (
                    'Set HSTS max-age to at least 31536000 (1 year).'
                ),
                'evidence': f'Strict-Transport-Security: {hsts}',
            })

    if 'includesubdomains' not in hsts.lower():
        findings.append({
            'title': 'HSTS Missing includeSubDomains Directive',
            'severity': 'MEDIUM',
            'category': 'headers',
            'description': (
                'The HSTS header does not include the includeSubDomains '
                'directive. Subdomains are not covered by the HSTS policy.'
            ),
            'recommendation': (
                'Add includeSubDomains to the HSTS header to ensure all '
                'subdomains use HTTPS.'
            ),
            'evidence': f'Strict-Transport-Security: {hsts}',
        })

    if 'preload' not in hsts.lower():
        findings.append({
            'title': 'HSTS Missing preload Directive',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                'The HSTS header does not include the preload directive. '
                'The domain is not submitted to the HSTS preload list, '
                'meaning first-time visitors are unprotected.'
            ),
            'recommendation': (
                'Add preload to the HSTS header and submit your domain to '
                'https://hstspreload.org/ for maximum protection.'
            ),
            'evidence': f'Strict-Transport-Security: {hsts}',
        })


def check_content_type_sniffing(response, parsed_url, findings):
    """Check for missing X-Content-Type-Options header."""
    xcto = response.headers.get('X-Content-Type-Options', '')

    if not xcto:
        findings.append({
            'title': 'Missing X-Content-Type-Options Header',
            'severity': 'MEDIUM',
            'category': 'headers',
            'description': (
                'The X-Content-Type-Options header is missing. Without it, '
                'browsers may MIME-sniff responses and interpret uploaded files '
                'as different content types (e.g., executing HTML in a .txt upload).'
            ),
            'recommendation': (
                'Add the header X-Content-Type-Options: nosniff to all responses. '
                'This prevents browsers from MIME-sniffing the response content type.'
            ),
            'evidence': 'X-Content-Type-Options header not present',
        })
    elif xcto.lower() != 'nosniff':
        findings.append({
            'title': f'Incorrect X-Content-Type-Options Value: {xcto}',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                f'The X-Content-Type-Options header is set to "{xcto}" instead '
                f'of "nosniff". The only valid value for this header is "nosniff".'
            ),
            'recommendation': 'Set X-Content-Type-Options: nosniff.',
            'evidence': f'X-Content-Type-Options: {xcto}',
        })


HEADERS_ANALYSIS_CHECKS = [
    check_csp_deep,
    check_cross_origin_headers,
    check_permissions_policy,
    check_hsts_deep,
    check_content_type_sniffing,
]