from unittest.mock import patch
from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCiIntake(HttpCase):

    def test_rejects_missing_key(self):
        resp = self.url_open('/qa/ci/bug', data=b'{}',
                             headers={'Content-Type': 'application/json'})
        self.assertEqual(resp.status_code, 403)

    def test_creates_ticket(self):
        import os
        import json
        with patch.dict(os.environ, {'QA_CI_KEY': 'test-key'}):
            payload = json.dumps({
                'title': 'Button missing', 'severity': 'high',
                'ci_commit_sha': 'abc123', 'ci_branch': 'main',
                'ci_run_url': 'https://github.com/actions/runs/1',
                'evidence': [],
            }).encode()
            resp = self.url_open('/qa/ci/bug', data=payload,
                                 headers={'Content-Type': 'application/json',
                                          'X-CI-Key': 'test-key'})
            self.assertEqual(resp.status_code, 200)
            result = resp.json()
            self.assertIn('QA-BUG/', result.get('name', ''))

    def test_assigns_ticket_from_github_login(self):
        import os
        import json
        user = self.env['res.users'].sudo().create({
            'name': 'CI Dev',
            'login': 'ci-dev@example.com',
            'github_login': 'ci-dev',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('qa_bug_management.group_qa_user').id,
            ])],
        })
        with patch.dict(os.environ, {'QA_CI_KEY': 'test-key'}):
            payload = json.dumps({
                'title': 'Mapped GitHub user failure',
                'ci_commit_sha': 'mapped123',
                'ci_branch': 'feature/mapped',
                'github_actor': 'fallback-user',
                'github_pr_author': 'ci-dev',
                'github_pr_url': 'https://github.com/acme/repo/pull/12',
                'evidence': [],
            }).encode()
            resp = self.url_open('/qa/ci/bug', data=payload,
                                 headers={'Content-Type': 'application/json',
                                          'X-CI-Key': 'test-key'})
            self.assertEqual(resp.status_code, 200)
            ticket = self.env['qa.bug.ticket'].sudo().browse(resp.json()['id'])
            self.assertEqual(ticket.assignee_id, user)
            self.assertEqual(ticket.ci_github_actor, 'fallback-user')
            self.assertEqual(ticket.ci_pr_author, 'ci-dev')
            self.assertEqual(ticket.ci_pr_url, 'https://github.com/acme/repo/pull/12')

    def test_dedup_same_commit_title(self):
        import os
        import json
        with patch.dict(os.environ, {'QA_CI_KEY': 'test-key'}):
            payload = lambda: json.dumps({
                'title': 'Dupe bug', 'ci_commit_sha': 'sha999',
                'ci_branch': 'main', 'evidence': [],
            }).encode()
            headers = {'Content-Type': 'application/json', 'X-CI-Key': 'test-key'}
            r1 = self.url_open('/qa/ci/bug', data=payload(), headers=headers).json()
            r2 = self.url_open('/qa/ci/bug', data=payload(), headers=headers).json()
            self.assertEqual(r1['id'], r2['id'])

    def test_rejects_missing_title(self):
        import os
        import json
        with patch.dict(os.environ, {'QA_CI_KEY': 'test-key'}):
            payload = json.dumps({
                'ci_commit_sha': 'abc999', 'evidence': []
            }).encode()
            resp = self.url_open('/qa/ci/bug', data=payload,
                                 headers={'Content-Type': 'application/json',
                                          'X-CI-Key': 'test-key'})
            self.assertEqual(resp.status_code, 400)

    def test_creates_evidence_rows(self):
        import os
        import json
        with patch.dict(os.environ, {'QA_CI_KEY': 'test-key'}):
            payload = json.dumps({
                'title': 'Evidence test', 'ci_commit_sha': 'evsha001',
                'ci_branch': 'feature/test', 'evidence': [
                    {'kind': 'screenshot', 'url': 'https://cdn.example.com/shot.png',
                     'caption': 'Failed step screenshot'},
                    {'kind': 'log', 'url': 'https://cdn.example.com/test.log',
                     'caption': 'Test output'},
                ],
            }).encode()
            resp = self.url_open('/qa/ci/bug', data=payload,
                                 headers={'Content-Type': 'application/json',
                                          'X-CI-Key': 'test-key'})
            self.assertEqual(resp.status_code, 200)
            result = resp.json()
            ticket_id = result.get('id')
            self.assertTrue(ticket_id)
            ticket = self.env['qa.bug.ticket'].sudo().browse(ticket_id)
            self.assertEqual(len(ticket.evidence_ids), 2)
