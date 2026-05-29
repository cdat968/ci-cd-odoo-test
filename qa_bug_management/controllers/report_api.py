import json
import os
from odoo import http
from odoo.http import request


def _ci_auth():
    ci_key = request.httprequest.headers.get('X-CI-Key', '')
    expected = os.environ.get('QA_CI_KEY', '')
    return expected and ci_key == expected


def _serialize_bug(ticket):
    steps_raw = ticket.steps or ''
    steps = [s.strip() for s in steps_raw.split('\n') if s.strip()]
    evidence = []
    for item in ticket.evidence_ids:
        src = item.get_image_url()
        evidence.append({'src': src or '', 'title': item.caption or ''})
    return {
        'id': ticket.component_a_bug_id or str(ticket.id),
        'summary': ticket.title or '',
        'description': ticket.description or '',
        'steps': steps,
        'expected': ticket.expected_result or '',
        'observed': ticket.observed_result or '',
        'build': ticket.build_found or '',
        'reproducibility': ticket.reproducibility or '',
        'severity': ticket.severity or '',
        'frequency': ticket.frequency or '',
        'priority': ticket.priority or '',
        'keyword': ticket.keyword or '',
        'status': ticket.status or '',
        'resolution': ticket.resolution or '',
        'note': ticket.note or '',
        'suggestedFix': ticket.suggested_fix or '',
        'feature': ticket.feature_area or '',
        'createdAt': ticket.create_date.isoformat() if ticket.create_date else '',
        'evidence': evidence,
    }


class ReportApiController(http.Controller):

    @http.route('/qa/api/report/<string:share_token>', type='http', auth='public',
                methods=['GET'], csrf=False)
    def get_report(self, share_token, **kwargs):
        Report = request.env['qa.report'].sudo()
        report = Report.search([('share_token', '=', share_token)], limit=1)
        if not report:
            return request.make_json_response({'error': 'not found'}, status=404)

        bugs = [_serialize_bug(t) for t in report.bug_ids]
        result = {
            'id': report.id,
            'title': report.name,
            'project_name': report.project_name or '',
            'report_date': report.report_date or '',
            'total_bugs': report.bug_count,
            'open_bugs': sum(1 for b in bugs if b['status'] not in ('closed', 'rejected', 'fixed')),
            'high_priority_count': sum(1 for b in bugs if b['priority'] in ('p1_urgent', 'p2_high')),
            'bugs': bugs,
        }
        return request.make_json_response(result)

    @http.route('/qa/api/report/bug/<string:share_token>/<string:bug_id>', type='http',
                auth='public', methods=['PATCH'], csrf=False)
    def patch_bug(self, share_token, bug_id, **kwargs):
        Report = request.env['qa.report'].sudo()
        report = Report.search([('share_token', '=', share_token)], limit=1)
        if not report:
            return request.make_json_response({'error': 'not found'}, status=404)

        # Find ticket by component_a_bug_id within this report
        ticket = report.bug_ids.filtered(
            lambda t: (t.component_a_bug_id or str(t.id)) == bug_id
        )
        if not ticket:
            return request.make_json_response({'error': 'bug not found'}, status=404)

        try:
            body = json.loads(request.httprequest.data or b'{}')
        except (json.JSONDecodeError, ValueError):
            return request.make_json_response({'error': 'invalid json'}, status=400)

        vals = {}
        if 'note' in body and body['note'] is not None:
            vals['note'] = body['note']
        if 'resolution' in body and body['resolution'] is not None:
            vals['resolution'] = body['resolution']
        if 'status' in body and body['status'] is not None:
            vals['status'] = body['status']

        if vals:
            ticket.write(vals)

        return request.make_json_response({
            'id': bug_id,
            'note': ticket.note or '',
            'resolution': ticket.resolution or '',
            'status': ticket.status or '',
        })

    @http.route('/qa/api/report/<int:report_id>', type='http', auth='public',
                methods=['DELETE'], csrf=False)
    def delete_report(self, report_id, **kwargs):
        if not _ci_auth():
            return request.make_json_response({'error': 'Forbidden'}, status=403)
        report = request.env['qa.report'].sudo().browse(report_id)
        if not report.exists():
            return request.make_json_response({'error': 'not found'}, status=404)
        report.unlink()
        return request.make_json_response({'status': 'deleted'})

    @http.route('/qa/api/field-options', type='http', auth='public',
                methods=['GET'], csrf=False)
    def get_field_options(self, **kwargs):
        options = request.env['qa.field.option'].sudo().search([], order='field_name, sequence')
        result = {}
        for opt in options:
            result.setdefault(opt.field_name, []).append({
                'value': opt.value,
                'label': opt.label,
                'description': opt.description or '',
            })
        return request.make_json_response(result)
