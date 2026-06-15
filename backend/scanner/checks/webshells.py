"""
Web shell detection (semi-active).

Probes common web shell paths to detect if any are publicly accessible.
Only uses safe GET requests and does not modify any data.
"""
import logging
import requests as req_lib
from .sensitive_files import _get_spa_baseline, _is_spa_false_positive

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10

WEBSHELL_PATHS = {
    'shell.php': {'severity': 'CRITICAL', 'desc': 'Common PHP web shell'},
    'cmd.php': {'severity': 'CRITICAL', 'desc': 'PHP command shell'},
    'uploader.php': {'severity': 'CRITICAL', 'desc': 'PHP file upload shell'},
    'b374k.php': {'severity': 'CRITICAL', 'desc': 'b374k PHP web shell'},
    'c99.php': {'severity': 'CRITICAL', 'desc': 'C99 PHP web shell'},
    'r57.php': {'severity': 'CRITICAL', 'desc': 'R57 PHP web shell'},
    'wso.php': {'severity': 'CRITICAL', 'desc': 'WSO PHP web shell'},
    'alfa.php': {'severity': 'CRITICAL', 'desc': 'Alfa PHP web shell'},
    'mini.php': {'severity': 'CRITICAL', 'desc': 'Mini PHP web shell'},
    'phpinfo.php': {'severity': 'HIGH', 'desc': 'PHP info disclosure'},
    'adminer.php': {'severity': 'HIGH', 'desc': 'Adminer database management tool'},
    'phpmyadmin/': {'severity': 'HIGH', 'desc': 'phpMyAdmin database interface'},
    'pma/': {'severity': 'HIGH', 'desc': 'phpMyAdmin alternative path'},
    'wp-admin/install.php': {'severity': 'MEDIUM', 'desc': 'WordPress install page'},
    'cgi-bin/': {'severity': 'MEDIUM', 'desc': 'CGI bin directory may expose scripts'},
    'test.php': {'severity': 'MEDIUM', 'desc': 'PHP test page'},
    'debug.php': {'severity': 'HIGH', 'desc': 'PHP debug page'},
    'console.php': {'severity': 'HIGH', 'desc': 'PHP console page'},
    'eval.php': {'severity': 'CRITICAL', 'desc': 'PHP eval shell'},
    'system.php': {'severity': 'CRITICAL', 'desc': 'PHP system command shell'},
    'backdoor.php': {'severity': 'CRITICAL', 'desc': 'PHP backdoor shell'},
    'webshell.php': {'severity': 'CRITICAL', 'desc': 'Generic PHP web shell'},
    'cmd.aspx': {'severity': 'CRITICAL', 'desc': 'ASP.NET command shell'},
    'shell.aspx': {'severity': 'CRITICAL', 'desc': 'ASP.NET web shell'},
    'admin.aspx': {'severity': 'HIGH', 'desc': 'ASP.NET admin page'},
    'webshell.jsp': {'severity': 'CRITICAL', 'desc': 'JSP web shell'},
    'cmd.jsp': {'severity': 'CRITICAL', 'desc': 'JSP command shell'},
    'manager/html': {'severity': 'HIGH', 'desc': 'Tomcat Manager interface'},
}


def check_webshells(response, parsed_url, findings):
    """Probe for common web shell paths."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    baseline_content = _get_spa_baseline(session, base_url, PROBE_TIMEOUT)

    found = []

    for path, info in WEBSHELL_PATHS.items():
        url = f'{base_url}/{path}'
        try:
            resp = session.get(
                url, timeout=PROBE_TIMEOUT,
                allow_redirects=True, verify=False,
            )

            if resp.status_code == 200 and len(resp.text) > 0:
                content = resp.text[:5000]
                if _is_spa_false_positive(content, baseline_content):
                    continue
                if _verify_webshell(path, content):
                    found.append({
                        'path': path,
                        'url': url,
                        'severity': info['severity'],
                        'desc': info['desc'],
                        'snippet': content[:150].replace('\n', ' '),
                    })
        except (req_lib.exceptions.RequestException, Exception):
            continue

    for item in found:
        findings.append({
            'title': f"Potential Web Shell: /{item['path']}",
            'severity': item['severity'],
            'category': 'webshell',
            'description': (
                f"A potentially dangerous file is accessible at /{item['path']}. "
                f"{item['desc']}. This could allow remote code execution."
            ),
            'recommendation': (
                'Remove the file immediately. Investigate how it was placed '
                'on the server. Ensure file upload validation is in place and '
                'review access logs for unauthorized access.'
            ),
            'evidence': f"Accessible at {item['url']} — snippet: {item['snippet'][:100]}",
        })


def _verify_webshell(path, content):
    """Verify that a response is likely a web shell, not a generic page."""
    content_lower = content.lower()

    if '<html' in content_lower[:500] and ('<!doctype' in content_lower[:500]):
        webshell_indicators = [
            'command', 'execute', 'shell', 'terminal', 'console',
            'upload', 'wget', 'curl', 'chmod', 'eval', 'system',
            'passwd', 'shadow', 'etc/', '/bin/', 'cmd.exe',
            'phpinfo', 'phpmyadmin', 'adminer', 'server_addr',
            'request_uri', 'document_root',
        ]
        return any(ind in content_lower for ind in webshell_indicators)

    if path.endswith('/'):
        return 'index of' in content_lower or 'directory listing' in content_lower

    if content.strip() and len(content.strip()) > 50:
        return True

    return False


WEBSHELL_CHECKS = [check_webshells]