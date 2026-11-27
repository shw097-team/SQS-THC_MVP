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
        "path": str(WAVE_ROOT / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r9.json"),
        "sha256": "8348c7ca686718e591741c0ca92959145e24da16d9948a5265c8cf7ecb069f1d",
    },
    "fixture": {
        "path": str(WAVE_ROOT / "20_TESTS" / "fixture" / "DEPLOYMENT_fixture_20261127_r9.json"),
        "sha256": "59c5553466fa36737edaf8bf7b3bb5ac37ff9e9279f076ddf0e9858f92696e95",
    },
}

REFUSED_ARGUMENTS = ("--context", "--root", "--allowed-root", "--epoch", "--trust-root")


def load(deployment_id: str) -> dict[str, Any]:
    entry = PINNED[deployment_id]
    return load_pinned_deployment(deployment_id, entry["sha256"], entry["path"])
