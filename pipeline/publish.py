"""
publish.py — two-step pipeline extension:
  step 1: upload evidence images to Cloudinary
  step 2: POST rendered HTML + payload to Next.js webapp API
Returns share_url.

Usage (CLI):
    python pipeline/publish.py \\
        --report-json path/to/artifacts.json \\
        --html path/to/report.html \\
        --title "Attendance Report Q2" \\
        --created-by "dat@company.com" \\
        [--no-publish]   # skip API call, just upload images
        [--dry-run]      # skip both steps, just print what would happen

Environment variables required:
    BACKEND_URL    — Base URL of the Next.js webapp (e.g. https://your-app.vercel.app)
    PIPELINE_KEY   — Secret key sent as X-Pipeline-Key header
    CLOUDINARY_URL — Cloudinary connection string (SDK auto-parses it)
                     Format: cloudinary://api_key:api_secret@cloud_name
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_TIMEOUT_SECONDS = 30
_MAX_RETRIES = 1


def _get_requests():
    """Lazily import requests to give a friendly error if not installed."""
    try:
        import requests  # type: ignore
        return requests
    except ImportError as exc:
        raise ImportError(
            "requests package is not installed. "
            "Run: pip install requests>=2.31.0"
        ) from exc


# ---------------------------------------------------------------------------
# Step 1 — upload evidence images to Cloudinary
# ---------------------------------------------------------------------------

def upload_evidence(evidence_map: dict[str, Any], report_id: str) -> dict[str, Any]:
    """Upload all evidence images to Cloudinary and return updated evidence_map.

    Args:
        evidence_map: Dict mapping asset_id -> { local_path, ...other fields }
        report_id:    Report identifier used as Cloudinary folder name.

    Returns:
        Updated evidence_map with ``secure_url`` and ``public_id`` added to
        each entry that was successfully uploaded.  Entries whose upload fails
        are left with their original ``local_path`` so callers can fall back
        gracefully.
    """
    from pipeline.cloudinary_uploader import upload_evidence_map  # type: ignore

    logger.info("Step 1 — uploading %d evidence image(s) to Cloudinary (report_id=%s) …", len(evidence_map), report_id)
    updated = upload_evidence_map(evidence_map, report_id)
    uploaded_count = sum(1 for v in updated.values() if v.get("secure_url"))
    logger.info("Step 1 — uploaded %d / %d image(s).", uploaded_count, len(evidence_map))
    return updated


# ---------------------------------------------------------------------------
# Step 2 — POST report to Next.js webapp API
# ---------------------------------------------------------------------------

def publish_report(
    title: str,
    html: str,
    payload: Any,
    created_by: str | None = None,
) -> str:
    """POST the rendered HTML report to the Next.js webapp API.

    Args:
        title:      Human-readable title shown in the webapp.
        html:       Full rendered HTML string produced by the pipeline.
        payload:    Arbitrary JSON-serialisable data (artifacts, metadata, …).
        created_by: Optional email / identifier of the report author.

    Returns:
        share_url string from the API response.

    Raises:
        EnvironmentError: If BACKEND_URL or PIPELINE_KEY are not set.
        RuntimeError:     If the API returns a non-2xx status code after retries.
        requests.RequestException: On network-level errors after retries.
    """
    requests = _get_requests()

    backend_url = os.environ.get("BACKEND_URL", "").rstrip("/")
    pipeline_key = os.environ.get("PIPELINE_KEY", "")

    if not backend_url:
        raise EnvironmentError(
            "BACKEND_URL environment variable is not set. "
            "Set it to the base URL of the Next.js webapp."
        )
    if not pipeline_key:
        raise EnvironmentError(
            "PIPELINE_KEY environment variable is not set. "
            "Set it to the shared secret expected by the /api/reports endpoint."
        )

    endpoint = f"{backend_url}/api/reports"
    headers = {
        "Content-Type": "application/json",
        "X-Pipeline-Key": pipeline_key,
    }
    body = {
        "title": title,
        "html": html,
        "payload": payload,
        "created_by": created_by,
    }

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 2):  # attempts: 1, 2
        try:
            logger.info(
                "Step 2 — POSTing report to %s (attempt %d/%d) …",
                endpoint,
                attempt,
                _MAX_RETRIES + 1,
            )
            response = requests.post(
                endpoint,
                headers=headers,
                json=body,
                timeout=_TIMEOUT_SECONDS,
            )

            if response.status_code == 404:
                raise RuntimeError(
                    f"API returned 404 — check that PIPELINE_KEY is correct "
                    f"and the endpoint exists at {endpoint}."
                )

            if not response.ok:
                raise RuntimeError(
                    f"API returned {response.status_code}: {response.text[:500]}"
                )

            data = response.json()
            share_url: str = data["share_url"]
            logger.info("Step 2 — report published. share_url=%s", share_url)
            return share_url

        except (RuntimeError, ValueError) as exc:
            # Non-retryable: bad status code or malformed response
            raise

        except Exception as exc:
            last_exc = exc
            if attempt <= _MAX_RETRIES:
                logger.warning(
                    "Network error on attempt %d: %s — retrying …",
                    attempt,
                    exc,
                )
            else:
                raise requests.exceptions.RequestException(
                    f"Request to {endpoint} failed after {_MAX_RETRIES + 1} attempt(s): {exc}"
                ) from exc

    # Should be unreachable, but satisfies type checker
    raise RuntimeError("publish_report: unexpected exit from retry loop")


# ---------------------------------------------------------------------------
# High-level pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(
    report_json_path: str | Path,
    html_path: str | Path,
    title: str,
    created_by: str | None = None,
    *,
    no_publish: bool = False,
    dry_run: bool = False,
) -> str | None:
    """Main entry point — runs step 1 + step 2 and returns share_url.

    Args:
        report_json_path: Path to the artifacts JSON produced by the pipeline.
        html_path:        Path to the rendered HTML report file.
        title:            Report title for the webapp.
        created_by:       Optional author email / identifier.
        no_publish:       If True, upload images but skip the API call.
        dry_run:          If True, skip all external calls and only print info.

    Returns:
        share_url string if the report was published, else None.
    """
    report_json_path = Path(report_json_path)
    html_path = Path(html_path)

    # Load artifacts JSON
    payload: Any = {}
    if report_json_path.exists():
        with open(report_json_path, encoding="utf-8") as fh:
            payload = json.load(fh)
    else:
        logger.warning("report_json_path does not exist: %s — using empty payload.", report_json_path)

    # Load rendered HTML
    if not html_path.exists():
        raise FileNotFoundError(f"HTML report not found: {html_path}")
    html_content = html_path.read_text(encoding="utf-8")

    # Derive a stable report_id from the artifacts or generate a UUID
    report_id: str = (
        payload.get("report_id")
        or payload.get("id")
        or str(uuid.uuid4())
    )

    # Collect evidence_map from artifacts (best-effort)
    evidence_map: dict[str, Any] = _collect_evidence_map(payload)

    # -----------------------------------------------------------------------
    # Dry-run mode
    # -----------------------------------------------------------------------
    if dry_run:
        print("[dry-run] Would upload evidence:")
        for asset_id, info in evidence_map.items():
            print(f"  {asset_id}: {info.get('local_path', '(no local_path)')}")
        if not no_publish:
            backend_url = os.environ.get("BACKEND_URL", "(BACKEND_URL not set)")
            print(f"[dry-run] Would POST to {backend_url}/api/reports")
            print(f"[dry-run]   title       = {title!r}")
            print(f"[dry-run]   created_by  = {created_by!r}")
            print(f"[dry-run]   html length = {len(html_content)} chars")
        else:
            print("[dry-run] --no-publish set — API call would be skipped.")
        return None

    # -----------------------------------------------------------------------
    # Step 1 — upload evidence images
    # -----------------------------------------------------------------------
    if evidence_map:
        evidence_map = upload_evidence(evidence_map, report_id)
        # Write updated evidence back into payload so URLs are included in POST
        _write_evidence_back(payload, evidence_map)
    else:
        logger.info("No evidence_map found in artifacts — skipping Cloudinary upload.")

    # -----------------------------------------------------------------------
    # Step 2 — publish to webapp API
    # -----------------------------------------------------------------------
    if no_publish:
        logger.info("--no-publish set — skipping API call.")
        return None

    share_url = publish_report(title, html_content, payload, created_by)
    return share_url


# ---------------------------------------------------------------------------
# Helpers for evidence extraction
# ---------------------------------------------------------------------------

def _collect_evidence_map(payload: Any) -> dict[str, Any]:
    """Extract a flat { asset_id: { local_path, ... } } map from the payload.

    Looks for a top-level ``evidence_map`` key first, then falls back to
    scanning ``bug_reports[].evidence_refs[].local_path``.
    """
    if isinstance(payload, dict):
        # Preferred: explicit top-level evidence_map
        if "evidence_map" in payload and isinstance(payload["evidence_map"], dict):
            return dict(payload["evidence_map"])

        # Fallback: gather from bug_reports evidence_refs
        collected: dict[str, Any] = {}
        for bug in payload.get("bug_reports", []):
            for ev in bug.get("evidence_refs", []) or bug.get("evidence", []):
                if isinstance(ev, dict) and ev.get("local_path"):
                    asset_id = ev.get("asset_id") or ev.get("asset_ref") or ev.get("type") or str(len(collected))
                    collected[str(asset_id)] = ev
        return collected

    return {}


def _write_evidence_back(payload: Any, evidence_map: dict[str, Any]) -> None:
    """Write updated evidence_map (with secure_url) back into payload in-place."""
    if not isinstance(payload, dict):
        return
    if "evidence_map" in payload:
        payload["evidence_map"] = evidence_map
    else:
        # Update individual evidence refs inside bug_reports
        for bug in payload.get("bug_reports", []):
            for ev in bug.get("evidence_refs", []) or bug.get("evidence", []):
                if isinstance(ev, dict):
                    asset_id = ev.get("asset_id") or ev.get("asset_ref") or ev.get("type")
                    if asset_id and str(asset_id) in evidence_map:
                        updated = evidence_map[str(asset_id)]
                        if "secure_url" in updated:
                            ev["secure_url"] = updated["secure_url"]
                        if "public_id" in updated:
                            ev["public_id"] = updated["public_id"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline publish step: upload evidence images to Cloudinary, "
            "then POST the report to the Next.js webapp API."
        )
    )
    parser.add_argument(
        "--report-json",
        required=True,
        metavar="PATH",
        help="Path to the artifacts JSON file produced by the pipeline.",
    )
    parser.add_argument(
        "--html",
        required=True,
        metavar="PATH",
        help="Path to the rendered HTML report file.",
    )
    parser.add_argument(
        "--title",
        required=True,
        help='Report title shown in the webapp (e.g. "Attendance Report Q2").',
    )
    parser.add_argument(
        "--created-by",
        default=None,
        metavar="EMAIL",
        help="Optional author email / identifier.",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        default=False,
        help="Upload images to Cloudinary but skip the API call.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Skip all external calls; just print what would happen.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    try:
        share_url = run_pipeline(
            report_json_path=args.report_json,
            html_path=args.html,
            title=args.title,
            created_by=args.created_by,
            no_publish=args.no_publish,
            dry_run=args.dry_run,
        )
    except (EnvironmentError, FileNotFoundError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 1
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        return 1

    if share_url:
        print(share_url)
    elif not args.dry_run:
        print("(report published without share_url or --no-publish was set)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
