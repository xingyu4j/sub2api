import contextlib
from datetime import date, timedelta
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('audit_exceptions', ROOT / 'tools/check_pnpm_audit_exceptions.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class AuditExceptionsTest(unittest.TestCase):
    def check_report(self, report, exceptions='version: 1\nexceptions:\n'):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / 'audit.json'
            exception_path = Path(directory) / 'exceptions.yml'
            audit_path.write_text(json.dumps(report), encoding='utf-8')
            exception_path.write_text(exceptions, encoding='utf-8')
            arguments = ['check', '--audit', str(audit_path), '--exceptions', str(exception_path)]
            with patch.object(sys, 'argv', arguments), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return checker.main()

    def test_a_successful_report_without_vulnerabilities_passes(self):
        for report in ({'advisories': {}}, {'vulnerabilities': {}}):
            with self.subTest(report=report):
                self.assertEqual(self.check_report(report), 0)

    def test_network_errors_and_unknown_output_cannot_pass(self):
        for report in ({'error': {'code': 'ECONNRESET'}}, {}, None, [],
                       {'error': 'registry unavailable', 'advisories': {}}):
            with self.subTest(report=report):
                self.assertEqual(self.check_report(report), 1)

    def test_high_severity_findings_still_require_an_unexpired_exception(self):
        report = {'advisories': {'1': {
            'module_name': 'xlsx', 'severity': 'high',
            'github_advisory_id': 'GHSA-4r6h-8v6p-xvw6',
        }}}
        self.assertEqual(self.check_report(report), 1)
        for expired in (False, True):
            expires_on = date.today() + timedelta(days=-1 if expired else 1)
            exceptions = f'''version: 1
exceptions:
  - package: xlsx
    advisory: GHSA-4r6h-8v6p-xvw6
    severity: high
    mitigation: Export only; never parse untrusted spreadsheets
    expires_on: {expires_on.isoformat()}
'''
            with self.subTest(expired=expired):
                self.assertEqual(self.check_report(report, exceptions), 1 if expired else 0)


if __name__ == '__main__':
    unittest.main()
