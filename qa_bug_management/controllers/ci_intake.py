import json
import os
from odoo import http
from odoo.http import request


class CiIntakeController(http.Controller):

    @http.route('/qa/ci/bug', type='http', auth='public', methods=['POST'], csrf=False)
    def ci_intake(self, **kwargs):
        # Key-based authentication
        ci_key = request.httprequest.headers.get('X-CI-Key', '')
        expected = os.environ.get('QA_CI_KEY', '')
        if not expected or ci_key != expected:
            return request.make_json_response({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.httprequest.data or b'{}')
        except (json.JSONDecodeError, ValueError):
            return request.make_json_response({'error': 'invalid json'}, status=400)

        title = data.get('title', '')
        if not title:
            return request.make_json_response({'error': 'title required'}, status=400)

        commit_sha = data.get('ci_commit_sha', '')
        BugTicket = request.env['qa.bug.ticket'].sudo()

        # Dedup: same commit + title and not resolved
        existing = BugTicket.search([
            ('ci_commit_sha', '=', commit_sha),
            ('title', '=', title),
            ('status', 'not in', ['fixed', 'wont_fix', 'duplicate']),
        ], limit=1)

        if existing:
            existing.description = (existing.description or '') + (
                f'<p><b>Re-run:</b> {data.get("ci_run_url", "")}</p>'
                f'<pre>{data.get("description", "")}</pre>'
            )
            ticket = existing
        else:
            evidence_data = data.get('evidence', [])
            ticket = BugTicket.create({
                'title': title,
                'description': data.get('description', ''),
                'severity': data.get('severity', 'medium'),
                'source': 'ci',
                'ci_run_url': data.get('ci_run_url', ''),
                'ci_commit_sha': commit_sha,
                'ci_branch': data.get('ci_branch', ''),
                'report_share_url': data.get('report_share_url', ''),
                'component_a_bug_id': data.get('component_a_bug_id', ''),
                'reporter': data.get('reporter', 'ci-bot'),
                'evidence_ids': [(0, 0, {
                    'kind': e.get('kind', 'link'),
                    'url': e.get('url', ''),
                    'caption': e.get('caption', ''),
                }) for e in evidence_data],
            })

        return request.make_json_response({'id': ticket.id, 'name': ticket.name})
