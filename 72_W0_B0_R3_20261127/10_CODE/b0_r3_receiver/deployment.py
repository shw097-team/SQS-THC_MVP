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
        "path": str(WAVE_ROOT / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r10.json"),
        "sha256": "c5efcca4e2b4798ee91b5f6a5384bc9de073d4ea036d954e0704fb1a0c75a669",
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
