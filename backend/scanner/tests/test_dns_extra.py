"""Tests for the extended DNS checks (CAA, DKIM, DNSSEC, MTA-STS, TLS-RPT,
zone transfer) added to ScanEngine._check_dns_records / _check_zone_transfer.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase

from scanner.engine import ScanEngine


def _run_result(stdout=''):
    result = MagicMock()
    result.stdout = stdout
    return result


class DnsExtraRecordsTest(TestCase):
    """All records present → no findings from the new checks."""

    def _all_good_side_effect(self, args, **kwargs):
        record_type = args[1]
        name = args[2]
        if record_type == '-type=txt' and name.startswith('default._domainkey'):
            return _run_result('v=DKIM1; k=rsa; p=abc')
        if record_type == '-type=txt' and '_domainkey' in name:
            return _run_result('')  # other selectors: nothing
        if record_type == '-type=txt' and name.startswith('_mta-sts'):
            return _run_result('v=STSv1; id=123')
        if record_type == '-type=txt' and name.startswith('_smtp._tls'):
            return _run_result('v=TLSRPTv1; rua=mailto:test@example.com')
        if record_type == '-type=txt' and name.startswith('_dmarc'):
            return _run_result('v=DMARC1; p=reject')
        if record_type == '-type=txt':
            return _run_result('v=spf1 include:_spf.example.com ~all')
        if record_type == '-type=caa':
            return _run_result('example.com  rdata_257 = 0 issue "letsencrypt.org"')
        if record_type == '-type=dnskey':
            return _run_result('example.com  rdata_48 = 257 3 8 AwEAA...')
        return _run_result('')

    def test_all_records_present_no_findings(self):
        engine = ScanEngine('https://example.com')
        with patch('subprocess.run', side_effect=self._all_good_side_effect):
            engine._check_dns_records('example.com')
        self.assertEqual(engine.findings, [])

    def test_missing_caa_flagged(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if args[1] == '-type=caa':
                return _run_result('')  # no CAA record
            return self._all_good_side_effect(args, **kwargs)

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_dns_records('example.com')

        titles = [f['title'] for f in engine.findings]
        self.assertIn('Missing CAA Record', titles)

    def test_missing_dnssec_flagged(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if args[1] == '-type=dnskey':
                return _run_result('')
            return self._all_good_side_effect(args, **kwargs)

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_dns_records('example.com')

        titles = [f['title'] for f in engine.findings]
        self.assertIn('DNSSEC Not Enabled', titles)

    def test_missing_dkim_flagged(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if '_domainkey' in args[2]:
                return _run_result('')
            return self._all_good_side_effect(args, **kwargs)

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_dns_records('example.com')

        titles = [f['title'] for f in engine.findings]
        self.assertIn('No DKIM Record Found (Common Selectors)', titles)

    def test_missing_mta_sts_flagged(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if args[2].startswith('_mta-sts'):
                return _run_result('')
            return self._all_good_side_effect(args, **kwargs)

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_dns_records('example.com')

        titles = [f['title'] for f in engine.findings]
        self.assertIn('Missing MTA-STS Record', titles)

    def test_missing_tls_rpt_flagged(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if args[2].startswith('_smtp._tls'):
                return _run_result('')
            return self._all_good_side_effect(args, **kwargs)

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_dns_records('example.com')

        titles = [f['title'] for f in engine.findings]
        self.assertIn('Missing TLS-RPT Record', titles)


class ZoneTransferTest(TestCase):
    def test_open_zone_transfer_flagged(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if args[1] == '-type=ns':
                return _run_result('example.com\tnameserver = ns1.example.com.')
            if args[1] == '-type=axfr':
                # Simulate a successful transfer dumping many records
                lines = '\n'.join(f'sub{i}.example.com. IN A 1.2.3.{i}' for i in range(20))
                return _run_result(lines)
            return _run_result('')

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_zone_transfer('example.com')

        titles = [f['title'] for f in engine.findings]
        self.assertIn('DNS Zone Transfer (AXFR) Allowed', titles)

    def test_refused_zone_transfer_no_finding(self):
        engine = ScanEngine('https://example.com')

        def side_effect(args, **kwargs):
            if args[1] == '-type=ns':
                return _run_result('example.com\tnameserver = ns1.example.com.')
            if args[1] == '-type=axfr':
                return _run_result('Transfer failed: connection refused')
            return _run_result('')

        with patch('subprocess.run', side_effect=side_effect):
            engine._check_zone_transfer('example.com')

        self.assertEqual(engine.findings, [])

    def test_no_nameservers_found_no_crash(self):
        engine = ScanEngine('https://example.com')
        with patch('subprocess.run', return_value=_run_result('')):
            engine._check_zone_transfer('example.com')
        self.assertEqual(engine.findings, [])
