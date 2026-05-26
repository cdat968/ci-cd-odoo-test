#!/usr/bin/env python3
"""Smoke test: POST report → GET /r/{id} → PATCH bug → GET patches → assert."""
import os, json, secrets, requests, sys

BASE_URL = os.environ['BASE_URL'].rstrip('/')
PIPELINE_KEY = os.environ['PIPELINE_KEY']

def main():
    # POST dummy report
    html = '<html><body><tr class="ticket-row" data-id="BUG-001"><td>Test</td></tr></body></html>'
    payload = {'bugs': [{'id': 'BUG-001', 'title': 'Smoke bug'}], 'test_cases': [], 'evidence_map': {}}
    r = requests.post(f'{BASE_URL}/api/reports',
                      json={'title': 'Smoke Test', 'html': html, 'payload': payload, 'created_by': 'ci'},
                      headers={'X-Pipeline-Key': PIPELINE_KEY}, timeout=30)
    r.raise_for_status()
    data = r.json()
    report_id = data['id']
    share_url = data['share_url']
    token = share_url.split('?t=')[1]
    print(f'Created report: {report_id}')

    # PATCH bug
    r2 = requests.patch(
        f'{BASE_URL}/api/reports/{report_id}/bugs/BUG-001?t={token}',
        json={'note': 'smoke test note', 'resolution': 'Fixed', 'updated_by': 'ci'},
        timeout=30)
    r2.raise_for_status()
    patch = r2.json()
    assert patch['status'] == 'Closed', f"Expected Closed, got {patch['status']}"
    print('PATCH bug: OK')

    # GET patches
    r3 = requests.get(f'{BASE_URL}/api/reports/{report_id}/patches?t={token}', timeout=30)
    r3.raise_for_status()
    patches = r3.json()['patches']
    assert len(patches) == 1 and patches[0]['resolution'] == 'Fixed'
    print('GET patches: OK')
    print('Smoke test PASSED')

if __name__ == '__main__':
    main()
