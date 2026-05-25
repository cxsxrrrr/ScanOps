"""
Passive injection vulnerability checks.

Detects indicators of SQL injection, XSS, NoSQL injection,
OS command injection, XXE, and server-side template injection
by analyzing HTTP response content and headers.
"""
import re
import logging

logger = logging.getLogger('scanner')

# Compiled regex patterns for performance (compiled once at module load)
SQL_ERROR_PATTERNS = re.compile(
    r'(?:'
    r'You have an error in your SQL syntax'
    r'|mysql_fetch|mysql_num_rows|mysql_query'
    r'|pg_query\(\)|pg_exec\(\)'
    r'|ORA-\d{5}'
    r'|Microsoft OLE DB Provider'
    r'|Unclosed quotation mark'
    r'|SQLSTATE\['
    r'|SQLite3::query'
    r'|near\s+".*?":\s+syntax error'
    r'|Warning:.*?\bsqlite_\w+'
    r'|com\.mysql\.jdbc'
    r'|org\.postgresql\.util\.PSQLException'
    r')',
    re.IGNORECASE,
)

NOSQL_ERROR_PATTERNS = re.compile(
    r'(?:'
    r'MongoError'
    r'|MongoServerError'
    r'|MongoDB\.Driver'
    r'|mongoose\.Error'
    r'|E11000 duplicate key'
    r'|CastError.*ObjectId'
    r')',
    re.IGNORECASE,
)

CMD_PATTERNS = re.compile(
    r'(?:'
    r'sh:\s+\d+:\s+'
    r'|/bin/sh:'
    r'|command not found'
    r'|Operation not permitted'
    r'|Cannot run program'
    r'|java\.lang\.Runtime\.exec'
    r'|os\.system\('
    r')',
    re.IGNORECASE,
)

SSTI_PATTERNS = re.compile(
    r'(?:'
    r'jinja2\.exceptions\.'
    r'|Twig_Error'
    r'|freemarker\.template\.'
    r'|UndefinedError:'
    r'|TemplateSyntaxError'
    r'|mako\.exceptions\.'
    r'|Smarty Compiler:'
    r')',
    re.IGNORECASE,
)

# DOM XSS sinks — patterns in JavaScript that can lead to DOM-based XSS
DOM_XSS_SINKS = re.compile(
    r'(?:'
    r'\.innerHTML\s*='
    r'|document\.write\s*\('
    r'|document\.writeln\s*\('
    r'|\.outerHTML\s*='
    r'|eval\s*\('
    r'|setTimeout\s*\(\s*["\']'
    r'|setInterval\s*\(\s*["\']'
    r'|new\s+Function\s*\('
    r')',
    re.IGNORECASE,
)

# Limit response body analysis to avoid scanning huge pages
MAX_BODY_SIZE = 100_000


def _get_body(response):
    """Return the response body truncated to MAX_BODY_SIZE."""
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_sqli(response, parsed_url, findings):
    """Detect SQL error messages leaked in the response body."""
    body = _get_body(response)
    match = SQL_ERROR_PATTERNS.search(body)
    if match:
        findings.append({
            'title': 'Potential SQL Injection Indicator',
            'severity': 'HIGH',
            'category': 'sqli',
            'description': (
                'The response contains SQL error messages that may indicate '
                'improper input sanitization or debugging output left enabled.'
            ),
            'recommendation': (
                'Use parameterized queries or an ORM. Never interpolate user '
                'input into SQL. Disable detailed error messages in production.'
            ),
            'evidence': f'Pattern matched: {match.group()[:200]}',
        })


def check_xss(response, parsed_url, findings):
    """Detect XSS indicators: missing CSP, DOM sinks, reflected input."""
    headers = response.headers
    body = _get_body(response)

    # Check for dangerous DOM sinks in JavaScript
    dom_matches = DOM_XSS_SINKS.findall(body)
    if dom_matches:
        unique_sinks = list(set(m.strip() for m in dom_matches))[:5]
        findings.append({
            'title': 'DOM-Based XSS Sinks Detected',
            'severity': 'MEDIUM',
            'category': 'xss',
            'description': (
                'The page contains JavaScript patterns that could lead to '
                'DOM-based XSS if user-controlled data reaches these sinks.'
            ),
            'recommendation': (
                'Avoid using innerHTML, document.write, eval, and similar '
                'unsafe DOM APIs. Use textContent or safe templating instead.'
            ),
            'evidence': f'Sinks found: {", ".join(unique_sinks)}',
        })

    # Check for Content-Type without charset (can enable XSS via encoding)
    content_type = headers.get('Content-Type', '')
    if 'text/html' in content_type and 'charset' not in content_type.lower():
        findings.append({
            'title': 'Missing Charset in Content-Type',
            'severity': 'LOW',
            'category': 'xss',
            'description': (
                'The Content-Type header does not specify a charset, which '
                'could allow UTF-7 or other encoding-based XSS attacks.'
            ),
            'recommendation': 'Set Content-Type: text/html; charset=UTF-8.',
            'evidence': f'Content-Type: {content_type}',
        })


