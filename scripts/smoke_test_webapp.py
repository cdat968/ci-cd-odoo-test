#!/usr/bin/env python3
"""Smoke test: POST report to Odoo → PATCH bug via webapp → verify via Odoo API."""
import os, json, requests, sys

ODOO_URL  = os.environ['ODOO_URL'].rstrip('/')
QA_CI_KEY = os.environ['QA_CI_KEY']
BASE_URL  = os.environ['BASE_URL'].rstrip('/')


def main():
    # Step 1: POST dummy report to Odoo
    payload = {
        'title': 'Smoke Test',
        'html': '',
        'reporter': 'ci',
        'payload': {
            'metadata': {'project_name': 'Smoke', 'report_date': '2026-01-01'},
            'bugs': [{
                'id': 'BUG-001',
                'summary': 'Smoke bug',
                'description': 'Auto smoke test',
                'steps': ['Open app'],
                'expected': 'Works',
                'observed': 'Fails',
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
    print(f'Created report in Odoo: id={report_id}, token={share_token[:8]}…')

    # Step 2: PATCH bug via Next.js (relays to Odoo)
    r2 = requests.patch(
        f'{BASE_URL}/api/reports/{report_id}/bugs/BUG-001?t={share_token}',
        json={'note': 'smoke test note', 'resolution': 'fixed', 'updated_by': 'ci'},
        timeout=30,
    )
    r2.raise_for_status()
    patch = r2.json()
    print(f'PATCH bug response: {patch}')

    # Step 3: Verify via Odoo GET API
    r3 = requests.get(f'{ODOO_URL}/qa/api/report/{share_token}', timeout=30)
    r3.raise_for_status()
    report_data = r3.json()
    bugs = report_data.get('bugs', [])
    bug = next((b for b in bugs if b['id'] == 'BUG-001'), None)
    assert bug is not None, 'BUG-001 not found in report'
    assert bug['note'] == 'smoke test note', f"Expected note 'smoke test note', got '{bug['note']}'"
    assert bug['resolution'] == 'fixed', f"Expected resolution 'fixed', got '{bug['resolution']}'"
    print('GET verify: OK')
    print('Smoke test PASSED')


if __name__ == '__main__':
    main()
