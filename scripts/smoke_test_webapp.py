#!/usr/bin/env python3
"""Smoke test: POST report to Odoo → PATCH bug via webapp → verify via Odoo API.
Test records are always deleted after the run (pass or fail).
"""
import os, json, requests, sys

ODOO_URL  = os.environ['ODOO_URL'].strip().rstrip('/')
QA_CI_KEY = os.environ['QA_CI_KEY']
BASE_URL  = os.environ['BASE_URL'].strip().rstrip('/')


def main():
    report_id = None
    try:
        # Step 1: POST dummy report to Odoo
        payload = {
            'title': 'Smoke Test',
            'html': '',
            'reporter': 'ci',
            'payload': {
                'metadata': {'project_name': 'Smoke', 'report_date': '2026-01-01'},
                'bugs': [{
                    'id': 'BUG-SMOKE-001',
                    'summary': 'Smoke bug',
                    'severity': 's3_minor',
                    'priority': 'p3_medium',
                    'status': 'new',
                }],
            },
        }
        r = requests.post(
            f'{ODOO_URL}/qa/ci/report',
            json=payload,
            headers={'X-CI-Key': QA_CI_KEY, 'Content-Type': 'application/json'},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        report_id   = data['id']
        share_token = data['share_token']
        print(f'Created report: id={report_id}, token={share_token[:8]}…')

        # Step 2: PATCH bug via Next.js relay (tests HTTP connectivity NextJS → Odoo)
        r2 = requests.patch(
            f'{BASE_URL}/api/reports/{report_id}/bugs/BUG-SMOKE-001?t={share_token}',
            json={'note': 'smoke test note', 'resolution': 'fixed', 'updated_by': 'ci'},
            timeout=30,
        )
        r2.raise_for_status()
        print(f'PATCH via NextJS relay: OK')

        # Step 3: Verify data was saved correctly via Odoo GET
        r3 = requests.get(f'{ODOO_URL}/qa/api/report/{share_token}', timeout=30)
        r3.raise_for_status()
        bugs = r3.json().get('bugs', [])
        bug  = next((b for b in bugs if b['id'] == 'BUG-SMOKE-001'), None)
        assert bug is not None, 'BUG-SMOKE-001 not found in report'
        assert bug['note'] == 'smoke test note', f"note mismatch: {bug['note']}"
        assert bug['resolution'] == 'fixed', f"resolution mismatch: {bug['resolution']}"
        print('Smoke test PASSED')

    finally:
        # Always clean up — test data must not remain in production DB
        if report_id is not None:
            try:
                rd = requests.delete(
                    f'{ODOO_URL}/qa/api/report/{report_id}',
                    headers={'X-CI-Key': QA_CI_KEY},
                    timeout=30,
                )
                if rd.status_code == 200:
                    print(f'Cleanup: report {report_id} deleted')
                else:
                    print(f'Cleanup warning: DELETE returned {rd.status_code}', file=sys.stderr)
            except Exception as e:
                print(f'Cleanup error: {e}', file=sys.stderr)


if __name__ == '__main__':
    main()
