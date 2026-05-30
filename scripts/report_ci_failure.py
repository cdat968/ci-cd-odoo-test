#!/usr/bin/env python3
"""
Report CI failure to Odoo qa.bug.ticket system.
Usage: python scripts/report_ci_failure.py --failures-json failures.json \
         --run-url $CI_RUN_URL --commit $COMMIT_SHA --branch $BRANCH
"""
import argparse, html, json, os
import requests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--failures-json', required=True)
    parser.add_argument('--run-url', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--branch', required=True)
    parser.add_argument('--report-url', default='')
    parser.add_argument('--github-actor', default='')
    parser.add_argument('--github-pr-author', default='')
    parser.add_argument('--github-pr-url', default='')
    parser.add_argument('--created-output', default='')
    args = parser.parse_args()

    odoo_url = os.environ['ODOO_URL'].rstrip('/')
    ci_key = os.environ['QA_CI_KEY']

    with open(args.failures_json) as f:
        data = json.load(f)

    created = []
    for failure in data.get('failures', []):
        metadata = [
            f"CI step: {failure.get('step', '')}",
            f"Branch: {args.branch}",
            f"Commit: {args.commit}",
            f"Run: {args.run_url}",
        ]
        if args.github_pr_url:
            metadata.append(f"PR: {args.github_pr_url}")
        if args.github_pr_author:
            metadata.append(f"PR author: {args.github_pr_author}")
        if args.github_actor:
            metadata.append(f"GitHub actor: {args.github_actor}")

        payload = {
            'title': f"[CI] {failure['module']}.{failure['test']} failed",
            'description': '\n'.join(metadata),
            'ci_error_log': f"<pre>{html.escape(failure.get('traceback', ''))}</pre>",
            'severity': 'high',
            'ci_run_url': args.run_url,
            'ci_commit_sha': args.commit,
            'ci_branch': args.branch,
            'github_actor': args.github_actor,
            'github_pr_author': args.github_pr_author,
            'github_pr_url': args.github_pr_url,
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
        line = f"Created: {result.get('name')} (id={result.get('id')})"
        created.append(line)
        print(line)

    if args.created_output:
        with open(args.created_output, 'w') as f:
            f.write('\n'.join(created))
            if created:
                f.write('\n')

if __name__ == '__main__':
    main()
