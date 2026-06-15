"""
Deep JWT security analysis.

Decodes JWT tokens found in responses to check for weak algorithms,
missing expiration, algorithm confusion attacks, and exposed secrets.
"""
import re
import json
import base64
import logging

logger = logging.getLogger('scanner')

JWT_PATTERN = re.compile(
    r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
)

MAX_BODY_SIZE = 150_000


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def _b64url_decode(data):
    """Decode base64url-encoded string, handling padding."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    try:
        return base64.urlsafe_b64decode(data)
    except Exception:
        return None


def _decode_jwt(token):
    """Decode JWT header and payload without verification."""
    parts = token.split('.')
    if len(parts) != 3:
        return None, None

    header_raw = _b64url_decode(parts[0])
    payload_raw = _b64url_decode(parts[1])

    header = None
    payload = None

    if header_raw:
        try:
            header = json.loads(header_raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    if payload_raw:
        try:
            payload = json.loads(payload_raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    return header, payload


def check_jwt_deep(response, parsed_url, findings):
    """Deep analysis of JWT tokens found in page content."""
    body = _get_body(response)
    tokens = JWT_PATTERN.findall(body)

    if not tokens:
        query = parsed_url.query if hasattr(parsed_url, 'query') else ''
        tokens = JWT_PATTERN.findall(query)

    if not tokens:
        return

    seen = set()
    for token in tokens[:10]:
        token_hash = token[:50]
        if token_hash in seen:
            continue
        seen.add(token_hash)

        header, payload = _decode_jwt(token)
        if header is None:
            continue

        _check_algorithm(token, header, findings)
        _check_expiration(token, payload, findings)
        _check_sensitive_claims(token, payload, findings)
        _check_jku_x5u(header, findings)


def _check_algorithm(token, header, findings):
    """Check for weak or dangerous JWT algorithms."""
    alg = header.get('alg', '').upper()

    if alg == 'NONE' or alg == '':
        findings.append({
            'title': 'JWT Using "none" Algorithm',
            'severity': 'CRITICAL',
            'category': 'jwt',
            'description': (
                'A JWT token uses the "none" algorithm, which means it is not '
                'signed at all. Attackers can modify the payload and the server '
                'may accept it as valid.'
            ),
            'recommendation': (
                'Never accept tokens with alg=none. Always verify the algorithm '
                'on the server side and reject none-type algorithms.'
            ),
            'evidence': f'JWT header: {json.dumps(header)}',
        })
        return

    if alg in ('HS256', 'HS384', 'HS512'):
        pass

    if alg.startswith('HS'):
        findings.append({
            'title': f'JWT Using Symmetric Algorithm ({alg})',
            'severity': 'INFO',
            'category': 'jwt',
            'description': (
                f'A JWT token uses the symmetric algorithm {alg}. If the signing '
                f'secret is weak or exposed, tokens can be forged. Symmetric '
                f'algorithms also require sharing the secret with all parties.'
            ),
            'recommendation': (
                'Use asymmetric algorithms (RS256, ES256) when possible. '
                'Ensure the HMAC secret is strong (256+ bits) and not hardcoded.'
            ),
            'evidence': f'JWT algorithm: {alg}',
        })

    if alg in ('RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512', 'PS256', 'PS384', 'PS512'):
        if header.get('typ', '').lower() == 'jwt' or True:
            pass


def _check_expiration(token, payload, findings):
    """Check if JWT has expiration and if it's reasonable."""
    if payload is None:
        return

    if 'exp' not in payload:
        findings.append({
            'title': 'JWT Token Without Expiration (exp)',
            'severity': 'HIGH',
            'category': 'jwt',
            'description': (
                'A JWT token does not include an expiration claim (exp). '
                'Tokens without expiration remain valid indefinitely, '
                'increasing the window of abuse if compromised.'
            ),
            'recommendation': (
                'Always set an exp claim on JWT tokens. Use short expiration '
                'times (15-60 minutes for access tokens) and refresh tokens '
                'for longer sessions.'
            ),
            'evidence': 'JWT payload missing exp claim',
        })
    else:
        import time
        try:
            exp_time = int(payload['exp'])
            now = int(time.time())
            lifetime_days = (exp_time - now) // 86400
            if lifetime_days > 30:
                findings.append({
                    'title': f'JWT Token Excessively Long Expiration ({lifetime_days}d)',
                    'severity': 'MEDIUM',
                    'category': 'jwt',
                    'description': (
                        f'A JWT token has an expiration {lifetime_days} days from now. '
                        f'Long-lived tokens increase the damage window if compromised.'
                    ),
                    'recommendation': (
                        'Use short-lived access tokens (15-60 minutes). '
                        'Issue refresh tokens for longer sessions.'
                    ),
                    'evidence': f'Token expires in {lifetime_days} days',
                })
        except (ValueError, TypeError, OSError):
            pass

    if 'iat' not in payload:
        findings.append({
            'title': 'JWT Token Without Issued-At (iat)',
            'severity': 'LOW',
            'category': 'jwt',
            'description': (
                'A JWT token does not include an issued-at claim (iat). '
                'Without iat, it is difficult to determine token age or '
                'enforce rotation policies.'
            ),
            'recommendation': 'Always include the iat claim in JWT tokens.',
            'evidence': 'JWT payload missing iat claim',
        })


