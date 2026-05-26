"""
cloudinary_uploader.py — standalone helper for uploading evidence images to Cloudinary.

Can be used independently from publish.py.

Requires:
    CLOUDINARY_URL env var (Cloudinary Python SDK parses it automatically)
    e.g. cloudinary://api_key:api_secret@cloud_name
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _get_cloudinary():
    """Lazily import cloudinary to give a friendly error if not installed."""
    try:
        import cloudinary
        import cloudinary.uploader
        return cloudinary, cloudinary.uploader
    except ImportError as exc:
        raise ImportError(
            "cloudinary package is not installed. "
            "Run: pip install cloudinary>=2.3.0"
        ) from exc


def upload_image(local_path: str, report_id: str, asset_id: str) -> dict[str, Any]:
    """Upload a single image to Cloudinary.

    Args:
        local_path: Absolute or relative path to the local image file.
        report_id:  Unique identifier for the report (used as folder name).
        asset_id:   Unique identifier for this asset (used as public_id).

    Returns:
        dict with keys:
            secure_url    — HTTPS URL of the uploaded image
            public_id     — Cloudinary public_id (folder/asset_id)
            original_path — The local_path that was uploaded

    Raises:
        Exception: re-raises any Cloudinary upload error after logging.
    """
    cloudinary_mod, uploader = _get_cloudinary()

    cloudinary_url = os.environ.get("CLOUDINARY_URL")
    if not cloudinary_url:
        raise EnvironmentError(
            "CLOUDINARY_URL environment variable is not set. "
            "Set it to cloudinary://api_key:api_secret@cloud_name"
        )

    logger.debug("Uploading %s to Cloudinary (folder=qa-reports/%s, public_id=%s)", local_path, report_id, asset_id)

    result = uploader.upload(
        local_path,
        folder=f"qa-reports/{report_id}",
        public_id=asset_id,
    )

    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"],
        "original_path": local_path,
    }


def upload_evidence_map(evidence_map: dict[str, Any], report_id: str) -> dict[str, Any]:
    """Batch-upload all evidence images in evidence_map.

    Each value in evidence_map should be a dict with at least a ``local_path``
    key.  After a successful upload, ``secure_url`` and ``public_id`` are added
    to the entry.  If an individual upload fails, a warning is logged and the
    original entry (with ``local_path`` intact) is kept so the caller can fall
    back to local paths.

    Args:
        evidence_map: Dict mapping asset_id -> { local_path, ...other fields }
        report_id:    Unique identifier for the report (used as Cloudinary folder).

    Returns:
        Updated evidence_map where each successfully uploaded entry has
        ``secure_url`` and ``public_id`` filled in.
    """
    updated: dict[str, Any] = {}

    for asset_id, asset_info in evidence_map.items():
        entry = dict(asset_info)  # shallow copy so we don't mutate the input
        local_path = entry.get("local_path", "")

        if not local_path:
            logger.warning("Evidence entry %s has no local_path — skipping upload.", asset_id)
            updated[asset_id] = entry
            continue

        try:
            upload_result = upload_image(local_path, report_id, asset_id)
            entry["secure_url"] = upload_result["secure_url"]
            entry["public_id"] = upload_result["public_id"]
            logger.info("Uploaded %s -> %s", asset_id, upload_result["secure_url"])
        except Exception as exc:
            logger.warning(
                "Failed to upload evidence %s (path=%s): %s — continuing with local path.",
                asset_id,
                local_path,
                exc,
            )

        updated[asset_id] = entry

    return updated
