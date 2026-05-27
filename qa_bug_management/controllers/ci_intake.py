import json
import os
from odoo import http
from odoo.http import request


def _ci_auth():
    """Return True if the X-CI-Key header matches QA_CI_KEY env var."""
    ci_key = request.httprequest.headers.get('X-CI-Key', '')
    expected = os.environ.get('QA_CI_KEY', '')
    return expected and ci_key == expected


def _normalize_severity(val: str) -> str:
    mapping = {
        's1': 's1_critical', 'critical': 's1_critical', 's1 - critical': 's1_critical',
        's2': 's2_major',    'major': 's2_major',       's2 - major': 's2_major',
        's3': 's3_minor',    'minor': 's3_minor',       's3 - minor': 's3_minor',
        's4': 's4_trivial',  'trivial': 's4_trivial',   's4 - trivial': 's4_trivial',
        'high': 's2_major', 'medium': 's3_minor', 'low': 's4_trivial',
    }
    return mapping.get((val or '').lower(), 's3_minor')


def _normalize_priority(val: str) -> str:
    mapping = {
        'p1': 'p1_urgent', 'urgent': 'p1_urgent', 'p1 - urgent': 'p1_urgent',
        'p2': 'p2_high',   'high': 'p2_high',     'p2 - high': 'p2_high',
        'p3': 'p3_medium', 'medium': 'p3_medium', 'p3 - medium': 'p3_medium',
        'p4': 'p4_low',    'low': 'p4_low',       'p4 - low': 'p4_low',
    }
    return mapping.get((val or '').lower(), 'p3_medium')


def _normalize_status(val: str) -> str:
    mapping = {
        'new': 'new', 'assigned': 'assigned',
        'in progress': 'in_progress', 'in_progress': 'in_progress',
        'fixed': 'fixed', 'in verification': 'in_verification',
        'in_verification': 'in_verification', 'closed': 'closed',
        're-opened': 'reopened', 'reopened': 'reopened', 'rejected': 'rejected',
    }
    return mapping.get((val or '').lower(), 'new')


class CiIntakeController(http.Controller):

    # ── Legacy single-bug endpoint (backward compat) ───────────────────────
    @http.route('/qa/ci/bug', type='http', auth='public', methods=['POST'], csrf=False)
    def ci_intake(self, **kwargs):
        if not _ci_auth():
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

        existing = BugTicket.search([
            ('ci_commit_sha', '=', commit_sha),
            ('title', '=', title),
            ('status', 'not in', ['fixed', 'closed', 'rejected']),
        ], limit=1)

        if existing:
            ticket = existing
        else:
            evidence_data = data.get('evidence', [])
            ticket = BugTicket.create({
                'title': title,
                'description': data.get('description', ''),
                'severity': _normalize_severity(data.get('severity', '')),
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

    # ── New report intake endpoint (Phase B) ──────────────────────────────
    @http.route('/qa/ci/report', type='http', auth='public', methods=['POST'], csrf=False)
    def ci_report(self, **kwargs):
        if not _ci_auth():
            return request.make_json_response({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.httprequest.data or b'{}')
        except (json.JSONDecodeError, ValueError):
            return request.make_json_response({'error': 'invalid json'}, status=400)

        title = data.get('title', '')
        if not title:
            return request.make_json_response({'error': 'title required'}, status=400)

        payload = data.get('payload', {})
        metadata = payload.get('metadata', {})
        bugs = payload.get('bugs', [])

        # Create qa.report
        Report = request.env['qa.report'].sudo()
        report = Report.create({
            'name': title,
            'project_name': metadata.get('project_name', ''),
            'report_date': metadata.get('report_date', ''),
            'html': data.get('html', ''),
        })

        # Create qa.bug.ticket records linked to this report
        BugTicket = request.env['qa.bug.ticket'].sudo()
        Evidence = request.env['qa.bug.evidence'].sudo()

        for bug in bugs:
            steps_raw = bug.get('steps', [])
            steps_text = '\n'.join(steps_raw) if isinstance(steps_raw, list) else (steps_raw or '')

            ticket = BugTicket.create({
                'report_id': report.id,
                'title': bug.get('summary', bug.get('title', '')),
                'description': bug.get('description', ''),
                'steps': steps_text,
                'expected_result': bug.get('expected', ''),
                'observed_result': bug.get('observed', ''),
                'build_found': bug.get('build', ''),
                'feature_area': bug.get('feature', ''),
                'keyword': bug.get('keyword', ''),
                'severity': _normalize_severity(bug.get('severity', '')),
                'priority': _normalize_priority(bug.get('priority', '')),
                'frequency': bug.get('frequency', '') or None,
                'reproducibility': bug.get('reproducibility', '') or None,
                'status': _normalize_status(bug.get('status', 'new')),
                'note': bug.get('note', ''),
                'suggested_fix': bug.get('suggestedFix', ''),
                'component_a_bug_id': bug.get('id', ''),
                'source': 'ci',
                'ci_run_url': data.get('ci_run_url', ''),
                'ci_commit_sha': data.get('ci_commit_sha', ''),
                'ci_branch': data.get('ci_branch', ''),
                'reporter': data.get('reporter', 'ci-bot'),
            })

            for ev in (bug.get('evidence') or []):
                Evidence.create({
                    'ticket_id': ticket.id,
                    'kind': 'screenshot',
                    'url': ev.get('src', ''),
                    'caption': ev.get('title', ''),
                })

        base_webapp_url = os.environ.get('BASE_WEBAPP_URL', '').rstrip('/')
        share_url = (
            f'{base_webapp_url}/r/{report.id}?t={report.share_token}'
            if base_webapp_url else ''
        )

        return request.make_json_response({
            'id': report.id,
            'share_token': report.share_token,
            'share_url': share_url,
        }, status=201)
