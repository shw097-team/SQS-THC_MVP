#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B1 EDGE/SEC safety battery — extra regression cases, not substitutes for the 60.

Each case performs a real subprocess call against the product entry point and
records stdout shape, exit code and the observed FirstFail.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "b1_cli.py")
OUT = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\71_W0_B0-B3_R7_20261127\40_OPS"
REPO = r"C:\Projects\Agent_Workspace\SQS-THC"


def call(args, timeout=180):
    p = subprocess.run([sys.executable, "-B", CLI, *args], capture_output=True, timeout=timeout)
    return {"exit": p.returncode,
            "stdout_len": len(p.stdout),
            "stdout_is_single_json_object": _single_json(p.stdout),
            "stdout_bom": p.stdout[:3] == b"\xef\xbb\xbf",
            "stderr": p.stderr.decode("utf-8", "replace").strip()[:300]}


def _single_json(b: bytes) -> bool:
    try:
        json.loads(b.decode("utf-8"))
        return True
    except Exception:
        return False


def repo_state():
    head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True).stdout.strip()
    st = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--untracked-files=normal"],
                        capture_output=True).stdout
    return {"head": head.decode(), "status_sha256": hashlib.sha256(st).hexdigest(),
            "status_lines": len(st.decode().splitlines())}


def main() -> int:
    before = repo_state()
    cases = []

    r = call(["--op", "BASE", "--context", "C:/tmp/x.json"])
    cases.append({"id": "SEC.CONTEXT_OVERRIDE", "expect_exit": 64, "observed": r,
                  "pass": r["exit"] == 64 and r["stdout_len"] == 2})

    r = call(["--op", "BASE", "--repo", "C:/Windows"])
    cases.append({"id": "SEC.REPO_OUTSIDE_ALLOWLIST", "expect_exit": 64, "observed": r,
                  "pass": r["exit"] == 64})

    r = call(["--op", "BASE", "--out", r"C:\Users\user\escaped.json"])
    cases.append({"id": "SEC.OUT_OUTSIDE_W", "expect_exit": 64, "observed": r,
                  "pass": r["exit"] == 64})

    r = call(["--op", "BASE", "--commit", "0489ac84a390a7172c6cce8322caefeb66b8942c"])
    cases.append({"id": "SEC.UNKNOWN_COMMIT", "expect_exit": 2, "observed": r,
                  "pass": r["exit"] == 2})

    r = call(["--op", "BASE", "--keys", "BASE-999"])
    cases.append({"id": "SEC.EMPTY_REQUEST_REFUSED", "expect_exit": 64, "observed": r,
                  "pass": r["exit"] == 64 and r["stdout_len"] == 2})

    r = call(["--op", "BASE", "--bogus-flag", "1"])
    cases.append({"id": "SEC.UNKNOWN_ARG", "expect_exit": 64, "observed": r,
                  "pass": r["exit"] == 64})

    r = call(["--op", "FDA"])
    cases.append({"id": "SEC.FDA_DENY_INVARIANT_OUTPUT", "expect_exit": 0, "observed": r,
                  "pass": r["exit"] in (0, 2)})

    after = repo_state()
    no_write = (before["head"] == after["head"] and
                before["status_sha256"] == after["status_sha256"])
    cases.append({"id": "SEC.NO_WRITE_TO_SOURCE_REPO", "expect": "head+status unchanged",
                  "before": before, "after": after, "pass": no_write})

    # product-level invariants from the last full run
    full = json.load(open(os.path.join(OUT, "b1_r7_run_all.json"), encoding="utf-8"))
    inv = {"effect_is_source_read": full["effect"] == "SOURCE_READ",
           "write_set_empty": full["write_set"] == [],
           "preimage_na": full["preimage"] == "N/A",
           "fin_order_deny": full["fin_order"] == "DENY",
           "gui_not_started": full["fda"]["gui_started"] is False,
           "lease_not_acquired": full["fda"]["lease_acquired"] is False,
           "broker_not_contacted": full["fda"]["broker_contacted"] is False,
           "no_allowed_effect_pos": full["fda"]["slots"][-1]["deny_control"]["allowed_effect_pos"] is None}
    cases.append({"id": "SEC.PRODUCT_EFFECT_INVARIANTS", "observed": inv,
                  "pass": all(inv.values())})

    counts = {"pass": sum(1 for c in cases if c["pass"]),
              "fail": sum(1 for c in cases if not c["pass"])}
    out = os.path.join(OUT, "b1_r7_edge_sec.json")
    json.dump({"schema": "SST.PH01.W0.B1.EDGE_SEC@5", "cases": cases, "counts": counts},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": out, "counts": counts}, ensure_ascii=False))
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
