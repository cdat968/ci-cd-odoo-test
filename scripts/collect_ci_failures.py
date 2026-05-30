#!/usr/bin/env python3
"""Collect Odoo CI failures from multiple test-step logs.

Each --step value must be formatted as:
    Display Name::log/path::exit-code/path
"""

import argparse
import json
import re
from pathlib import Path

from parse_odoo_test_log import parse


def _slug(value):
    return re.sub(r'[^a-zA-Z0-9_]+', '_', value.strip().lower()).strip('_') or 'unknown'


def _read_exit_code(path):
    try:
        return int(Path(path).read_text().strip())
    except (OSError, ValueError):
        return 1


def _read_log(path):
    try:
        return Path(path).read_text(errors='replace').splitlines()
    except OSError:
        return []


def _tail(lines, limit=160):
    return '\n'.join(lines[-limit:]) if lines else 'CI log file was missing or empty.'


def collect(steps):
    failures = []
    for raw_step in steps:
        try:
            step_name, log_path, exit_path = raw_step.split('::', 2)
        except ValueError:
            raise SystemExit(f'Invalid --step value: {raw_step!r}')

        exit_code = _read_exit_code(exit_path)
        lines = _read_log(log_path)
        parsed = parse(lines)

        for failure in parsed:
            failure.setdefault('module', 'ci')
            failure.setdefault('test', _slug(step_name))
            failure['step'] = step_name
            failures.append(failure)

        if exit_code != 0 and not parsed:
            failures.append({
                'module': 'ci',
                'test': _slug(step_name),
                'step': step_name,
                'traceback': (
                    f'{step_name} failed with exit code {exit_code}.\n\n'
                    f'Last CI log lines:\n{_tail(lines)}'
                ),
            })

    return {
        'failed': len(failures),
        'failures': failures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', action='append', required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.step), indent=2))


if __name__ == '__main__':
    main()
