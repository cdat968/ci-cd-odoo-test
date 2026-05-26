#!/usr/bin/env python3
"""
upload_report.py — Upload an HTML test report to the QA webapp (Component A).

Usage (from CI):
    python scripts/upload_report.py \
        --html path/to/report.html \
        --title "My Test Run" \
        --report-dir path/to/report-root \
        --created-by ci-bot

Required env vars:
    BACKEND_URL               — base URL of the webapp (e.g. https://xxx.vercel.app)
    COMPONENT_A_PIPELINE_KEY  — value for the X-Pipeline-Key header

Optional env vars:
    CLOUDINARY_URL            — cloudinary://key:secret@cloud_name
                                If set, relative evidence images are uploaded to
                                Cloudinary and their src paths are rewritten to
                                HTTPS URLs before the HTML is POSTed.

Stdout: ONLY the share_url returned by the API.
Stderr: all informational / warning / error messages.
Exit:   always 0 (errors must not fail the CI pipeline).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import json
import urllib.parse
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _err(msg: str) -> None:
    """Print a message to stderr."""
    print(msg, file=sys.stderr)


def _parse_cloudinary_url(url: str) -> dict:
    """
    Parse a Cloudinary URL of the form cloudinary://api_key:api_secret@cloud_name
    and return a dict suitable for cloudinary.config().
    """
    parsed = urllib.parse.urlparse(url)
    return {
        "cloud_name": parsed.hostname,
        "api_key": parsed.username,
        "api_secret": parsed.password,
    }


def _upload_images_to_cloudinary(
    html: str,
    report_dir: Path,
    cloudinary_url: str,
) -> str:
    """
    Find all relative evidence image paths in *html*, upload each unique file to
    Cloudinary (folder: qa-reports/ci), and rewrite the src values to the
    returned HTTPS URLs.

    Returns the (possibly modified) HTML string.
    """
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        _err(
            "WARNING: 'cloudinary' package is not installed. "
            "Skipping image upload. Run: pip install cloudinary"
        )
        return html

    # Configure the Cloudinary SDK.
    try:
        config = _parse_cloudinary_url(cloudinary_url)
        cloudinary.config(**config)
    except Exception as exc:
        _err(f"WARNING: Failed to parse CLOUDINARY_URL: {exc}. Skipping image upload.")
        return html

    # Find all unique relative paths matching the pattern.
    pattern = re.compile(r'\bsrc\s*:\s*"(assets/evidence/[^"]+)"')
    relative_paths: list[str] = list(dict.fromkeys(pattern.findall(html)))

    if not relative_paths:
        _err("INFO: No evidence image paths found in HTML.")
        return html

    _err(f"INFO: Found {len(relative_paths)} unique evidence image(s) to upload.")

    # Upload each file and build a replacement map.
    replacement_map: dict[str, str] = {}
    for rel_path in relative_paths:
        abs_path = report_dir / rel_path
        if not abs_path.is_file():
            _err(f"WARNING: Image not found, skipping: {abs_path}")
            continue
        try:
            result = cloudinary.uploader.upload(
                str(abs_path),
                folder="qa-reports/ci",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                resource_type="image",
            )
            cloud_url: str = result.get("secure_url", "")
            if cloud_url:
                replacement_map[rel_path] = cloud_url
                _err(f"INFO: Uploaded {rel_path} → {cloud_url}")
            else:
                _err(f"WARNING: No secure_url in Cloudinary response for {rel_path}.")
        except Exception as exc:
            _err(f"WARNING: Failed to upload {rel_path}: {exc}")

    # Rewrite occurrences in the HTML.
    def _replacer(match: re.Match) -> str:
        rel = match.group(1)
        if rel in replacement_map:
            return f'"src": "{replacement_map[rel]}"'
        return match.group(0)

    html = pattern.sub(_replacer, html)
    _err(f"INFO: Rewrote {len(replacement_map)} image src(s) to Cloudinary URLs.")
    return html


def _post_report(
    backend_url: str,
    pipeline_key: str,
    title: str,
    html: str,
    created_by: str,
) -> str:
    """
    POST the report to BACKEND_URL/api/reports and return the share_url.
    Raises on HTTP or network errors.
    """
    import urllib.request

    url = backend_url.rstrip("/") + "/api/reports"
    payload = json.dumps(
        {
            "title": title,
            "html": html,
            "payload": {},
            "created_by": created_by,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Pipeline-Key": pipeline_key,
        },
        method="POST",
    )

    _err(f"INFO: POSTing report to {url} …")
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")

    data = json.loads(body)
    share_url: str = data.get("share_url", "")
    if not share_url:
        raise ValueError(f"API response did not contain 'share_url'. Response: {body}")
    return share_url


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload an HTML test report to the QA webapp."
    )
    parser.add_argument("--html", required=True, help="Path to the HTML report file.")
    parser.add_argument("--title", required=True, help="Title for the report.")
    parser.add_argument(
        "--report-dir",
        required=True,
        help="Root directory of the report (used to resolve relative image paths).",
    )
    parser.add_argument(
        "--created-by",
        default="ci-bot",
        help="Who created this report (default: ci-bot).",
    )
    args = parser.parse_args()

    # ---- Validate required env vars ----------------------------------------
    backend_url = os.environ.get("BACKEND_URL", "").strip()
    pipeline_key = os.environ.get("COMPONENT_A_PIPELINE_KEY", "").strip()
    cloudinary_url = os.environ.get("CLOUDINARY_URL", "").strip()

    if not backend_url:
        _err("ERROR: BACKEND_URL environment variable is not set.")
        sys.exit(0)

    if not pipeline_key:
        _err("ERROR: COMPONENT_A_PIPELINE_KEY environment variable is not set.")
        sys.exit(0)

    # ---- Read HTML ---------------------------------------------------------
    html_path = Path(args.html)
    if not html_path.is_file():
        _err(f"ERROR: HTML file not found: {html_path}")
        sys.exit(0)

    try:
        html_content = html_path.read_text(encoding="utf-8")
    except Exception as exc:
        _err(f"ERROR: Could not read HTML file: {exc}")
        sys.exit(0)

    report_dir = Path(args.report_dir)
    if not report_dir.is_dir():
        _err(f"WARNING: --report-dir '{report_dir}' is not a directory. Image upload may fail.")

    # ---- Optionally rewrite images -----------------------------------------
    if cloudinary_url:
        _err("INFO: CLOUDINARY_URL detected — uploading evidence images …")
        html_content = _upload_images_to_cloudinary(html_content, report_dir, cloudinary_url)
    else:
        _err("INFO: CLOUDINARY_URL not set — skipping image upload.")

    # ---- POST to webapp ----------------------------------------------------
    try:
        share_url = _post_report(
            backend_url=backend_url,
            pipeline_key=pipeline_key,
            title=args.title,
            html=html_content,
            created_by=args.created_by,
        )
        # ONLY this line goes to stdout.
        print(share_url)
    except Exception as exc:
        _err(f"ERROR: Failed to upload report: {exc}")

    # Always exit 0.
    sys.exit(0)


if __name__ == "__main__":
    main()
