"""
Semi-active sensitive file and path probing.

Probes common sensitive paths (.env, .git, backups, config files, etc.)
to determine if they are publicly accessible. Only uses safe GET requests
and does not modify any data on the target server.
"""
import logging
import requests as req_lib

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10
MAX_PROBES = 40

SENSITIVE_PATHS = {
    '.env': {'severity': 'CRITICAL', 'desc': 'Environment variables file exposing secrets'},
    '.env.local': {'severity': 'CRITICAL', 'desc': 'Local environment variables file'},
    '.env.production': {'severity': 'CRITICAL', 'desc': 'Production environment variables'},
    '.env.staging': {'severity': 'CRITICAL', 'desc': 'Staging environment variables'},
    '.git/config': {'severity': 'CRITICAL', 'desc': 'Git configuration file — repository may be cloneable'},
    '.git/HEAD': {'severity': 'CRITICAL', 'desc': 'Git HEAD file — repository structure exposed'},
    '.gitignore': {'severity': 'LOW', 'desc': 'Git ignore file reveals project structure'},
    '.DS_Store': {'severity': 'MEDIUM', 'desc': 'macOS directory metadata exposing file structure'},
    'robots.txt': {'severity': 'INFO', 'desc': 'Robots.txt — may reveal disallowed paths'},
    'sitemap.xml': {'severity': 'INFO', 'desc': 'Sitemap — reveals site structure'},
    'wp-config.php.bak': {'severity': 'CRITICAL', 'desc': 'WordPress config backup with database credentials'},
    'web.config': {'severity': 'MEDIUM', 'desc': 'ASP.NET configuration file'},
    'package.json': {'severity': 'LOW', 'desc': 'Node.js package file revealing dependencies'},
    'composer.json': {'severity': 'LOW', 'desc': 'PHP Composer file revealing dependencies'},
    'Gemfile': {'severity': 'LOW', 'desc': 'Ruby Gemfile revealing dependencies'},
    'Dockerfile': {'severity': 'MEDIUM', 'desc': 'Docker build configuration exposing infrastructure'},
    'docker-compose.yml': {'severity': 'MEDIUM', 'desc': 'Docker Compose config exposing service architecture'},
    'docker-compose.yaml': {'severity': 'MEDIUM', 'desc': 'Docker Compose config exposing service architecture'},
    '.htaccess': {'severity': 'MEDIUM', 'desc': 'Apache configuration file'},
    '.htpasswd': {'severity': 'CRITICAL', 'desc': 'Apache password file with hashed credentials'},
    'nginx.conf': {'severity': 'MEDIUM', 'desc': 'Nginx configuration file'},
    'httpd.conf': {'severity': 'MEDIUM', 'desc': 'Apache httpd configuration'},
    'config.yml': {'severity': 'HIGH', 'desc': 'Configuration file — may contain secrets'},
    'config.yaml': {'severity': 'HIGH', 'desc': 'Configuration file — may contain secrets'},
    'config.json': {'severity': 'HIGH', 'desc': 'Configuration file — may contain secrets'},
    'config.php': {'severity': 'HIGH', 'desc': 'PHP configuration file — may contain secrets'},
    'settings.py': {'severity': 'MEDIUM', 'desc': 'Django settings file'},
    'database.yml': {'severity': 'CRITICAL', 'desc': 'Database configuration — contains credentials'},
    '.svn/entries': {'severity': 'HIGH', 'desc': 'SVN metadata — repository information exposed'},
    '.hg/store': {'severity': 'HIGH', 'desc': 'Mercurial repository data exposed'},
    'backup/': {'severity': 'MEDIUM', 'desc': 'Backup directory — may contain database dumps'},
    'backups/': {'severity': 'MEDIUM', 'desc': 'Backups directory — may contain database dumps'},
    'db/': {'severity': 'MEDIUM', 'desc': 'Database directory — may contain data files'},
    '.well-known/security.txt': {'severity': 'INFO', 'desc': 'Security contact information'},
    'crossdomain.xml': {'severity': 'LOW', 'desc': 'Flash cross-domain policy — may allow cross-origin access'},
    'clientaccesspolicy.xml': {'severity': 'LOW', 'desc': 'Silverlight cross-domain policy'},
    'elmah.axd': {'severity': 'HIGH', 'desc': 'ELMAH error log — exposes detailed errors'},
    'trace.axd': {'severity': 'HIGH', 'desc': 'ASP.NET trace viewer — exposes request details'},
    'server-status': {'severity': 'MEDIUM', 'desc': 'Apache server status page'},
    'server-info': {'severity': 'MEDIUM', 'desc': 'Apache server info page'},
    'actuator/health': {'severity': 'MEDIUM', 'desc': 'Spring Boot Actuator health endpoint'},
    'actuator/env': {'severity': 'HIGH', 'desc': 'Spring Boot Actuator env — exposes configuration'},
    'actuator/beans': {'severity': 'MEDIUM', 'desc': 'Spring Boot Actuator beans — exposes internal structure'},
    'phpinfo.php': {'severity': 'HIGH', 'desc': 'PHP info page — exposes server configuration'},
    'test.php': {'severity': 'LOW', 'desc': 'PHP test page'},
    'info.php': {'severity': 'HIGH', 'desc': 'PHP info page — exposes server configuration'},
    '.vscode/settings.json': {'severity': 'LOW', 'desc': 'VS Code settings — reveals project configuration'},
    '.idea/workspace.xml': {'severity': 'LOW', 'desc': 'IntelliJ workspace — reveals project structure'},
    'wp-content/debug.log': {'severity': 'CRITICAL', 'desc': 'WordPress debug log — may expose errors and paths'},
}

