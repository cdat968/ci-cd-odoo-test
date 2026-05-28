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

echo "Starting OCA Helpdesk smoke test environment..."
set +e
docker compose -f "$COMPOSE_FILE" up \
  --abort-on-container-exit \
  --exit-code-from odoo_helpdesk_smoke \
  odoo_helpdesk_smoke
EXIT_CODE=$?
set -e
END_TS=$(date +%s)

echo "OCA Helpdesk smoke test run took $((END_TS - START_TS))s"
if [ "$EXIT_CODE" -ne 0 ]; then
  echo "OCA Helpdesk smoke tests FAILED (exit $EXIT_CODE)"
  exit "$EXIT_CODE"
fi
echo "OCA Helpdesk smoke tests PASSED"
