import json
import os
import urllib.request
from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCiReportEndpoint(HttpCase):

    def setUp(self):
        super().setUp()
        self._orig_key = os.environ.get('QA_CI_KEY')
        os.environ['QA_CI_KEY'] = 'test-ci-key-123'

    def tearDown(self):
        super().tearDown()
        if self._orig_key is None:
            os.environ.pop('QA_CI_KEY', None)
        else:
            os.environ['QA_CI_KEY'] = self._orig_key

    def _post_report(self, key='test-ci-key-123', payload=None):
        if payload is None:
            payload = {
                'title': 'Test Report',
                'html': '',
                'payload': {
                    'metadata': {'project_name': 'Test', 'report_date': '2026-01-01'},
                    'bugs': [{
                        'id': 'BUG-001',
                        'summary': 'Test bug',
                        'severity': 's3_minor',
                        'priority': 'p3_medium',
                        'status': 'new',
                    }],
                },
            }
        return self.url_open(
            '/qa/ci/report',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'X-CI-Key': key},
        )

    def test_post_report_valid_key(self):
        resp = self._post_report()
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn('id', data)
        self.assertIn('share_token', data)
        self.assertTrue(len(data['share_token']) > 0)

    def test_post_report_invalid_key(self):
        resp = self._post_report(key='wrong-key')
        self.assertEqual(resp.status_code, 403)

    def test_post_report_missing_title(self):
        resp = self._post_report(payload={'html': '', 'payload': {'bugs': [], 'metadata': {}}})
        self.assertEqual(resp.status_code, 400)

    def test_post_report_creates_bugs(self):
        payload = {
            'title': 'Multi Bug Report',
            'html': '',
            'payload': {
                'metadata': {'project_name': 'Test', 'report_date': '2026-01-01'},
                'bugs': [
                    {'id': 'BUG-001', 'summary': 'Bug one', 'severity': 's1_critical', 'priority': 'p1_urgent', 'status': 'new'},
                    {'id': 'BUG-002', 'summary': 'Bug two', 'severity': 's3_minor', 'priority': 'p4_low', 'status': 'new'},
                ],
            },
        }
        resp = self._post_report(payload=payload)
        self.assertEqual(resp.status_code, 201)
        report_id = resp.json()['id']
        report = self.env['qa.report'].sudo().browse(report_id)
        self.assertEqual(len(report.bug_ids), 2)


@tagged('post_install', '-at_install')
class TestReportApiEndpoint(HttpCase):

    def setUp(self):
        super().setUp()
        self._orig_key = os.environ.get('QA_CI_KEY')
        os.environ['QA_CI_KEY'] = 'test-ci-key-123'
        # Create a test report + bug
        self.report = self.env['qa.report'].sudo().create({
            'name': 'API Test Report',
            'project_name': 'Test Project',
            'report_date': '2026-01-01',
        })
        self.ticket = self.env['qa.bug.ticket'].sudo().create({
            'report_id': self.report.id,
            'title': 'Test bug',
            'component_a_bug_id': 'BUG-001',
            'severity': 's3_minor',
            'priority': 'p3_medium',
            'status': 'new',
        })
        self.token = self.report.share_token

    def tearDown(self):
        super().tearDown()
        if self._orig_key is None:
            os.environ.pop('QA_CI_KEY', None)
        else:
            os.environ['QA_CI_KEY'] = self._orig_key

    def test_get_report_valid_token(self):
        resp = self.url_open(f'/qa/api/report/{self.token}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['id'], self.report.id)
        self.assertIn('bugs', data)
        self.assertEqual(len(data['bugs']), 1)
        self.assertEqual(data['bugs'][0]['id'], 'BUG-001')

    def test_get_report_invalid_token(self):
        resp = self.url_open('/qa/api/report/invalid-token-xyz')
        self.assertEqual(resp.status_code, 404)

    def test_patch_bug_valid(self):
        req = urllib.request.Request(
            self.base_url() + f'/qa/api/report/bug/{self.token}/BUG-001',
            data=json.dumps({'note': 'patched note', 'resolution': 'fixed'}).encode(),
            headers={'Content-Type': 'application/json'},
            method='PATCH',
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
        self.assertEqual(data['note'], 'patched note')
        self.assertEqual(data['resolution'], 'fixed')

    def test_patch_bug_wrong_token(self):
        req = urllib.request.Request(
            self.base_url() + '/qa/api/report/bug/wrong-token/BUG-001',
            data=json.dumps({'note': 'test'}).encode(),
            headers={'Content-Type': 'application/json'},
            method='PATCH',
        )
        try:
            urllib.request.urlopen(req)
            self.fail('Expected HTTP error')
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


@tagged('post_install', '-at_install')
class TestFieldOptionsEndpoint(HttpCase):

    def test_get_field_options_returns_groups(self):
        resp = self.url_open('/qa/api/field-options')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn('severity', data)
        self.assertIn('priority', data)
        self.assertTrue(len(data['severity']) > 0)
