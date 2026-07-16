"""
Passive WordPress security scanner.

Detects WordPress installations and checks for:
- Version disclosure and outdated versions
- Theme and plugin enumeration
- User enumeration via REST API and author archives
- Common misconfigurations (xmlrpc, debug.log, directory listing, etc.)
"""
import re
import logging
import requests as req_lib

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 200_000

# WordPress version that is considered "current" — update periodically
CURRENT_WP_MAJOR = 6

# Known dangerous plugins (slug -> reason)
DANGEROUS_PLUGINS = {
    'revslider': 'Revolution Slider — historically critical file disclosure vulnerabilities',
    'gravity-forms': 'Gravity Forms — multiple known RCE and injection vulnerabilities',
    'duplicator': 'Duplicator — known installer file exposure vulnerabilities',
    'wp-file-manager': 'WP File Manager — critical unauthenticated file upload (CVE-2020-25213)',
    'easy-wp-smtp': 'Easy WP SMTP — debug log credential exposure',
    'nextgen-gallery': 'NextGEN Gallery — SQL injection vulnerabilities',
    'loginizer': 'Loginizer — SQL injection in login tracking',
    'flavflavor': 'flavor — file disclosure vulnerability',
}

# Paths to probe for misconfigurations
WP_PROBE_PATHS = {
    'xmlrpc': '/xmlrpc.php',
    'wp_config_bak': '/wp-config.php.bak',
    'wp_config_old': '/wp-config.php~',
    'wp_config_save': '/wp-config.php.save',
    'wp_config_txt': '/wp-config.txt',
    'debug_log': '/wp-content/debug.log',
    'uploads_listing': '/wp-content/uploads/',
    'includes_listing': '/wp-includes/',
    'wp_cron': '/wp-cron.php',
    'readme': '/readme.html',
    'registration': '/wp-login.php?action=register',
    'users_api': '/wp-json/wp/v2/users',
}


def _get_body(response):
    """Return truncated response body."""
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def detect_wordpress(response):
    """
    Check if the target is a WordPress site.

    Returns True if WordPress indicators are found.
    """
    body = _get_body(response)
    headers = response.headers

    indicators = [
        'wp-content/' in body,
        'wp-includes/' in body,
        'WordPress' in headers.get('X-Powered-By', ''),
        bool(re.search(
            r'<meta\s+name=["\']generator["\']\s+content=["\']WordPress',
            body, re.IGNORECASE,
        )),
        '/wp-json/' in body,
        'wp-embed.min.js' in body,
    ]

    return any(indicators)


def extract_wp_version(response, session, base_url):
    """
    Try to extract the WordPress version from multiple sources.

    Returns version string or None.
    """
    body = _get_body(response)

    # 1. Meta generator tag
    match = re.search(
        r'<meta\s+name=["\']generator["\']\s+content=["\']WordPress\s+([\d.]+)',
        body, re.IGNORECASE,
    )
    if match:
        return match.group(1)

    # 2. RSS/Atom feed generator
    try:
        feed_resp = session.get(
            f'{base_url}/feed/', timeout=10, allow_redirects=True, verify=False,
        )
        feed_match = re.search(
            r'<generator>https?://wordpress\.org/\?v=([\d.]+)</generator>',
            feed_resp.text[:50_000], re.IGNORECASE,
        )
        if feed_match:
            return feed_match.group(1)
    except req_lib.exceptions.RequestException:
        pass

    # 3. readme.html
    try:
        readme_resp = session.get(
            f'{base_url}/readme.html', timeout=10, allow_redirects=True, verify=False,
        )
        if readme_resp.status_code == 200:
            readme_match = re.search(
                r'Version\s+([\d.]+)', readme_resp.text[:10_000],
            )
            if readme_match:
                return readme_match.group(1)
    except req_lib.exceptions.RequestException:
        pass

    return None


def enumerate_themes(body):
    """Extract active theme(s) from page source."""
    themes = set()
    for match in re.finditer(
        r'wp-content/themes/([a-zA-Z0-9_-]+)/', body, re.IGNORECASE,
    ):
        themes.add(match.group(1))
    return themes


def enumerate_plugins(body):
    """Extract plugins referenced in page source."""
    plugins = set()
    for match in re.finditer(
        r'wp-content/plugins/([a-zA-Z0-9_-]+)/', body, re.IGNORECASE,
    ):
        plugins.add(match.group(1))
    return plugins