SECRET_PATTERNS = [
    'DB_PASSWORD', 'DATABASE_URL', 'SECRET_KEY', 'APP_KEY',
    'API_KEY', 'PRIVATE_KEY', 'AWS_SECRET', 'AWS_ACCESS',
    'SENDGRID_API_KEY', 'STRIPE_SECRET', 'MAIL_PASSWORD',
    'MONGO_URI', 'REDIS_URL', 'POSTGRES_PASSWORD',
    'password=', 'passwd=', 'pwd=',
]


def _get_spa_baseline(session, base_url, timeout):
    """Fetch the baseline response for the root URL to detect SPA false positives."""
    try:
        resp = session.get(
            base_url, timeout=timeout,
            allow_redirects=True, verify=False,
        )
        if resp.status_code == 200 and len(resp.text) > 0:
            return resp.text[:5000]
    except (req_lib.exceptions.RequestException, Exception):
        pass
    return None


def _is_spa_false_positive(path_content, baseline_content):
    """Check if a response is just the SPA shell returning the same page for all routes."""
    if not baseline_content:
        return False
    path_stripped = path_content.strip()
    baseline_stripped = baseline_content.strip()
    if path_stripped == baseline_stripped:
        return True
    if len(path_stripped) > 0 and len(baseline_stripped) > 0:
        overlap = len(set(path_stripped[:2000]) & set(baseline_stripped[:2000]))
        total = max(len(set(path_stripped[:2000])), len(set(baseline_stripped[:2000])), 1)
        if overlap / total > 0.95:
            return True
    return False


def check_sensitive_files(response, parsed_url, findings):
    """Probe common sensitive paths to check if they are publicly accessible."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    baseline_content = _get_spa_baseline(session, base_url, PROBE_TIMEOUT)

    found = []

    for path, info in list(SENSITIVE_PATHS.items())[:MAX_PROBES]:
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
                if _verify_content(path, content):
                    found.append({
                        'path': path,
                        'url': url,
                        'severity': info['severity'],
                        'desc': info['desc'],
                        'content_snippet': resp.text[:200].replace('\n', ' '),
                    })
        except (req_lib.exceptions.RequestException, Exception):
            continue

    if not found:
        return

    for item in found:
        findings.append({
            'title': f"Sensitive File Exposed: /{item['path']}",
            'severity': item['severity'],
            'category': 'access_control',
            'description': (
                f"A sensitive file is publicly accessible at /{item['path']}. "
                f"{item['desc']}. This file may expose credentials, configuration, "
                f"or internal application details."
            ),
            'recommendation': _get_remediation(item['path']),
            'evidence': f"Accessible at {item['url']} — snippet: {item['content_snippet'][:150]}",
        })


def _verify_content(path, content):
    """Basic content verification to reduce false positives."""
    if path == 'robots.txt':
        return 'user-agent' in content.lower() or 'disallow' in content.lower()
    if path == 'sitemap.xml':
        return '<urlset' in content.lower() or '<sitemapindex' in content.lower()
    if path.endswith('.json'):
        return '{' in content[:5] or '[' in content[:5]
    if path.endswith('.yml') or path.endswith('.yaml'):
        return ':' in content and ('\n' in content or '---' in content)
    if path.endswith('.xml'):
        return '<?xml' in content.lower() or '<' in content[:20]
    if 'config' in path or '.env' in path:
        if '<html' in content[:500].lower() or '<!doctype' in content[:500].lower():
            return False
        for pattern in SECRET_PATTERNS:
            if pattern.lower() in content.lower():
                return True
        return len(content.strip()) > 10 and '=' in content
    if path.startswith('.git/'):
        return 'ref:' in content or '[branch' in content or '[core]' in content
    if path.endswith('/'):
        return 'index of' in content.lower() or 'parent directory' in content.lower()
    return True


def _get_remediation(path):
    """Return path-specific remediation advice."""
    if path.startswith('.env') or 'config' in path:
        return (
            'Remove this file from public access immediately. '
            'Never commit environment files to version control. '
            'Use environment variables injected at deployment time.'
        )
    if '.git' in path:
        return (
            'Block access to the .git directory via web server configuration. '
            'In Apache: RedirectMatch 404 /\\.git. In Nginx: location ~ /\\.git { deny all; }'
        )
    if path in ('phpinfo.php', 'info.php'):
        return 'Remove phpinfo pages from production servers. Disable phpinfo() in production.'
    if path.startswith('actuator/'):
        return (
            'Restrict Spring Boot Actuator endpoints. Set management.endpoints.web.exposure.exclude='
            '"*" or limit to health and info only. Require authentication for actuator access.'
        )
    if 'backup' in path or 'db/' in path:
        return (
            'Remove backup files from the web root. Store backups outside '
            'the document root and restrict access via server configuration.'
        )
    return (
        'Restrict access to this file via web server configuration. '
        'Move sensitive files outside the web root directory.'
    )


SENSITIVE_FILES_CHECKS = [check_sensitive_files]