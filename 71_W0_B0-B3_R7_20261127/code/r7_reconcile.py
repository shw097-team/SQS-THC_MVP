#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-key reconciliation for B1 and per-case delta for B2 — measured, not narrated.

B1: every BASE/KERNEL target is classified by the identity the product actually resolved
(TRACKED in the repo at the pinned commit, disk-only, allowlist-verified external carrier, or
outside the owner allowlist), so "PARTIAL 5" becomes a table with a cause and an owner.

B2: the 2,854→2,786 move is explained case by case: which requiredness cells are author-
qualified (no declared contract), which remain UNKNOWN, and why nothing else moved.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_spec as SPEC

W = r"<LOCAL_ROOT>"
R7 = os.path.join(W, "71_W0_B0-B3_R7_20261127")
OPS = os.path.join(R7, "40_OPS")


def b1() -> dict:
    run = json.load(open(os.path.join(OPS, "b1_r7_run_all.json"), encoding="utf-8"))
    rows = []
    for e in run["base"]["entries"]:
        targets = e.get("targets") or []
        statuses = [t.get("status") for t in targets]
        if any(s == "NOT_IN_OWNER_ALLOWLIST" for s in statuses):
            cause, owner = "TARGET_OUTSIDE_OWNER_ALLOWLIST", "FDA Source Owner (D-2)"
        elif all(s in ("TRACKED", "TRACKED_CONTENT_MATCH") for s in statuses):
            cause, owner = "TRACKED_AT_PINNED_COMMIT", "-"
        elif all(s == "DISK_DIRECTORY" for s in statuses):
            cause, owner = "DISK_DIRECTORY_NOT_TRACKED", "Repo owner (commit the directory)"
        elif any(s == "DISK_BUT_UNTRACKED" for s in statuses):
            cause, owner = "DISK_BUT_UNTRACKED", "Repo owner (commit or declare excluded)"
        elif all(s in ("ALLOWLIST_VERIFIED",) for s in statuses):
            cause, owner = "EXTERNAL_CARRIER_ALLOWLIST_VERIFIED", "-"
        else:
            cause, owner = "MIXED", "see per-target statuses"
        rows.append({"key": e.get("key"), "targets": len(targets), "statuses": statuses,
                     "cause": cause, "owner": owner})
    summary = {}
    for r in rows:
        summary[r["cause"]] = summary.get(r["cause"], 0) + 1
    return {"schema": "SST.PH01.W0.B1.BaseReconcile@1",
            "keys": len(rows), "by_cause": summary, "rows": rows,
            "claim_ceiling": ("each row states the identity the product resolved; no row is "
                              "called partial without a cause")}


def b2() -> dict:
    tqaep = json.load(open(os.path.join(OPS, "b2_r7_tqaep.json"), encoding="utf-8"))
    cases = tqaep["cases"]
    rows = cases.values() if isinstance(cases, dict) else cases
    qualified, unknown, other = [], [], []
    for c in rows:
        if c["verdict"] != "HOLD":
            continue
        act = c.get("actual") or {}
        basis = str(act.get("requiredness_basis") or "")
        if "AUTHOR_QUALIFIER_UNRATIFIED" in basis:
            m = re.search(r"cell '([^']+)'", basis)
            qualified.append({"case_id": c["case_id"],
                              "cell": m.group(1) if m else act.get("requiredness"),
                              "basis": basis})
        elif (act.get("requiredness") in (None, "UNKNOWN")) or "not in the closed" in basis:
            unknown.append({"case_id": c["case_id"], "cell": act.get("requiredness"),
                            "basis": basis})
        else:
            other.append({"case_id": c["case_id"], "basis": basis})
    return {"schema": "SST.PH01.W0.B2.QualifierDelta@1",
            "hold_total": len(qualified) + len(unknown) + len(other),
            "author_qualified_holds": len(qualified),
            "unknown_requiredness_holds": len(unknown),
            "other_holds": len(other),
            "qualified_cells": sorted({q["cell"] for q in qualified}),
            "cases": {"author_qualified": qualified, "unknown": unknown, "other": other},
            "claim_ceiling": ("a cell outside the declared requiredness vocabulary holds; the "
                              "verbatim cell is preserved so the owner can adopt a contract")}


def main() -> int:
    b1r = b1()
    b2r = b2()
    json.dump(b1r, open(os.path.join(OPS, "b1_r7_base_reconcile.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    json.dump(b2r, open(os.path.join(OPS, "b2_r7_qualifier_delta.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"b1_by_cause": b1r["by_cause"],
                      "b2_holds": b2r["hold_total"],
                      "b2_author_qualified": b2r["author_qualified_holds"],
                      "b2_unknown": b2r["unknown_requiredness_holds"],
                      "b2_other": b2r["other_holds"],
                      "qualified_cells": b2r["qualified_cells"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
