#!/usr/bin/env bash
set -euo pipefail

echo "Starting Odoo test environment..."
docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from odoo
EXIT_CODE=$?

docker compose -f docker-compose.test.yml down -v --remove-orphans

if [ $EXIT_CODE -ne 0 ]; then
  echo "Odoo tests FAILED (exit $EXIT_CODE)"
  exit $EXIT_CODE
fi
echo "Odoo tests PASSED"
