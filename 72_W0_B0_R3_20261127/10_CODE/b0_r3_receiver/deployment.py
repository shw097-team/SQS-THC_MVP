# -*- coding: utf-8 -*-
"""Pinned deployment registry.

The pins live in module scope on purpose: a deployment descriptor is located and
authenticated here, never by a caller-supplied path.  `/r0` (prod) is the real owner
rights chain; `fixture` is a separate, labelled trust anchor used only by the isolated
algorithm tests and carries no product rights.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .receiver import load_pinned_deployment

WAVE_ROOT = Path(__file__).resolve().parents[2]

PINNED: dict[str, dict[str, str]] = {
    "prod": {
        "path": str(WAVE_ROOT / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r8.json"),
        "sha256": "78c78defe5058cab817fbb916e6656b4f3d061ac7bc4ada1381ebe4248e4aac3",
    },
    "fixture": {
        "path": str(WAVE_ROOT / "20_TESTS" / "fixture" / "DEPLOYMENT_fixture_20261127.json"),
        "sha256": "4aaaf297a1f473f13179a5f76bfccf754821320922defe7f40587bbb8738a1d5",
    },
}

REFUSED_ARGUMENTS = ("--context", "--root", "--allowed-root", "--epoch", "--trust-root")


def load(deployment_id: str) -> dict[str, Any]:
    entry = PINNED[deployment_id]
    return load_pinned_deployment(deployment_id, entry["sha256"], entry["path"])
