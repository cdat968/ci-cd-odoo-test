# Deployment & CI/CD Setup

## GitHub Secrets cần cấu hình

| Secret | Mô tả |
|---|---|
| `ODOO_URL` | URL Odoo instance (vd: https://odoo.company.com) |
| `QA_CI_KEY` | Khớp với env var `QA_CI_KEY` trên Odoo server |
| `COMPONENT_A_PIPELINE_KEY` | Khớp với `PIPELINE_KEY` trên Vercel |

## GitHub Variables (không phải secret)

| Variable | Mô tả |
|---|---|
| `COMPONENT_A_BASE_URL` | URL webapp Vercel (vd: https://qa-report.vercel.app) |

## Local test

```bash
bash scripts/run_odoo_tests.sh
```

## CI/CD Pipeline Overview

### Workflow: `ci.yml`

Runs on every push and pull request to `main` and `18.0` branches.

#### Job 1: `test-odoo`
- Starts Odoo 18 + PostgreSQL via Docker Compose
- Runs module tests with `--test-enable --stop-after-init`
- Parses test output for failures
- Auto-creates bug tickets in Odoo via `/qa/ci/bug` endpoint
- Fails the workflow if any tests fail

#### Job 2: `test-webapp`
- Conditional: only runs if `COMPONENT_A_BASE_URL` is configured
- Health check: `GET /api/health`
- Smoke test: POST report → fetch share link → PATCH bug → verify persistence

#### Job 3: `lint-check`
- Type-checks Next.js webapp with TypeScript compiler

### Docker Compose: `docker-compose.test.yml`

- **Service `db`**: PostgreSQL 15 with `ci_test` database
- **Service `odoo`**: Odoo 18 container
  - Mounts `addons/qa_bug_management` read-only
  - Runs in test mode and exits after initialization
  - Logs to stderr for log parsing

### Test Result Parsing

Script: `scripts/parse_odoo_test_log.py`

Extracts failures using regex:
- `FAIL: testName (module.path)`
- `ERROR: testName (module.path)`
- Captures last 20 lines of traceback per failure
- Outputs JSON: `{ "failed": N, "failures": [...] }`

### Failure Reporting

Script: `scripts/report_ci_failure.py`

- Reads parsed failures JSON
- POSTs each to Odoo `/qa/ci/bug` endpoint
- Includes:
  - CI run URL (GitHub Actions)
  - Commit SHA
  - Branch name
  - Stack trace
- Server deduplicates on `(commit_sha, title)` pair

### Webapp Smoke Test

Script: `scripts/smoke_test_webapp.py`

Full round-trip test:
1. POST `/api/reports` with dummy QA data → get `report_id` and share `token`
2. PATCH `/api/reports/{report_id}/bugs/BUG-001?t={token}` → mark bug as Fixed
3. GET `/api/reports/{report_id}/patches?t={token}` → verify patch persisted
4. Assert status == 'Closed'

## Setting up GitHub Secrets

### In GitHub UI

1. Go to: Settings → Secrets and variables → Actions
2. Create **Secrets**:
   - `ODOO_URL`: e.g., `https://odoo.company.com`
   - `QA_CI_KEY`: Copy from your Odoo server env
   - `COMPONENT_A_PIPELINE_KEY`: Copy from Vercel env
3. Create **Variables**:
   - `COMPONENT_A_BASE_URL`: e.g., `https://qa-report.vercel.app`

### Via GitHub CLI

```bash
gh secret set ODOO_URL --body "https://odoo.company.com"
gh secret set QA_CI_KEY --body "<ci-key-value>"
gh secret set COMPONENT_A_PIPELINE_KEY --body "<pipeline-key-value>"
gh variable set COMPONENT_A_BASE_URL --body "https://qa-report.vercel.app"
```

## Disabling Webapp Test (for now)

If the Next.js webapp is not yet deployed:
- Leave `COMPONENT_A_BASE_URL` variable **empty** or **unset**
- The `test-webapp` and `lint-check` jobs will skip automatically

## Troubleshooting

### Docker Compose fails on macOS

If using M1/M2 Mac and image not available for `arm64`:
```yaml
  odoo:
    image: odoo:18.0
    platform: linux/amd64  # Force AMD64 emulation
```

### Test timeout in CI

Increase timeout in `docker-compose.test.yml`:
```yaml
    healthcheck:
      timeout: 10s       # was 5s
      retries: 15        # was 10
```

### Secrets not found at runtime

Ensure secrets are defined at the repository level (not environment level).
Check: Settings → Secrets and variables → Actions → Secrets.

## Manual test commands

### Run Odoo tests locally

```bash
bash scripts/run_odoo_tests.sh
```

### Parse log manually

```bash
docker compose logs odoo 2>&1 | python scripts/parse_odoo_test_log.py
```

### Test Odoo failure reporting (requires ODOO_URL, QA_CI_KEY env vars)

```bash
export ODOO_URL="https://odoo.company.com"
export QA_CI_KEY="your-key"

# Create dummy failures.json
python -c '
import json
data = {
    "failed": 1,
    "failures": [{
        "test": "test_create",
        "module": "qa_bug_management.tests.test_qa_bug_ticket",
        "traceback": "AssertionError: bug not created"
    }]
}
with open("failures.json", "w") as f:
    json.dump(data, f)
'

python scripts/report_ci_failure.py \
  --failures-json failures.json \
  --run-url "https://github.com/org/repo/actions/runs/123" \
  --commit "abc123def456" \
  --branch "feature/test"
```

### Test webapp smoke test (requires COMPONENT_A_BASE_URL, PIPELINE_KEY env vars)

```bash
export BASE_URL="https://qa-report.vercel.app"
export PIPELINE_KEY="your-pipeline-key"

python scripts/smoke_test_webapp.py
```