def check_wordpress(response, session, base_url, findings):
    """
    Run all WordPress-specific security checks.

    This is the main entry point called by the scan engine.
    Only runs if WordPress is detected.
    """
    if not detect_wordpress(response):
        return

    body = _get_body(response)

    findings.append({
        'title': 'WordPress Installation Detected',
        'severity': 'INFO',
        'category': 'wordpress',
        'description': 'The target is running WordPress.',
        'recommendation': 'Ensure WordPress core, themes, and plugins are kept up to date.',
        'evidence': 'WordPress indicators found in page source.',
    })

    # --- Version check ---
    version = extract_wp_version(response, session, base_url)
    if version:
        findings.append({
            'title': f'WordPress Version Disclosed: {version}',
            'severity': 'LOW',
            'category': 'wordpress',
            'description': (
                f'WordPress version {version} is disclosed. '
                'Version information helps attackers find known vulnerabilities.'
            ),
            'recommendation': (
                'Remove the generator meta tag. Add '
                "remove_action('wp_head', 'wp_generator') to your theme's functions.php."
            ),
            'evidence': f'WordPress version: {version}',
        })

        # Check if outdated
        try:
            major = int(version.split('.')[0])
            if major < CURRENT_WP_MAJOR:
                findings.append({
                    'title': f'Outdated WordPress Version: {version}',
                    'severity': 'HIGH',
                    'category': 'wordpress',
                    'description': (
                        f'WordPress {version} is outdated. Older versions have '
                        'known security vulnerabilities that are actively exploited.'
                    ),
                    'recommendation': (
                        f'Update to the latest WordPress {CURRENT_WP_MAJOR}.x release immediately.'
                    ),
                    'evidence': f'Detected version: {version}, current major: {CURRENT_WP_MAJOR}',
                })
        except (ValueError, IndexError):
            pass

    # --- Theme enumeration ---
    themes = enumerate_themes(body)
    if themes:
        findings.append({
            'title': f'WordPress Themes Detected: {", ".join(sorted(themes))}',
            'severity': 'INFO',
            'category': 'wordpress',
            'description': (
                f'{len(themes)} theme(s) detected: {", ".join(sorted(themes))}. '
                'Themes should be kept updated to prevent exploitation.'
            ),
            'recommendation': 'Keep all themes updated. Remove unused themes.',
            'evidence': f'Themes: {", ".join(sorted(themes))}',
        })

    # --- Plugin enumeration ---
    plugins = enumerate_plugins(body)
    if plugins:
        findings.append({
            'title': f'WordPress Plugins Detected ({len(plugins)})',
            'severity': 'LOW',
            'category': 'wordpress',
            'description': (
                f'{len(plugins)} plugin(s) detected: {", ".join(sorted(plugins))}. '
                'Each plugin increases the attack surface.'
            ),
            'recommendation': (
                'Keep all plugins updated. Remove unused plugins. '
                'Only use plugins from trusted sources.'
            ),
            'evidence': f'Plugins: {", ".join(sorted(plugins))}',
        })

        # Check for known dangerous plugins
        for plugin_slug in plugins:
            slug_lower = plugin_slug.lower()
            if slug_lower in DANGEROUS_PLUGINS:
                findings.append({
                    'title': f'High-Risk Plugin: {plugin_slug}',
                    'severity': 'HIGH',
                    'category': 'wordpress',
                    'description': DANGEROUS_PLUGINS[slug_lower],
                    'recommendation': (
                        f'Verify that {plugin_slug} is updated to the latest version. '
                        'Consider alternatives if the plugin is no longer maintained.'
                    ),
                    'evidence': f'Plugin detected: {plugin_slug}',
                })

    # --- Misconfiguration probes ---
    _check_xmlrpc(session, base_url, findings)
    _check_debug_log(session, base_url, findings)
    _check_config_backups(session, base_url, findings)
    _check_directory_listing(session, base_url, findings)
    _check_user_enumeration(session, base_url, findings)
    _check_registration(session, base_url, findings)
    _check_readme(session, base_url, findings)
    _check_wp_cron(session, base_url, findings)
    _check_rest_api_open(session, base_url, findings)


# ------------------------------------------------------------------
# Individual misconfiguration checks
# ------------------------------------------------------------------

def _check_xmlrpc(session, base_url, findings):
    """Check if xmlrpc.php is enabled."""
    try:
        resp = session.post(
            f'{base_url}/xmlrpc.php',
            data='<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>',
            headers={'Content-Type': 'text/xml'},
            timeout=10, verify=False,
        )
        if resp.status_code == 200 and 'methodResponse' in resp.text:
            findings.append({
                'title': 'XML-RPC Interface Enabled',
                'severity': 'MEDIUM',
                'category': 'wordpress',
                'description': (
                    'The XML-RPC interface is enabled and accepts method calls. '
                    'This can be used for brute-force amplification attacks '
                    'and DDoS via pingback abuse.'
                ),
                'recommendation': (
                    'Disable XML-RPC if not needed. Use a plugin like '
                    '"Disable XML-RPC" or block via .htaccess/nginx config.'
                ),
                'evidence': 'xmlrpc.php responds to system.listMethods',
            })
    except req_lib.exceptions.RequestException:
        pass


