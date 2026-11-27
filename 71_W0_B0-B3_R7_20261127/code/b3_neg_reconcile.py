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


def faithfulness(case: dict, mutation_applied: str, unit: dict) -> tuple[bool, str]:
    declared = (case.get("mutation") or "").strip()
    if mutation_applied == "DELETE_CHILD":
        # the declared mutation keeps the NEG design; the harness removes the whole unit,
        # so the NEG carrier disappears with it and TRACE_ORPHAN is unobservable
        return False, "MUTATION_DELETES_NEG_CARRIER_WITH_UNIT"
    if mutation_applied == "DELETE_NEG":
        # the harness appends a '::DELETED' clone instead of removing the NEG design
        return False, "MUTATION_NOT_DECLARED_SHAPE"
    if mutation_applied == "PROTECTED_FIELD":
        # declared shape is "change one protected field"; direct_clause_sha is one
        return True, "DECLARED_SHAPE"
    if mutation_applied == "GENERIC_REMOVE":
        m = re.search(r"change only field (\S+)", declared)
        if m and m.group(1) not in ("direct_clause_sha",):
            return False, f"MUTATION_APPLIED_TO_WRONG_FIELD:{m.group(1)}"
        return True, "DECLARED_SHAPE"
    return False, "MUTATION_UNCLASSIFIED"


def run() -> int:
    spec = SPEC.load("B3")
    cases = SPEC.case_table(spec["text"], "B3")
    units = {u["unit_id"]: u for u in SPEC.units(spec["text"])}
    neg = json.load(open(os.path.join(OPS, "b3_r7_neg_mutations.json"), encoding="utf-8"))

    rows = []
    for c in neg["cases"]:
        cid = c["case_id"]
        sc = cases.get(cid) or {}
        unit = units.get(c.get("unit_id"), {})
        faithful, why = faithfulness(sc, c.get("mutation", ""), unit)
        expected, observed = sc.get("expected"), c.get("first_fail")
        if faithful and expected == observed:
            verdict, reason = "PASS", None
        elif not faithful:
            verdict, reason = "HOLD", f"MUTATION_NOT_FAITHFUL:{why}"
        else:
            verdict, reason = "HOLD", "FIRST_FAIL_CODE_DIVERGENT"
        rows.append({"case_id": cid, "unit_id": c.get("unit_id"), "kind": c.get("kind"),
                     "mutation_applied": c.get("mutation"),
                     "mutation_declared": sc.get("mutation"),
                     "expected_first_fail": expected, "observed_first_fail": observed,
                     "refusal_executed": bool(c.get("refused")),
                     "mutation_faithful": faithful, "faithfulness_basis": why,
                     "verdict": verdict, "reason": reason,
                     "case_in_spec": bool(sc)})

    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    reason_counts = {}
    for r in rows:
        if r["reason"]:
            reason_counts[r["reason"]] = reason_counts.get(r["reason"], 0) + 1
    out = {
        "schema": "SST.PH01.W0.B3.NegReconcile@1",
        "spec_b3_sha256": spec["raw_sha256"],
        "cases_executed": len(rows),
        "expected_case_count": 44,
        "verdict_counts": counts,
        "hold_reasons": reason_counts,
        "code_divergence": [{"case_id": r["case_id"], "expected": r["expected_first_fail"],
                             "observed": r["observed_first_fail"]}
                            for r in rows if r["reason"] == "FIRST_FAIL_CODE_DIVERGENT"],
        "claim_ceiling": ("a refusal that fired is not a NEG PASS unless the SPEC's declared "
                          "FirstFail is the code the product returned and the mutation applied "
                          "is the mutation the case names"),
        "cases": rows,
    }
    p = os.path.join(OPS, "b3_r7_neg_reconcile.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p, "verdict_counts": counts, "hold_reasons": reason_counts},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
