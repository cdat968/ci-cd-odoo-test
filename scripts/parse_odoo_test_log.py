#!/usr/bin/env python3
"""
Parse Odoo test log output and print structured failure summary.
Usage: docker compose logs odoo 2>&1 | python scripts/parse_odoo_test_log.py
"""
import sys, re, json

# Odoo 18 logs via Python logger — line format:
#   odoo-1 | 2026-... ERROR db odoo.tests.result: FAIL: test_xxx (module.Class)
# Also handle Python 3.11+ format where method name is appended:
#   FAIL: test_xxx (module.Class.test_xxx)
# And plain unittest format (no logger prefix)
FAIL_RE = re.compile(r'FAIL: (test\w+) \(([^)]+)\)')
ERROR_RE = re.compile(r'ERROR: (test\w+) \(([^)]+)\)')
# Odoo 18 summary line: "X failed, Y error(s)"
SUMMARY_RE = re.compile(r'(\d+) failed,?\s*(\d+)? ?error')
TRACEBACK_RE = re.compile(r'Traceback \(most recent call last\):')

def parse(lines):
    failures = []
    current_tb = []
    in_tb = False
    for line in lines:
        if TRACEBACK_RE.search(line):
            in_tb = True
            current_tb = [line.rstrip()]
        elif in_tb:
            current_tb.append(line.rstrip())
            if line.strip() and not line.startswith(' '):
                in_tb = False
        m = FAIL_RE.search(line) or ERROR_RE.search(line)
        if m:
            failures.append({
                'test': m.group(1),
                'module': m.group(2),
                'traceback': '\n'.join(current_tb[-20:]),
            })
            current_tb = []
    return failures

if __name__ == '__main__':
    lines = sys.stdin.readlines()
    results = parse(lines)
    print(json.dumps({'failed': len(results), 'failures': results}, indent=2))
    sys.exit(1 if results else 0)
