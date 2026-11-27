# -*- coding: utf-8 -*-
"""Pinned deployment registry.

The pins live in module scope on purpose: a deployment descriptor is located and
authenticated here, never by a caller-supplied path.  `/r0` (prod) is the real owner
rights chain; `fixture` is a separate, labelled trust anchor used only by the isolated
algorithm tests and carries no product rights.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .receiver import load_pinned_deployment

WAVE_ROOT = Path(__file__).resolve().parents[2]

# the product tree this wave relocated; the receiver reuses its trust primitives instead of
# growing a second Windows open path.  Bound here, never from a caller argument.
_PRODUCT_TREE = WAVE_ROOT / "20_DEV"
if str(_PRODUCT_TREE) not in sys.path:
    sys.path.insert(0, str(_PRODUCT_TREE))

PINNED: dict[str, dict[str, str]] = {
    "prod": {
        "path": str(WAVE_ROOT / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r11.json"),
        "sha256": "9d89781cbce772c14fa1d6edcc7ffa8231331827cef1150644736ea8666a4571",
    },
    "fixture": {
        "path": str(WAVE_ROOT / "20_TESTS" / "fixture" / "DEPLOYMENT_fixture_20261127_r9.json"),
        "sha256": "08fbce8bc27df86329f24ef3b09e486aa4ff2620c7de0f00922566fadbe497a8",
    },
}

REFUSED_ARGUMENTS = ("--context", "--root", "--allowed-root", "--epoch", "--trust-root")


def load(deployment_id: str) -> dict[str, Any]:
    entry = PINNED[deployment_id]
    return load_pinned_deployment(deployment_id, entry["sha256"], entry["path"])
