# Pipeline Publish

Two-step extension that connects the Python HTML-report pipeline to the Next.js webapp:

1. **Step 1** — upload evidence images to Cloudinary  
2. **Step 2** — POST the rendered HTML + artifacts payload to `/api/reports`

---

## Install dependencies

```bash
pip install -r pipeline/requirements.txt
```

---

## Set environment variables

Copy `.env.example` and fill in real values:

```bash
cp pipeline/.env.example .env
# then edit .env:
#   BACKEND_URL   = https://your-app.vercel.app
#   PIPELINE_KEY  = <secret key from webapp env>
#   CLOUDINARY_URL= cloudinary://api_key:api_secret@cloud_name
```

Load the env file before running (or export vars directly):

```bash
export $(grep -v '^#' .env | xargs)
```

---

## Run publish after generating a report

After `testing_report_runner.py` writes `output/report.html`:

```bash
python pipeline/publish.py \
  --report-json output/artifacts.json \
  --html        output/report.html \
  --title       "Attendance Report Q2" \
  --created-by  "dat@company.com"
```

The command prints the `share_url` on success, e.g.:

```
https://your-app.vercel.app/r/abc123?t=<token>
```

---

## Flags

| Flag | Description |
|---|---|
| `--dry-run` | Print what would happen without calling any external API |
| `--no-publish` | Upload images to Cloudinary but skip the POST to `/api/reports` |
| `--log-level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` (default: `INFO`) |

### Dry-run example

```bash
python pipeline/publish.py \
  --report-json output/artifacts.json \
  --html        output/report.html \
  --title       "Test Run" \
  --dry-run
```

Output:

```
[dry-run] Would upload evidence:
  EVD-001: screenshots/step1.png
  EVD-002: screenshots/step2.png
[dry-run] Would POST to https://your-app.vercel.app/api/reports
[dry-run]   title       = 'Test Run'
[dry-run]   created_by  = None
[dry-run]   html length = 42341 chars
```

### Skip API, images only

```bash
python pipeline/publish.py \
  --report-json output/artifacts.json \
  --html        output/report.html \
  --title       "Test Run" \
  --no-publish
```

---

## Integration snippet for `testing_report_runner.py`

Do **not** modify `testing_report_runner.py` directly. Instead, call `publish.py`
from a wrapper script after the runner completes:

```python
# run_and_publish.py
import subprocess, sys

# 1. Generate the HTML report (unchanged pipeline)
result = subprocess.run([
    sys.executable,
    "automation/testing_report_runner.py",
    "--artifacts", "data/artifacts.json",
    "--output",    "output/report.html",
    "--operation", "create_new_report",
    "--report-key", "mode2_vi",
], check=True)

# 2. Publish to webapp
from pipeline.publish import run_pipeline

share_url = run_pipeline(
    report_json_path="data/artifacts.json",
    html_path="output/report.html",
    title="Attendance Report Q2",
    created_by="dat@company.com",
)
print("Published:", share_url)
```

Or import directly:

```python
from pipeline.publish import run_pipeline

share_url = run_pipeline(
    report_json_path="data/artifacts.json",
    html_path="output/report.html",
    title="Attendance Report Q2",
    created_by="dat@company.com",
    dry_run=False,
    no_publish=False,
)
```

---

## Cloudinary folder structure

Images are stored at:

```
qa-reports/<report_id>/<asset_id>
```

For example:

```
qa-reports/550e8400-e29b-41d4-a716-446655440000/EVD-001
```

---

## Error handling

- If a single image upload fails, a `WARNING` is logged and the pipeline continues with the original `local_path` value.
- Network errors on the API call are retried once before raising.
- If `BACKEND_URL` or `PIPELINE_KEY` are missing, an `EnvironmentError` is raised immediately.
- A 404 from the API indicates a wrong `PIPELINE_KEY` or missing endpoint.
