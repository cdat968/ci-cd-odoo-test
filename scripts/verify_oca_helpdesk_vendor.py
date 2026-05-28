#!/usr/bin/env python3
"""Verify the vendored OCA Helpdesk slice is present and internally complete."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = ROOT / "addons_oca" / "helpdesk"
REQUIRED_ADDONS = ("helpdesk_mgmt", "helpdesk_mgmt_project")
ODOO_CORE_ADDONS = {"mail", "portal", "project"}


def load_manifest(addon: str) -> dict:
    manifest_path = VENDOR_ROOT / addon / "__manifest__.py"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest: {manifest_path.relative_to(ROOT)}")
    return ast.literal_eval(manifest_path.read_text(encoding="utf-8"))


def main() -> None:
    vendored = set(REQUIRED_ADDONS)
    for addon in REQUIRED_ADDONS:
        manifest = load_manifest(addon)
        missing = [
            dependency
            for dependency in manifest.get("depends", [])
            if dependency not in vendored and dependency not in ODOO_CORE_ADDONS
        ]
        if missing:
            joined = ", ".join(missing)
            raise SystemExit(f"{addon} has non-vendored dependencies: {joined}")

        version = manifest.get("version", "unknown")
        print(f"{addon} {version}: ok")


if __name__ == "__main__":
    main()
