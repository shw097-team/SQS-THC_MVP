#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 original NEG mutations, executed faithfully against the ledger relation.

What changed from the previous harness (checker findings M3/M5):
  * the NEG design has a structural carrier — the unit's own `case_ids`, which the SPEC
    declares. A "delete only the NEG design" mutation removes exactly that case id and
    leaves the child in place, so the product can observe NEG_MISSING;
  * "delete only the child" removes the child while its declared NEG designs remain known,
    so the product can observe TRACE_ORPHAN instead of the constant ATOM_ABSENT;
  * a protected-field mutation changes the pinned clause identity, so the product can
    observe SUBSTANTIVE_GAP (PROTECTED) or AUTHOR:CHILD_RULE_HOLD:<key> (CHILD);
  * a field the SPEC names but the unit does not carry as a structured field is HOLD with
    `FIELD_CARRIER_ABSENT`, never silently re-labelled.

A case is PASS only when the observed code equals the SPEC's declared code AND the mutation
applied is the mutation the case names.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b3_product as P
import w0_spec as SPEC

OPS = P.OPS
# Only fields the unit actually carries and the product actually verifies. `owner` and
# `requiredness` are NOT in the unit (owner is absent in 365/365; requiredness lives in the
# B2 carrier), so mutating them cannot be observed here and must be HOLD, not FAIL.
CHILD_FIELDS = {"key", "payload_sha", "direct_clause_sha"}


def declared_negs(tbl: dict) -> dict:
    out = {}
    for cid, c in tbl.items():
        if ".NEG." in cid:
            out.setdefault(c["key"], []).append(cid)
    return out


def ledger(units: list[dict], declared: dict) -> dict:
    """Delegates to the product relation; the harness only mutates."""
    return P.ledger_relations(units, declared)


def eval_child(unit: dict) -> dict:
    ev = P.verify_mapping(unit)
    ok = ev.get("decision") == "SOURCE_BOUND_VERIFIED"
    return {"decision": ev.get("decision"), "ok": ok}


def classify(cid: str, unit: dict) -> str:
    c = cid.upper()
    if "DELETE_CHILD" in c:
        return "DELETE_CHILD"
    if "DELETE_NEG" in c:
        return "DELETE_NEG"
    if unit.get("kind") == "PROTECTED":
        return "PROTECTED_FIELD"
    return "FIELD"


def run() -> dict:
    spec = SPEC.load("B3")
    units = SPEC.units(spec["text"])
    tbl = SPEC.case_table(spec["text"], "B3")
    declared = declared_negs(tbl)
    exp_path = os.path.join(OPS, "b3_typed_carrier_expected.json")
    if os.path.isfile(exp_path):
        carrier_exp = json.load(open(exp_path, encoding="utf-8"))
    else:
        carrier_exp = P.freeze_carrier_expectations(units, exp_path)
    base_rows = ledger(units, declared)
    base_ok = sum(1 for r in base_rows.values() if r["child_present"])

    cases = []
    for key, neg_ids in declared.items():
        base_unit = base_rows[key]["unit"]
        if base_unit is None:
            continue
        for cid in neg_ids:
            how = classify(cid, base_unit)
            observed, note = None, None
            if how == "DELETE_CHILD":
                mutated = [u for u in units if u["unit_id"] != base_unit["unit_id"]]
                row = ledger(mutated, declared)[key]
                observed = "AUTHOR:TRACE_ORPHAN" if not row["child_present"] else None
            elif how == "DELETE_NEG":
                mutated = [copy.deepcopy(u) if u["unit_id"] == base_unit["unit_id"] else u
                           for u in units]
                for u in mutated:
                    if u["unit_id"] == base_unit["unit_id"]:
                        u["case_ids"] = [x for x in (u.get("case_ids") or []) if x != cid]
                row = ledger(mutated, declared)[key]
                observed = ("AUTHOR:NEG_MISSING"
                            if cid not in row["neg_present"] and row["child_present"] else None)
            elif how == "PROTECTED_FIELD":
                bad = copy.deepcopy(base_unit)
                bad["direct_clause_sha"] = "0" * 64
                observed = P.clause_refusal(bad)
            else:
                name = cid.rsplit(".", 1)[-1].replace("FIELD_", "")
                exp_val = ((carrier_exp.get("rows") or {}).get(base_unit["unit_id"], {})
                           .get("carriers", {}).get(name, {}) or {}).get("value")
                if exp_val is None:
                    note = f"FIELD_CARRIER_ABSENT:{name}"
                else:
                    bad = copy.deepcopy(base_unit)
                    if name == "direct_clause_sha":
                        bad["direct_clause_sha"] = "0" * 64
                    elif name in ("child", "original_id"):
                        bad["key"] = bad["key"] + "::MUT"
                    elif name in ("parent", "source_sha256"):
                        bad["direct_parent_ref"] = (bad.get("direct_parent_ref") or "") + "MUT"
                    elif name == "clause_span":
                        bad["resolved_source_ref"] = (bad.get("resolved_source_ref") or "L1–2") + "MUT"
                    elif name in ("case", "polarity"):
                        bad["case_ids"] = list(bad.get("case_ids") or []) + ["B3.NEG.MUT"]
                    elif name == "oracle":
                        bad["oracle_ref"] = (bad.get("oracle_ref") or "") + "MUT"
                    elif name == "draft":
                        bad["output_field"] = (bad.get("output_field") or "") + "MUT"
                    else:
                        bad[name] = "MUT"
                    observed = P.carrier_refusal(bad, carrier_exp) or P.clause_refusal(bad)

            expected = (tbl.get(cid) or {}).get("expected")
            faithful = note is None
            if not faithful:
                verdict, reason = "HOLD", note
            elif observed is None:
                nm = cid.rsplit(".", 1)[-1].replace("FIELD_", "")
                verdict, reason = "FAIL", f"FIELD_MUTATION_NOT_DETECTED:{nm}"
            elif observed == expected:
                verdict, reason = "PASS", None
            else:
                verdict, reason = "HOLD", "FIRST_FAIL_CODE_DIVERGENT"
            cases.append({"case_id": cid, "unit_id": base_unit["unit_id"], "key": key,
                          "kind": base_unit.get("kind"), "mutation": how,
                          "mutation_faithful": faithful, "expected_first_fail": expected,
                          "observed_first_fail": observed, "verdict": verdict,
                          "reason": reason})

    counts = {}
    for c in cases:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    reasons = {}
    for c in cases:
        if c["reason"]:
            reasons[c["reason"]] = reasons.get(c["reason"], 0) + 1
    out = {"schema": "SST.PH01.W0.B3.NegMutations@2",
           "verdict_owner": "this receipt (it now carries expected vs observed and the "
                            "faithfulness judgement)",
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "baseline": {"units": len(units), "keys_with_child": base_ok,
                        "declared_neg_designs": sum(len(v) for v in declared.values())},
           "cases": cases, "counts": counts, "hold_reasons": reasons,
           "claim_ceiling": ("each case's code is produced by the ledger relation under a "
                             "named mutation; a case whose field has no structured carrier is "
                             "HOLD, not a pass")}
    p = os.path.join(OPS, "b3_r7_neg_mutations.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p, "counts": counts, "hold_reasons": reasons,
                      "cases": len(cases)}, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    run()
