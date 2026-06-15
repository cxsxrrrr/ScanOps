"""
Extended DNS security record checks.

Checks DKIM, DNSSEC, CAA, MX records, and validates SPF/DMARC policies
beyond the basic checks in the engine.
"""
import re
import logging
import subprocess

logger = logging.getLogger('scanner')

DNS_TIMEOUT = 10

COMMON_DKIM_SELECTORS = [
    'default', 'google', 'selector1', 'selector2',
    's1', 's2', 'mail', 'smtpapi', 'smtp',
    '20161025', '20170101', '20200101', '20210101',
    '20220101', '20230101', '20240101',
    'mesrv', 'k1', 'k2', 'm1', 'm2',
]


def check_dns_extended(response, parsed_url, findings):
    """Extended DNS security record checks."""
    hostname = parsed_url.hostname
    if not hostname:
        return

    _check_dkim(hostname, findings)
    _check_dnssec(hostname, findings)
    _check_caa(hostname, findings)
    _check_mx(hostname, findings)
    _check_spf_policy(hostname, findings)
    _check_dmarc_policy(hostname, findings)


def _nslookup(query_type, domain):
    """Run nslookup and return stdout or empty string."""
    try:
        result = subprocess.run(
            ['nslookup', '-type=' + query_type, domain],
            capture_output=True, text=True, timeout=DNS_TIMEOUT,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ''


def _dig(query_type, domain):
    """Run dig and return stdout or empty string (fallback)."""
    try:
        result = subprocess.run(
            ['dig', query_type, domain, '+short'],
            capture_output=True, text=True, timeout=DNS_TIMEOUT,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ''


def _check_dkim(hostname, findings):
    """Check DKIM records for common selectors."""
    found = False
    for selector in COMMON_DKIM_SELECTORS[:5]:
        dkim_domain = f'{selector}._domainkey.{hostname}'
        output = _nslookup('txt', dkim_domain)
        if 'v=dkim1' in output.lower() or 'p=' in output.lower():
            found = True
            break

    if not found:
        findings.append({
            'title': 'DKIM Record Not Found (Common Selectors)',
            'severity': 'LOW',
            'category': 'dns',
            'description': (
                'No DKIM record found for any common selector. DKIM helps '
                'prevent email spoofing by cryptographically signing outgoing '
                'emails. Without DKIM, attackers can more easily forge emails '
                'from your domain.'
            ),
            'recommendation': (
                'Set up DKIM signing for all email-sending services. '
                'Publish DKIM public keys in DNS and configure your mail '
                'server or email provider to sign outgoing messages.'
            ),
            'evidence': f'No DKIM record found for common selectors on {hostname}',
        })


def _check_dnssec(hostname, findings):
    """Check if the domain has DNSSEC enabled."""
    output = _nslookup('dnskey', hostname)

    has_dnskey = 'DNSKEY' in output or 'flags' in output.lower() and '256' in output

    if not has_dnskey:
        ds_output = _nslookup('ds', hostname)
        has_ds = 'DS' in ds_output and 'key tag' in ds_output.lower()

        if not has_ds:
            findings.append({
                'title': 'DNSSEC Not Enabled',
                'severity': 'LOW',
                'category': 'dns',
                'description': (
                    'The domain does not appear to have DNSSEC enabled. '
                    'Without DNSSEC, DNS responses can be spoofed or '
                    'tampered with in transit (DNS cache poisoning).'
                ),
                'recommendation': (
                    'Enable DNSSEC for your domain by signing your DNS zone '
                    'and publishing DS records at your registrar.'
                ),
                'evidence': f'No DNSKEY or DS records found for {hostname}',
            })


def _check_caa(hostname, findings):
    """Check if CAA records are configured."""
    output = _nslookup('caa', hostname)

    caa_found = False
    if 'issue' in output.lower() or 'issuewild' in output.lower():
        caa_found = True

    if not caa_found:
        dig_output = _dig('caa', hostname)
        if dig_output.strip():
            caa_found = True

    if not caa_found:
        findings.append({
            'title': 'CAA Record Missing',
            'severity': 'LOW',
            'category': 'dns',
            'description': (
                'No CAA (Certificate Authority Authorization) record found. '
                'Without CAA, any certificate authority can issue certificates '
                'for your domain, increasing the risk of unauthorized certificates.'
            ),
            'recommendation': (
                'Add CAA records to specify which certificate authorities '
                'are allowed to issue certificates for your domain. '
                'E.g., issue "letsencrypt.org"'
            ),
            'evidence': f'No CAA record found for {hostname}',
        })
    else:
        if 'issue ";"' in output or '0 issue ";"' in output:
            findings.append({
                'title': 'CAA Record Blocks All Certificate Issuance',
                'severity': 'INFO',
                'category': 'dns',
                'description': (
                    'CAA records are configured to block certificate issuance '
                    'by default. Ensure this is intentional and that you have '
                    'the certificates you need.'
                ),
                'recommendation': (
                    'If this is intentional, no action needed. Otherwise, '
                    'add CAA records to allow your preferred certificate authority.'
                ),
                'evidence': f'CAA issue directive found: ; (blocks all)',
            })


def _check_mx(hostname, findings):
    """Check MX records for the domain."""
    output = _nslookup('mx', hostname)

    if 'mail exchanger' not in output.lower() and 'mx' not in output.lower():
        findings.append({
            'title': 'No MX Records Found',
            'severity': 'LOW',
            'category': 'dns',
            'description': (
                'No MX (Mail Exchanger) records found for this domain. '
                'While not required for all domains, missing MX records '
                'can affect email delivery and prevent verification of '
                'email-based security policies.'
            ),
            'recommendation': (
                'Add MX records if this domain sends or receives email. '
                'If the domain does not handle email, ensure SPF and DMARC '
                'policies reflect this (e.g., v=spf1 -all).'
            ),
            'evidence': f'No MX records found for {hostname}',
        })


def _check_spf_policy(hostname, findings):
    """Analyze SPF policy for weakness."""
    output = _nslookup('txt', hostname)

    spf_match = re.search(r'"v=spf1([^"]*)"', output, re.IGNORECASE)
    if not spf_match:
        return

    spf_value = spf_match.group(0).strip('"')

    if '+all' in spf_value:
        findings.append({
            'title': 'SPF Policy Allows All Senders (+all)',
            'severity': 'HIGH',
            'category': 'dns',
            'description': (
                'The SPF record ends with "+all", which means any server '
                'in the world can send email on behalf of this domain. '
                'This completely defeats the purpose of SPF.'
            ),
            'recommendation': (
                'Change the SPF record to end with "~all" (softfail) or '
                '"-all" (hardfail). E.g., v=spf1 include:_spf.google.com ~all'
            ),
            'evidence': f'SPF: {spf_value}',
        })
    elif '?all' in spf_value:
        findings.append({
            'title': 'SPF Policy is Neutral (?all)',
            'severity': 'MEDIUM',
            'category': 'dns',
            'description': (
                'The SPF record ends with "?all" (neutral), which means '
                'receiving servers will not treat SPF failures as spam. '
                'This provides minimal protection.'
            ),
            'recommendation': (
                'Replace "?all" with "~all" (softfail) or "-all" (hardfail) '
                'to enforce SPF policy.'
            ),
            'evidence': f'SPF: {spf_value}',
        })
    elif '~all' in spf_value:
        findings.append({
            'title': 'SPF Uses Softfail (~all)',
            'severity': 'INFO',
            'category': 'dns',
            'description': (
                'The SPF record uses "~all" (softfail). While better than '
                '"?all" or "+all", softfail may still allow spoofed emails '
                'to pass some spam filters.'
            ),
            'recommendation': (
                'Consider using "-all" (hardfail) for stronger enforcement '
                'once SPF is validated and not causing delivery issues.'
            ),
            'evidence': f'SPF: {spf_value}',
        })

    if 'v=spf1' in output.lower():
        spf_count = output.lower().count('v=spf1')
        if spf_count > 1:
            findings.append({
                'title': 'Multiple SPF Records Detected',
                'severity': 'MEDIUM',
                'category': 'dns',
                'description': (
                    f'{spf_count} SPF records were found. Multiple SPF records '
                    f'will cause SPF validation to fail permanently, making '
                    f'your domain vulnerable to email spoofing.'
                ),
                'recommendation': (
                    'Combine all SPF records into a single TXT record. '
                    'Only one SPF record per domain is allowed.'
                ),
                'evidence': f'{spf_count} SPF records found',
            })

    dns_lookups = spf_value.lower().count('include:')
    redirects = spf_value.lower().count('redirect=')
    if (dns_lookups + redirects) > 10:
        findings.append({
            'title': f'SPF Record Exceeds DNS Lookup Limit ({dns_lookups})',
            'severity': 'MEDIUM',
            'category': 'dns',
            'description': (
                f'The SPF record requires {dns_lookups} DNS lookups, '
                f'exceeding the RFC limit of 10. This causes SPF to fail '
                f'with a PermError, making your domain vulnerable to spoofing.'
            ),
            'recommendation': (
                'Reduce the number of include directives. Consider using '
                'ip4/ip6 mechanisms instead of includes for frequently '
                'used sending services.'
            ),
            'evidence': f'SPF include count: {dns_lookups}',
        })


def _check_dmarc_policy(hostname, findings):
    """Analyze DMARC policy for weakness."""
    output = _nslookup('txt', f'_dmarc.{hostname}')

    if 'v=dmarc1' not in output.lower():
        return

    dmarc_match = re.search(r'"v=dmarc1;([^"]*)"', output, re.IGNORECASE)
    if not dmarc_match:
        return

    dmarc_value = dmarc_match.group(0).strip('"')

    if 'p=none' in dmarc_value.lower():
        findings.append({
            'title': 'DMARC Policy Set to None (p=none)',
            'severity': 'MEDIUM',
            'category': 'dns',
            'description': (
                'The DMARC policy is set to "p=none", which only monitors '
                'email authentication failures without taking any action. '
                'Spoofed emails will still be delivered.'
            ),
            'recommendation': (
                'Once DMARC reports are stable with low failure rates, '
                'change to "p=quarantine" or "p=reject" for enforcement.'
            ),
            'evidence': f'DMARC: {dmarc_value}',
        })
    elif 'p=quarantine' in dmarc_value.lower():
        findings.append({
            'title': 'DMARC Policy Set to Quarantine',
            'severity': 'INFO',
            'category': 'dns',
            'description': (
                'The DMARC policy is set to "p=quarantine", which sends '
                'failing emails to spam. This is a good intermediate policy.'
            ),
            'recommendation': (
                'Consider upgrading to "p=reject" once you have '
                'confidence in your email authentication setup.'
            ),
            'evidence': f'DMARC: {dmarc_value}',
        })

    if 'rua=' not in dmarc_value.lower() and 'ruf=' not in dmarc_value.lower():
        findings.append({
            'title': 'DMARC Missing Reporting Configuration',
            'severity': 'LOW',
            'category': 'dns',
            'description': (
                'The DMARC record does not include reporting addresses (rua/ruf). '
                'Without reporting, you cannot monitor authentication failures.'
            ),
            'recommendation': (
                'Add rua=mailto:dmarc@yourdomain.com to your DMARC record '
                'to receive aggregate reports. Consider ruf for forensic reports.'
            ),
            'evidence': f'DMARC: {dmarc_value}',
        })


DNS_EXTENDED_CHECKS = [check_dns_extended]