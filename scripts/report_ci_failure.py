#!/usr/bin/env python3
"""
Report CI failure to Odoo qa.bug.ticket system.
Usage: python scripts/report_ci_failure.py --failures-json failures.json \
         --run-url $CI_RUN_URL --commit $COMMIT_SHA --branch $BRANCH
"""
import argparse, json, os, sys
import requests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--failures-json', required=True)
    parser.add_argument('--run-url', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--branch', required=True)
    parser.add_argument('--report-url', default='')
    args = parser.parse_args()

    odoo_url = os.environ['ODOO_URL'].rstrip('/')
    ci_key = os.environ['QA_CI_KEY']

    with open(args.failures_json) as f:
        data = json.load(f)

    for failure in data.get('failures', []):
        payload = {
            'title': f"[CI] {failure['module']}.{failure['test']} failed",
            'description': '',
            'ci_error_log': f"<pre>{failure.get('traceback', '')}</pre>",
            'severity': 'high',
            'ci_run_url': args.run_url,
            'ci_commit_sha': args.commit,
            'ci_branch': args.branch,
            'report_share_url': args.report_url,
            'evidence': [],
        }
        resp = requests.post(
            f'{odoo_url}/qa/ci/bug',
            json=payload,
            headers={
                'X-CI-Key': ci_key,
                'Content-Type': 'application/json',
            },
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"Created: {result.get('name')} (id={result.get('id')})")

if __name__ == '__main__':
    main()