def _check_debug_log(session, base_url, findings):
    """Check if WordPress debug log is publicly accessible."""
    try:
        resp = session.get(
            f'{base_url}/wp-content/debug.log',
            timeout=10, verify=False,
        )
        if resp.status_code == 200 and len(resp.text) > 50:
            # Check if it looks like a real log file
            if 'PHP' in resp.text or 'WordPress' in resp.text or 'Error' in resp.text:
                findings.append({
                    'title': 'WordPress Debug Log Exposed',
                    'severity': 'CRITICAL',
                    'category': 'wordpress',
                    'description': (
                        'The WordPress debug log is publicly accessible. '
                        'It may contain sensitive information including file paths, '
                        'database queries, credentials, and internal errors.'
                    ),
                    'recommendation': (
                        'Delete the debug.log file. Set WP_DEBUG to false in production. '
                        'If debugging is needed, use WP_DEBUG_LOG with a non-public path.'
                    ),
                    'evidence': f'debug.log accessible at {base_url}/wp-content/debug.log',
                })
    except req_lib.exceptions.RequestException:
        pass


def _check_config_backups(session, base_url, findings):
    """Check for exposed wp-config.php backup files."""
    backup_paths = [
        '/wp-config.php.bak', '/wp-config.php~',
        '/wp-config.php.save', '/wp-config.txt',
        '/wp-config.php.old', '/wp-config.php.orig',
        '/wp-config.bak', '/wp-config.old',
    ]

    for path in backup_paths:
        try:
            resp = session.get(
                f'{base_url}{path}', timeout=10, verify=False,
            )
            if resp.status_code == 200 and 'DB_NAME' in resp.text:
                findings.append({
                    'title': 'WordPress Configuration Backup Exposed',
                    'severity': 'CRITICAL',
                    'category': 'wordpress',
                    'description': (
                        f'A backup of wp-config.php was found at {path}. '
                        'This file contains database credentials, authentication '
                        'keys, and other sensitive configuration data.'
                    ),
                    'recommendation': (
                        'Delete all backup files from the web server immediately. '
                        'Rotate database credentials and WordPress salts.'
                    ),
                    'evidence': f'wp-config backup at {base_url}{path}',
                })
                return  # One finding is enough
        except req_lib.exceptions.RequestException:
            continue


def _check_directory_listing(session, base_url, findings):
    """Check for directory listing on sensitive WordPress directories."""
    dirs = {
        '/wp-content/uploads/': 'Uploads directory',
        '/wp-includes/': 'WordPress includes directory',
        '/wp-content/plugins/': 'Plugins directory',
        '/wp-content/themes/': 'Themes directory',
    }

    for path, label in dirs.items():
        try:
            resp = session.get(
                f'{base_url}{path}', timeout=10, verify=False,
            )
            if resp.status_code == 200 and (
                '<title>Index of' in resp.text
                or 'Parent Directory' in resp.text
                or 'Directory listing for' in resp.text
            ):
                findings.append({
                    'title': f'Directory Listing: {label}',
                    'severity': 'MEDIUM',
                    'category': 'wordpress',
                    'description': (
                        f'{label} ({path}) has directory listing enabled. '
                        'Attackers can browse files and discover sensitive content.'
                    ),
                    'recommendation': (
                        'Disable directory listing in your web server configuration. '
                        'Add an empty index.php to each directory.'
                    ),
                    'evidence': f'Directory listing at {base_url}{path}',
                })
        except req_lib.exceptions.RequestException:
            continue


