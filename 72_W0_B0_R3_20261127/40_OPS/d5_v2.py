#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D5 v2: measure the receiver's real external-process use, not string counts.

The previous version counted literals in rights.py and reported icacls=0 while the
product's own read path invokes icacls ten times per source.  This version wraps
`subprocess.run` in-process, drives one real receive, and reports what actually ran.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
CODE = WAVE / "10_CODE"
OUT = WAVE / "40_OPS" / "d5_receiver_f2_v2_20261127.json"
ENVELOPE = WAVE / "40_OPS" / "b0_sourcereadset_r9_20261127.json"
SOURCES = [
    Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\藍圖\SST_PLP_PH01_W0_全批次藍圖.md"),
    Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_WM\SST_PLP_PH01_ALL_WNM_2026-11-24_r2\SST_PLP_PH01_W0M_實質正文.md"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(root: Path) -> dict[str, str]:
    rows = {}
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".tmp_tests"}]
        for name in sorted(filenames):
            p = Path(dirpath) / name
            try:
                rows[str(p.relative_to(root))] = sha(p)
            except OSError:
                rows[str(p.relative_to(root))] = "UNREADABLE"
    return rows


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    sys.path.insert(0, str(CODE))
    calls: Counter = Counter()
    real_run = subprocess.run

    def counting_run(*args, **kwargs):
        argv = args[0] if args else kwargs.get("args")
        name = os.path.basename(str(argv[0])).lower() if argv else "?"
        calls[name] += 1
        return real_run(*args, **kwargs)

    pre_sources = {str(p): sha(p) for p in SOURCES}
    pre_tree = tree(CODE)
    subprocess.run = counting_run
    try:
        from consumers import b3
        receipt = b3.receive_envelope(ENVELOPE.read_bytes())
    finally:
        subprocess.run = real_run
    post_sources = {str(p): sha(p) for p in SOURCES}
    post_tree = tree(CODE)
    changed = sorted(set(pre_tree) ^ set(post_tree)) + \
        sorted(k for k in pre_tree if k in post_tree and pre_tree[k] != post_tree[k])

    import sysconfig
    stdlib = sysconfig.get_paths()["stdlib"].lower()
    own = ("b0_r3_receiver", "consumers", "b0_reader")
    outside = [n for n, m in sorted(sys.modules.items())
               if (getattr(m, "__file__", "") or "").lower().startswith(stdlib) is False
               and getattr(m, "__file__", None)
               and not n.startswith("_")
               and not any(n == o or n.startswith(o + ".") for o in own)]
    import importlib.metadata as md
    dists = {}
    for d in ("cryptography", "cffi", "pycparser", "pywin32"):
        try:
            dists[d] = md.version(d)
        except Exception:
            dists[d] = None

    out = {
        "schema": "SST.PH01.W0.B0.R3.D5ReceiverF2/2",
        "measured_at": now.isoformat(),
        "external_process_calls_observed": dict(sorted(calls.items())),
        "external_process_total": sum(calls.values()),
        "how_measured": ("subprocess.run wrapped in-process around one real receive; every call "
                         "counted by executable name, including the product's own icacls ACL reads"),
        "modules_outside_stdlib_and_package": outside,
        "distributions": dists,
        "python": sys.version.split()[0],
        "native_first": {
            "network_modules_in_scope": [n for n in outside
                                         if n in {"socket", "ssl", "http", "urllib3", "requests"}],
            "claim_ceiling": "Import-surface observation only; no packet-level OFF proof.",
        },
        "no_write_observation": {
            "source_sha_before": pre_sources,
            "source_sha_after": post_sources,
            "sources_unchanged": pre_sources == post_sources,
            "code_tree_files": [len(pre_tree), len(post_tree)],
            "code_tree_changes": changed,
            "receive_verdict": receipt.get("verdict"),
            "no_product_write_observed": pre_sources == post_sources and not changed,
        },
    }
    OUT.write_bytes(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("external_process_calls_observed",
                                          "external_process_total",
                                          "modules_outside_stdlib_and_package",
                                          "distributions", "no_write_observation")},
                     ensure_ascii=False, indent=1)[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
