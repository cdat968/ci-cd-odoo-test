#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.test.yml"
START_TS=$(date +%s)

cleanup() {
  local code=$?
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
  exit "$code"
}
trap cleanup EXIT

echo "Starting QA Helpdesk bridge test environment..."
set +e
docker compose -f "$COMPOSE_FILE" up \
  --abort-on-container-exit \
  --exit-code-from odoo_helpdesk_bridge \
  odoo_helpdesk_bridge
EXIT_CODE=$?
set -e
END_TS=$(date +%s)

echo "QA Helpdesk bridge test run took $((END_TS - START_TS))s"
if [ "$EXIT_CODE" -ne 0 ]; then
  echo "QA Helpdesk bridge tests FAILED (exit $EXIT_CODE)"
  exit "$EXIT_CODE"
fi
echo "QA Helpdesk bridge tests PASSED"
