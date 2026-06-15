"""
Extended backup file probing (semi-active).

Probes for backup copies of discovered files and common config backups.
Only uses safe GET requests.
"""
import logging
import requests as req_lib
from .sensitive_files import _get_spa_baseline, _is_spa_false_positive

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10

BACKUP_SUFFIXES = {
    '.bak': 'Generic backup file',
    '.backup': 'Generic backup file',
    '.old': 'Old/previous version',
    '.orig': 'Original file backup',
    '.save': 'Saved file',
    '.swp': 'Vim swap file',
    '.swo': 'Vim swap file',
    '~': 'Linux backup convention',
    '.copy': 'Copy of file',
    '.tmp': 'Temporary file',
    '.temp': 'Temporary file',
    '.dist': 'Distribution file',
    '.dev': 'Development config',
    '.local': 'Local config file',
    '.staging': 'Staging config file',
    '.prod': 'Production config file',
    '.env.bak': 'Environment backup',
}

CONFIG_FILES = {
    '.env': 'Environment variables file',
    '.env.local': 'Local environment file',
    '.env.production': 'Production environment file',
    '.env.staging': 'Staging environment file',
    'composer.json': 'PHP Composer dependencies',
    'composer.lock': 'PHP Composer lock file',
    'package.json': 'Node.js package file',
    'package-lock.json': 'Node.js lock file',
    'yarn.lock': 'Yarn lock file',
    'Gemfile.lock': 'Ruby lock file',
    'pnpm-lock.yaml': 'pnpm lock file',
}


def check_backup_files(response, parsed_url, findings):
    """Probe for backup copies of configuration and source files."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    baseline_content = _get_spa_baseline(session, base_url, PROBE_TIMEOUT)

    found = []
    targets = _generate_targets(parsed_url.path)

    for path, desc in targets:
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
                if _is_likely_backup(path, content):
                    found.append({
                        'path': path,
                        'url': url,
                        'desc': desc,
                        'snippet': content[:150].replace('\n', ' '),
                    })
        except (req_lib.exceptions.RequestException, Exception):
            continue

    for item in found:
        severity = 'HIGH' if '.env' in item['path'] else 'MEDIUM'
        if item['path'].endswith(('.bak', '.backup', '.old', '~', '.swp')):
            severity = 'HIGH'

        findings.append({
            'title': f"Backup File Exposed: /{item['path']}",
            'severity': severity,
            'category': 'info_disclosure',
            'description': (
                f"A backup file is publicly accessible at /{item['path']}. "
                f"{item['desc']}. Backup files often contain credentials "
                f"or internal configuration that should not be public."
            ),
            'recommendation': (
                'Remove backup files from the web root. Add rules to block '
                'requests for backup file patterns (*.bak, *.old, *.swp, *~). '
                'Use .gitignore-equivalent rules on the web server.'
            ),
            'evidence': f"Accessible at {item['url']} — snippet: {item['snippet'][:100]}",
        })


def _generate_targets(current_path):
    """Generate backup file paths to probe based on the current URL path."""
    targets = []

    for suffix, desc in BACKUP_SUFFIXES.items():
        for config in list(CONFIG_FILES.keys())[:10]:
            targets.append((f'{config}{suffix}', f'{desc} — backup of {config}'))

    common_backups = [
        ('index.php.bak', 'PHP index backup'),
        ('index.html.bak', 'HTML index backup'),
        ('wp-config.php.bak', 'WordPress config backup'),
        ('wp-config.php.save', 'WordPress config saved'),
        ('wp-config.php~', 'WordPress config backup'),
        ('.htaccess.bak', 'Apache config backup'),
        ('.htpasswd.bak', 'Apache password backup'),
        ('nginx.conf.bak', 'Nginx config backup'),
        ('httpd.conf.bak', 'Apache httpd backup'),
        ('web.config.bak', 'ASP.NET config backup'),
        ('config.php.bak', 'PHP config backup'),
        ('config.json.bak', 'JSON config backup'),
        ('settings.py.bak', 'Django settings backup'),
        ('database.yml.bak', 'Database config backup'),
        ('Dockerfile.bak', 'Docker config backup'),
        ('docker-compose.yml.bak', 'Docker Compose backup'),
        ('id_rsa', 'SSH private key'),
        ('id_dsa', 'SSH DSA private key'),
        ('.ssh/id_rsa', 'SSH private key in .ssh'),
        ('backup.sql', 'SQL database dump'),
        ('database.sql', 'Database SQL dump'),
        ('dump.sql', 'Database dump file'),
        ('db_backup.zip', 'Database backup archive'),
        ('site_backup.tar.gz', 'Site backup archive'),
        ('backup.zip', 'Backup archive'),
        ('backup.tar', 'Backup tar archive'),
        ('backup.tar.gz', 'Backup compressed archive'),
        ('www.zip', 'Web root archive'),
        ('www.tar.gz', 'Web root compressed archive'),
        ('.git/HEAD', 'Git HEAD file'),
    ]
    targets.extend(common_backups)

    return targets[:40]


def _is_likely_backup(path, content):
    """Verify content looks like a backup/config file, not a generic HTML page."""
    content_lower = content.lower()

    if '<!doctype html' in content_lower[:100] and '<html' in content_lower[:500]:
        if '.env' not in path and 'config' not in path and 'composer' not in path:
            return False

    if path.endswith(('.sql', '.zip', '.tar', '.tar.gz', '.gz')):
        return True

    if path in ('id_rsa', 'id_dsa', '.ssh/id_rsa') or 'id_rsa' in path:
        return 'private key' in content_lower or 'begin rsa' in content_lower or len(content.strip()) > 0

    if '.env' in path:
        return '=' in content or 'export ' in content_lower or len(content.strip()) > 10

    if 'config' in path.lower() or path.endswith(('.json', '.yml', '.yaml', '.py')):
        return len(content.strip()) > 20

    if path.endswith(('.bak', '.backup', '.old', '.orig', '.save')):
        return len(content.strip()) > 10

    return len(content.strip()) > 10


BACKUP_FILES_CHECKS = [check_backup_files]