#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 NEG reconciliation — compare each executed mutation with the SPEC's declared case.

Why this exists: the first r7 TQAEP pass counted 44 `PASS_REFUSAL` on the fact that a
CHILD atom is absent from the B2 ToolReadSet. That fact is true for every CHILD atom and
is independent of the mutation, so it cannot support a NEG verdict. This module drives the
comparison the SPEC actually declares:

  * `expected` = the case table's own FirstFail token (AUTHOR:TRACE_ORPHAN /
    AUTHOR:NEG_MISSING / AUTHOR:CHILD_RULE_HOLD:<key> / SUBSTANTIVE_GAP);
  * `observed` = the first_fail the product entry really returned for the mutated set;
  * `faithful` = whether the mutation the harness applied is the mutation the case names.

A case is PASS only when the applied mutation is faithful AND the observed code equals the
declared one. Anything else is HOLD with the reason recorded; nothing is re-labelled PASS.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_spec as SPEC

W = r"<LOCAL_ROOT>\71_W0_B0-B3_R7_20261127"
OPS = os.path.join(W, "40_OPS")


def run() -> int:
    """Independent re-verification of the mutation receipt (it owns the verdict now).

    This receipt no longer judges: it recomputes, from the SPEC case table and the mutation
    receipt, whether each claimed verdict follows, and reports any case where the receipt's
    verdict and the recomputation disagree. A disagreement is a defect in the receipt.
    """
    spec = SPEC.load("B3")
    cases = SPEC.case_table(spec["text"], "B3")
    neg = json.load(open(os.path.join(OPS, "b3_r7_neg_mutations.json"), encoding="utf-8"))

    rows, disagree = [], []
    for c in neg["cases"]:
        cid = c["case_id"]
        exp, obs = (cases.get(cid) or {}).get("expected"), c.get("observed_first_fail")
        if not c.get("mutation_faithful"):
            recomputed = "HOLD"
        elif obs is None:
            recomputed = "FAIL"
        elif obs == exp:
            recomputed = "PASS"
        else:
            recomputed = "HOLD"
        if recomputed != c["verdict"]:
            disagree.append({"case_id": cid, "receipt": c["verdict"], "recomputed": recomputed})
        rows.append({"case_id": cid, "expected": exp, "observed": obs,
                     "mutation": c.get("mutation"), "mutation_faithful": c.get("mutation_faithful"),
                     "receipt_verdict": c["verdict"], "recomputed_verdict": recomputed,
                     "reason": c.get("reason")})

    counts = {}
    for r in rows:
        counts[r["receipt_verdict"]] = counts.get(r["receipt_verdict"], 0) + 1
    out = {
        "schema": "SST.PH01.W0.B3.NegReconcile@2",
        "verdict_owner": "b3_r7_neg_mutations.json",
        "role": "independent recomputation of the same cases; not a second judgement",
        "spec_b3_sha256": spec["raw_sha256"],
        "cases_verified": len(rows),
        "verdict_counts": counts,
        "disagreements": disagree,
        "cases": rows,
        "claim_ceiling": ("a receipt whose verdict does not survive recomputation from the SPEC "
                          "table and the recorded observed code is defective"),
    }
    p = os.path.join(OPS, "b3_r7_neg_reconcile.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p, "verdict_counts": counts,
                      "disagreements": len(disagree)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