def _check_user_enumeration(session, base_url, findings):
    """Check for user enumeration via REST API and author archives."""
    users_found = []

    # REST API method
    try:
        resp = session.get(
            f'{base_url}/wp-json/wp/v2/users',
            timeout=10, verify=False,
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    for user in data[:10]:
                        name = user.get('name', user.get('slug', 'unknown'))
                        users_found.append(name)
            except ValueError:
                pass
    except req_lib.exceptions.RequestException:
        pass

    # Author archive method (fallback)
    if not users_found:
        for author_id in range(1, 6):
            try:
                resp = session.get(
                    f'{base_url}/?author={author_id}',
                    timeout=10, verify=False, allow_redirects=False,
                )
                if resp.status_code in (301, 302):
                    location = resp.headers.get('Location', '')
                    match = re.search(r'/author/([^/]+)', location)
                    if match:
                        users_found.append(match.group(1))
            except req_lib.exceptions.RequestException:
                continue

    if users_found:
        severity = 'HIGH' if 'admin' in [u.lower() for u in users_found] else 'MEDIUM'
        findings.append({
            'title': f'WordPress User Enumeration ({len(users_found)} users)',
            'severity': severity,
            'category': 'wordpress',
            'description': (
                f'{len(users_found)} WordPress user(s) discovered: '
                f'{", ".join(users_found[:10])}. '
                'User enumeration enables targeted brute-force attacks.'
                + (' The default "admin" user exists, making attacks easier.'
                   if 'admin' in [u.lower() for u in users_found] else '')
            ),
            'recommendation': (
                'Disable the REST API users endpoint for unauthenticated users. '
                'Rename the default admin account. Use a security plugin to '
                'block user enumeration.'
            ),
            'evidence': f'Users: {", ".join(users_found[:10])}',
        })


def _check_registration(session, base_url, findings):
    """Check if WordPress user registration is open."""
    try:
        resp = session.get(
            f'{base_url}/wp-login.php?action=register',
            timeout=10, verify=False, allow_redirects=False,
        )
        # If registration is open, it returns 200 with the registration form
        if resp.status_code == 200 and 'user_login' in resp.text:
            findings.append({
                'title': 'WordPress Registration Open',
                'severity': 'MEDIUM',
                'category': 'wordpress',
                'description': (
                    'WordPress user registration is open. Anyone can create '
                    'an account, which may lead to privilege escalation if '
                    'default roles are misconfigured.'
                ),
                'recommendation': (
                    'Disable user registration if not needed (Settings → General). '
                    'If needed, ensure the default role is "Subscriber" and use '
                    'CAPTCHA on the registration form.'
                ),
                'evidence': f'Registration form accessible at {base_url}/wp-login.php?action=register',
            })
    except req_lib.exceptions.RequestException:
        pass


def _check_readme(session, base_url, findings):
    """Check if readme.html is accessible (reveals version)."""
    try:
        resp = session.get(
            f'{base_url}/readme.html',
            timeout=10, verify=False,
        )
        if resp.status_code == 200 and 'WordPress' in resp.text:
            findings.append({
                'title': 'WordPress readme.html Accessible',
                'severity': 'LOW',
                'category': 'wordpress',
                'description': (
                    'The WordPress readme.html file is publicly accessible. '
                    'It reveals the WordPress version and installation details.'
                ),
                'recommendation': (
                    'Delete readme.html from the WordPress root directory '
                    'or block access via web server configuration.'
                ),
                'evidence': f'readme.html accessible at {base_url}/readme.html',
            })
    except req_lib.exceptions.RequestException:
        pass


def _check_wp_cron(session, base_url, findings):
    """Check if wp-cron.php is publicly accessible."""
    try:
        resp = session.get(
            f'{base_url}/wp-cron.php',
            timeout=10, verify=False,
        )
        if resp.status_code == 200:
            findings.append({
                'title': 'WP-Cron Publicly Accessible',
                'severity': 'LOW',
                'category': 'wordpress',
                'description': (
                    'wp-cron.php is publicly accessible. An attacker could '
                    'trigger scheduled tasks or use it for DoS attacks by '
                    'making repeated requests.'
                ),
                'recommendation': (
                    'Disable WP-Cron and use a real cron job instead. '
                    "Add define('DISABLE_WP_CRON', true) to wp-config.php."
                ),
                'evidence': f'wp-cron.php accessible at {base_url}/wp-cron.php',
            })
    except req_lib.exceptions.RequestException:
        pass


def _check_rest_api_open(session, base_url, findings):
    """Check if the WordPress REST API is fully open."""
    try:
        resp = session.get(
            f'{base_url}/wp-json/',
            timeout=10, verify=False,
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
                namespaces = data.get('namespaces', [])
                if 'wp/v2' in namespaces:
                    findings.append({
                        'title': 'WordPress REST API Fully Open',
                        'severity': 'LOW',
                        'category': 'wordpress',
                        'description': (
                            'The WordPress REST API is accessible without authentication. '
                            'This exposes site information, post content, and '
                            'potentially user data to anyone.'
                        ),
                        'recommendation': (
                            'Restrict REST API access for unauthenticated users. '
                            'Use a plugin or custom code to limit which endpoints '
                            'are publicly accessible.'
                        ),
                        'evidence': f'REST API namespaces: {", ".join(namespaces[:5])}',
                    })
            except ValueError:
                pass
    except req_lib.exceptions.RequestException:
        pass