def check_nosql_injection(response, parsed_url, findings):
    """Detect NoSQL error messages in the response body."""
    body = _get_body(response)
    match = NOSQL_ERROR_PATTERNS.search(body)
    if match:
        findings.append({
            'title': 'Potential NoSQL Injection Indicator',
            'severity': 'HIGH',
            'category': 'nosqli',
            'description': (
                'The response contains NoSQL/MongoDB error messages that may '
                'indicate insufficient input validation.'
            ),
            'recommendation': (
                'Sanitize and validate all user inputs. Use query builders '
                'instead of raw query construction. Disable verbose errors.'
            ),
            'evidence': f'Pattern matched: {match.group()[:200]}',
        })


def check_cmd_injection(response, parsed_url, findings):
    """Detect OS command execution error patterns."""
    body = _get_body(response)

    # Check for cgi-bin exposure
    if '/cgi-bin/' in body:
        findings.append({
            'title': 'CGI-BIN Directory Detected',
            'severity': 'MEDIUM',
            'category': 'cmd_injection',
            'description': (
                'References to /cgi-bin/ were found. CGI scripts are historically '
                'vulnerable to command injection attacks.'
            ),
            'recommendation': (
                'Remove or restrict access to CGI scripts. Migrate to modern '
                'frameworks with proper input handling.'
            ),
            'evidence': 'References to /cgi-bin/ found in response.',
        })

    match = CMD_PATTERNS.search(body)
    if match:
        findings.append({
            'title': 'Potential OS Command Injection Indicator',
            'severity': 'HIGH',
            'category': 'cmd_injection',
            'description': (
                'The response contains shell error messages suggesting '
                'potential command execution on the server.'
            ),
            'recommendation': (
                'Never pass user input to shell commands. Use safe APIs '
                'and allowlists for any required system operations.'
            ),
            'evidence': f'Pattern matched: {match.group()[:200]}',
        })


def check_xxe(response, parsed_url, findings):
    """Detect XXE indicators: XML content-type and parser errors."""
    headers = response.headers
    content_type = headers.get('Content-Type', '')
    body = _get_body(response)

    # XML endpoints that accept external entities
    if 'xml' in content_type.lower():
        findings.append({
            'title': 'XML Content-Type Endpoint Detected',
            'severity': 'MEDIUM',
            'category': 'xxe',
            'description': (
                'The endpoint returns XML content. If the server parses XML '
                'input without disabling external entities, it may be vulnerable '
                'to XXE attacks.'
            ),
            'recommendation': (
                'Disable DTDs and external entity processing in the XML parser. '
                'Use JSON instead of XML where possible.'
            ),
            'evidence': f'Content-Type: {content_type}',
        })

    # XML parser error messages
    xxe_errors = re.search(
        r'(?:XMLParseError|SAXParseException|lxml\.etree|'
        r'simplexml_load|DOMDocument::load)',
        body,
        re.IGNORECASE,
    )
    if xxe_errors:
        findings.append({
            'title': 'XML Parser Error Disclosed',
            'severity': 'MEDIUM',
            'category': 'xxe',
            'description': (
                'XML parser error messages are visible in the response, '
                'revealing the parsing library in use.'
            ),
            'recommendation': (
                'Suppress detailed XML parser error output in production. '
                'Ensure external entity processing is disabled.'
            ),
            'evidence': f'Pattern matched: {xxe_errors.group()[:200]}',
        })


def check_ssti(response, parsed_url, findings):
    """Detect server-side template injection error patterns."""
    body = _get_body(response)
    match = SSTI_PATTERNS.search(body)
    if match:
        findings.append({
            'title': 'Potential Server-Side Template Injection',
            'severity': 'HIGH',
            'category': 'ssti',
            'description': (
                'Template engine error messages detected in the response. '
                'This may indicate that user input is being rendered unsafely '
                'within server-side templates.'
            ),
            'recommendation': (
                'Never pass user input directly into template rendering. '
                'Use sandboxed template environments and disable debug mode.'
            ),
            'evidence': f'Pattern matched: {match.group()[:200]}',
        })


# Export list of all injection check functions
INJECTION_CHECKS = [
    check_sqli,
    check_xss,
    check_nosql_injection,
    check_cmd_injection,
    check_xxe,
    check_ssti,
]
