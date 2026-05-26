"""
test_publish.py — unit tests for pipeline/publish.py and pipeline/cloudinary_uploader.py

Run with:
    python -m unittest pipeline/test_publish.py
or:
    python pipeline/test_publish.py
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the repo root is on sys.path so imports work when run directly.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Helper: build a minimal fake cloudinary upload response
# ---------------------------------------------------------------------------

def _make_cloudinary_response(asset_id: str, report_id: str) -> dict:
    return {
        "secure_url": f"https://res.cloudinary.com/demo/image/upload/qa-reports/{report_id}/{asset_id}.png",
        "public_id": f"qa-reports/{report_id}/{asset_id}",
    }


# ---------------------------------------------------------------------------
# Test: upload_evidence_map (dry-run via mock)
# ---------------------------------------------------------------------------

class TestUploadEvidenceMap(unittest.TestCase):
    """Tests for cloudinary_uploader.upload_evidence_map"""

    def _make_evidence_map(self):
        return {
            "EVD-001": {"local_path": "/tmp/step1.png", "title": "Step 1 screenshot"},
            "EVD-002": {"local_path": "/tmp/step2.png", "title": "Step 2 screenshot"},
        }

    def test_upload_evidence_map_dry_run(self):
        """Mock cloudinary SDK, verify that secure_url and public_id are filled."""
        report_id = "test-report-001"
        evidence_map = self._make_evidence_map()

        # Patch cloudinary.uploader.upload at the location it is imported inside
        # cloudinary_uploader.py
        with patch("cloudinary.uploader") as mock_uploader_module:
            # Build a fresh mock for the uploader so upload() is callable
            mock_uploader = MagicMock()
            mock_uploader_module.upload.side_effect = lambda path, folder, public_id: _make_cloudinary_response(public_id.split("/")[-1], report_id)

            # Patch the lazy import inside cloudinary_uploader
            with patch("pipeline.cloudinary_uploader._get_cloudinary", return_value=(MagicMock(), mock_uploader)):
                with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@cloud"}):
                    from pipeline.cloudinary_uploader import upload_evidence_map

                    result = upload_evidence_map(evidence_map, report_id)

        # Both entries must have secure_url and public_id
        self.assertIn("EVD-001", result)
        self.assertIn("EVD-002", result)

        for asset_id in ("EVD-001", "EVD-002"):
            entry = result[asset_id]
            self.assertIn("secure_url", entry, f"{asset_id} should have secure_url")
            self.assertIn("public_id", entry, f"{asset_id} should have public_id")
            self.assertTrue(entry["secure_url"].startswith("https://"), f"{asset_id} secure_url should be HTTPS")
            # original fields must be preserved
            self.assertIn("local_path", entry, f"{asset_id} should still have local_path")
            self.assertIn("title", entry, f"{asset_id} should still have title")

    def test_upload_evidence_map_partial_failure(self):
        """If one upload fails, the failed entry keeps local_path; others succeed."""
        report_id = "test-report-002"
        evidence_map = {
            "EVD-OK":  {"local_path": "/tmp/ok.png"},
            "EVD-FAIL": {"local_path": "/tmp/fail.png"},
        }

        def _side_effect(path, folder, public_id):
            if "FAIL" in public_id:
                raise IOError("Simulated upload failure")
            return _make_cloudinary_response(public_id.split("/")[-1], report_id)

        mock_uploader = MagicMock()
        mock_uploader.upload.side_effect = _side_effect

        with patch("pipeline.cloudinary_uploader._get_cloudinary", return_value=(MagicMock(), mock_uploader)):
            with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@cloud"}):
                from pipeline import cloudinary_uploader
                # Reload to avoid cached import state
                import importlib
                importlib.reload(cloudinary_uploader)

                result = cloudinary_uploader.upload_evidence_map(evidence_map, report_id)

        # Successful entry has secure_url
        self.assertIn("secure_url", result["EVD-OK"])
        # Failed entry keeps local_path, no secure_url
        self.assertNotIn("secure_url", result["EVD-FAIL"])
        self.assertEqual(result["EVD-FAIL"]["local_path"], "/tmp/fail.png")


# ---------------------------------------------------------------------------
# Test: publish_report success
# ---------------------------------------------------------------------------

class TestPublishReportSuccess(unittest.TestCase):
    """Tests for publish.publish_report — success path."""

    def test_publish_report_success(self):
        """Mock requests.post, verify payload shape and that share_url is returned."""
        import importlib
        import pipeline.publish as publish_mod
        importlib.reload(publish_mod)

        fake_share_url = "https://example.vercel.app/r/abc123?t=tok"
        fake_response = MagicMock()
        fake_response.status_code = 201
        fake_response.ok = True
        fake_response.json.return_value = {"id": "abc123", "share_url": fake_share_url}

        with patch.dict(os.environ, {"BACKEND_URL": "https://example.vercel.app", "PIPELINE_KEY": "secret-key"}):
            with patch("requests.post", return_value=fake_response) as mock_post:
                share_url = publish_mod.publish_report(
                    title="Test Report",
                    html="<html><body>Hello</body></html>",
                    payload={"bug_reports": []},
                    created_by="tester@example.com",
                )

        # share_url must match
        self.assertEqual(share_url, fake_share_url)

        # Verify the POST was called once with correct arguments
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args

        # URL
        called_url = call_kwargs[0][0] if call_kwargs[0] else call_kwargs[1].get("url") or call_kwargs[0][0]
        self.assertIn("/api/reports", str(call_kwargs))

        # Header
        called_headers = call_kwargs[1].get("headers") or {}
        self.assertEqual(called_headers.get("X-Pipeline-Key"), "secret-key")

        # Body fields
        called_json = call_kwargs[1].get("json") or {}
        self.assertEqual(called_json.get("title"), "Test Report")
        self.assertIn("html", called_json)
        self.assertIn("payload", called_json)
        self.assertEqual(called_json.get("created_by"), "tester@example.com")

        # Timeout
        self.assertEqual(call_kwargs[1].get("timeout"), 30)


# ---------------------------------------------------------------------------
# Test: publish_report wrong key → 404 → exception
# ---------------------------------------------------------------------------

class TestPublishReportWrongKey(unittest.TestCase):
    """Tests for publish.publish_report — 404 response."""

    def test_publish_report_wrong_key(self):
        """Mock 404 response, verify RuntimeError is raised."""
        import importlib
        import pipeline.publish as publish_mod
        importlib.reload(publish_mod)

        fake_response = MagicMock()
        fake_response.status_code = 404
        fake_response.ok = False
        fake_response.text = "Not found"

        with patch.dict(os.environ, {"BACKEND_URL": "https://example.vercel.app", "PIPELINE_KEY": "wrong-key"}):
            with patch("requests.post", return_value=fake_response):
                with self.assertRaises(RuntimeError) as ctx:
                    publish_mod.publish_report(
                        title="Test",
                        html="<html/>",
                        payload={},
                        created_by=None,
                    )

        error_message = str(ctx.exception)
        self.assertIn("404", error_message)

    def test_publish_report_missing_backend_url(self):
        """Missing BACKEND_URL should raise EnvironmentError immediately."""
        import importlib
        import pipeline.publish as publish_mod
        importlib.reload(publish_mod)

        env = {k: v for k, v in os.environ.items() if k != "BACKEND_URL"}
        env.pop("BACKEND_URL", None)

        with patch.dict(os.environ, env, clear=True):
            # Restore other vars that may be needed but not BACKEND_URL
            with self.assertRaises(EnvironmentError) as ctx:
                publish_mod.publish_report(
                    title="Test",
                    html="<html/>",
                    payload={},
                )

        self.assertIn("BACKEND_URL", str(ctx.exception))

    def test_publish_report_missing_pipeline_key(self):
        """Missing PIPELINE_KEY should raise EnvironmentError immediately."""
        import importlib
        import pipeline.publish as publish_mod
        importlib.reload(publish_mod)

        with patch.dict(os.environ, {"BACKEND_URL": "https://example.vercel.app"}, clear=False):
            # Temporarily remove PIPELINE_KEY
            original = os.environ.pop("PIPELINE_KEY", None)
            try:
                with self.assertRaises(EnvironmentError) as ctx:
                    publish_mod.publish_report(
                        title="Test",
                        html="<html/>",
                        payload={},
                    )
            finally:
                if original is not None:
                    os.environ["PIPELINE_KEY"] = original

        self.assertIn("PIPELINE_KEY", str(ctx.exception))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