def _check_sensitive_claims(token, payload, findings):
    """Check for sensitive data exposed in JWT payload."""
    if payload is None:
        return

    sensitive_keys = [
        'password', 'secret', 'private_key', 'credit_card',
        'ssn', 'social_security', 'api_key', 'access_key',
    ]

    found_sensitive = []
    for key in sensitive_keys:
        if key in payload or key.replace('_', '') in payload:
            found_sensitive.append(key)

    if found_sensitive:
        findings.append({
            'title': f'Sensitive Data in JWT Payload ({", ".join(found_sensitive)})',
            'severity': 'HIGH',
            'category': 'jwt',
            'description': (
                'The JWT payload contains sensitive data: '
                f'{", ".join(found_sensitive)}. JWT payloads are base64-encoded '
                f'and easily decoded. Never store secrets in JWT tokens.'
            ),
            'recommendation': (
                'Remove sensitive data from JWT payloads. Use opaque references '
                'or store sensitive data server-side with the token as a lookup key.'
            ),
            'evidence': f'Sensitive claims found: {", ".join(found_sensitive)}',
        })

    if 'sub' in payload and isinstance(payload['sub'], (int, float)) and payload['sub'] < 1000:
        findings.append({
            'title': 'JWT with Predictable Subject Claim',
            'severity': 'MEDIUM',
            'category': 'jwt',
            'description': (
                f'The JWT subject (sub) is a low integer ({payload["sub"]}), '
                f'which may indicate sequential or predictable user IDs that '
                f'enable IDOR attacks.'
            ),
            'recommendation': (
                'Use UUIDs or other non-sequential identifiers for the sub claim '
                'to prevent enumeration attacks.'
            ),
            'evidence': f'sub={payload["sub"]}',
        })


def _check_jku_x5u(header, findings):
    """Check for JKU/X5U headers that enable algorithm confusion attacks."""
    for key in ('jku', 'x5u', 'jwk'):
        if key in header:
            severity = 'HIGH' if key in ('jku', 'x5u') else 'MEDIUM'
            findings.append({
                'title': f'JWT Contains {key.upper()} Header',
                'severity': severity,
                'category': 'jwt',
                'description': (
                    f'A JWT token includes the {key.upper()} header claim. '
                    f'{"This allows an attacker to point to a malicious key set, " if key != "jwk" else ""}'
                    f'enabling algorithm confusion attacks where the attacker '
                    f'signs a token with their own key.'
                ),
                'recommendation': (
                    'Use a strict allowlist of accepted JWKS URLs on the server. '
                    'Never trust the jku/x5u claims blindly. Prefer embedded keys '
                    'or server-side key references.'
                ),
                'evidence': f'JWT {key.upper()}={header[key]}',
            })


JWT_DEEP_CHECKS = [check_jwt_deep]