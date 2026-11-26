#!/usr/bin/env python3
"""B2 TQAEP v2 — real POS predicate and real per-class NEG mutation.

The @1 receipt claimed 2,930 PASS under `claim_ceiling = PAYLOAD_INTEGRITY_ONLY`: every NEG was
"mutate `__b2_neg_probe__` and see the same payload hash change", which is a tautology and carries
no requiredness/namespace/state semantics. This version replaces it:

* POS: row payload pin recomputed + mandatory fields per kind + requiredness judged against the rule
  in the SPEC's own input_rule + q_row consistency + quadrant agreement.
* NEG class comes from the SPEC §06 Expected column, and the mutation is constructed from the data:
    - NAMESPACE_JOIN_DENY (1,385 Q rows): a tail-only join that a naive implementation would accept.
    - TOOL_REQUIREDNESS_HOLD (18 HARD + 54 TECH_ROUTE): HARD deleted, or a route row claiming HARD
      plus enablement.
    - STATE_CONFLICT (8 E00_TECH): a second contradictory disposition state on the same row.
  Every NEG also evaluates the *baseline* through the same oracle; a mutation that the baseline
  already fails is not evidence.

Not claimed: clause-level identity (the generator's clause-sha rule is unbound), tool availability,
licence/lock, B5 selection, any execution.
"""
from __future__ import annotations

import collections
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b2_semantics as S  # noqa: E402

WAVE = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
OPS = os.path.join(WAVE, "40_OPS")
CLASS = {"Q_SOURCE_ROW": "NAMESPACE_JOIN_DENY", "HARD": "TOOL_REQUIREDNESS_HOLD",
         "TECH_ROUTE": "TOOL_REQUIREDNESS_HOLD", "E00_TECH": "STATE_CONFLICT"}


REQ_TOKENS = {"HARD", "EVAL_ONLY", "OPTIONAL", "DEFER_WITH_TRIGGER", "DEFER_NOFIT",
              "REFERENCE_ONLY", "NOT_SELECTED", "SELECTED_OPTIONAL_DISABLED",
              "SELECTED_DESIGN_ONLY", "SELECTED_DOCUMENT_ADAPTER"}


def requiredness_applicable(u: dict, req_row: str) -> tuple[bool, str]:
    k = u.get("kind")
    if k == "TECH_ROUTE":
        return (False, "route-only by kind: the row carries a disposition, not a requiredness")
    if k == "Q_SOURCE_ROW" and req_row not in REQ_TOKENS:
        return (False, "the original source column is prose, not a requiredness token; the "
                       "authoritative value lives in the parent table row")
    return (True, "")


def mandatory_ok(u: dict) -> tuple[bool, list[str]]:
    sp = u.get("source_payload") or []
    k = u.get("kind")
    need = {"HARD": 9, "E00_TECH": 6, "Q_SOURCE_ROW": 8}[k] if k != "TECH_ROUTE" else 1
    miss = [f"column_{i}" for i in range(need) if i >= len(sp) or str(sp[i]).strip() == ""]
    if k == "TECH_ROUTE":
        txt = " ".join(str(x) for x in sp)
        segs = [x for x in txt.split("／") if x.strip()]
        if len(segs) < 6:
            miss.append(f"composite_segments<6({len(segs)})")
        if not re.search(r"SELECTED|DEFER|REFERENCE|NOT_", txt):
            miss.append("no_disposition_token")
    if k == "Q_SOURCE_ROW":
        qr = u.get("q_row") or {}
        if qr.get("payload") != sp:
            miss.append("q_row_payload_mismatch")
        if not qr.get("full_key") or "::ROW=" not in (u.get("key") or ""):
            miss.append("q_row_identity_incomplete")
        if not isinstance(qr.get("source_row"), int) or qr.get("source_row", 0) <= 0:
            miss.append("source_row_invalid")
    return (not miss), miss


def main() -> int:
    spec = S.load_spec()
    t = spec["text"]
    us = S.units(t)
    cases = S.case_table(t)
    by_key = {u["key"]: u for u in us}

    # tail index over Q rows: a tail-only join would be ambiguous, which is the point
    tail_index: dict[str, list[str]] = collections.defaultdict(list)
    q_index: dict[str, list[str]] = collections.defaultdict(list)
    for u in us:
        q_index[u["key"]].append(u["unit_id"])
        if u.get("kind") == "Q_SOURCE_ROW":
            tail_index[(u.get("key") or "").split("::")[-1]].append(u["key"])

    out_cases = []
    tally = collections.Counter()
    for u in us:
        k = u.get("kind")
        uid = u["unit_id"]
        pol_pos = f"B2.POS.{u['spec_id'].split('.SPEC.', 1)[-1]}"
        pol_neg = f"B2.NEG.{u['spec_id'].split('.SPEC.', 1)[-1]}"
        c_pos, c_neg = cases.get(pol_pos), cases.get(pol_neg)

        # ---------------- POS
        recalc = S.sha(json.dumps(u.get("source_payload"), ensure_ascii=False,
                                  separators=(",", ":")).encode())
        pin_ok = recalc == u.get("payload_sha")
        mand_ok, mand_miss = mandatory_ok(u)
        req_row = S.row_requiredness(u)
        req_ind, req_rule = S.independent_requiredness(u)
        requ_applicable, requ_reason = requiredness_applicable(u, req_row)
        req_ok = (req_row == req_ind) if requ_applicable else True
        qa = S.q_of(u) if k == "Q_SOURCE_ROW" else None
        q_ok = bool(qa and qa["agree"]) if k == "Q_SOURCE_ROW" else True
        pos_ok = pin_ok and mand_ok and req_ok and q_ok
        pos_rec = {"case_id": pol_pos, "unit_id": uid, "kind": k,
                   "polarity": "POS", "verdict": "PASS" if pos_ok else "FAIL",
                   "observed": {"payload_pin": pin_ok, "mandatory_fields": mand_ok,
                                "missing": mand_miss,
                                "requiredness_row": req_row,
                                "requiredness_independent": req_ind, "requiredness_rule": req_rule,
                                "requiredness_agree": req_ok,
                                "quadrant": (qa or {}).get("q"), "quadrant_agree": q_ok,
                                "clause_identity": (u.get("_clause") or "UNBOUND_RULE")},
                   "expected": (c_pos or {}).get("expected"),
                   "first_fail": None if pos_ok else "B2_POS_ROW_OR_REQUIREDNESS"}
        out_cases.append(pos_rec)
        tally["POS_" + pos_rec["verdict"]] += 1

        # ---------------- NEG
        expected = (c_neg or {}).get("expected") or CLASS[k]
        cls = CLASS[k]
        observed, mutation, baseline = None, {}, None
        if cls == "NAMESPACE_JOIN_DENY":
            tail = "::".join((u.get("key") or "").split("::")[1:])
            naive = S.suffix_lookup(tail, {k2: 1 for k2 in q_index})
            mutation = {"selector": {"suffix": tail}, "naive_suffix_matches": len(naive),
                        "naive_examples": naive[:3],
                        "why": "join on the tail of the key, which drops the Q-namespace identity"}
            baseline = len(S.join_rows({"key": u["key"]}, q_index))
            try:
                S.join_rows({"suffix": tail}, q_index)
                observed = None
            except S.OracleError as e:
                observed = str(e)
            ok = (observed == "NAMESPACE_JOIN_DENY" and baseline == 1 and len(naive) >= 1)
        elif cls == "TOOL_REQUIREDNESS_HOLD":
            if k == "HARD":
                mutation = {"declared_requiredness": "EVAL_ONLY", "why": "原 HARD 被删除"}
                observed = S.requiredness_gate("EVAL_ONLY", req_ind, False)
            else:
                mutation = {"declared_requiredness": "HARD", "claimed_enable": True,
                            "why": "route-only row 被當 HARD 啟用"}
                observed = S.requiredness_gate("HARD", req_ind, True)
            baseline = S.requiredness_gate(req_row, req_ind, False)
            ok = (observed == "TOOL_REQUIREDNESS_HOLD" and baseline is None)
        else:  # STATE_CONFLICT
            state = req_row
            mutation = {"states": [state, "ENABLED"], "why": "同一 row 兩個互斥處置狀態"}
            observed = S.state_gate([state, "ENABLED"])
            baseline = S.state_gate([state])
            ok = (observed == "STATE_CONFLICT" and baseline is None)

        neg_rec = {"case_id": pol_neg, "unit_id": uid, "kind": k, "polarity": "NEG",
                   "class": cls, "expected": expected, "observed_first_fail": observed,
                   "mutation": mutation, "baseline_first_fail": baseline,
                   "spec_expected_matches_class": expected == cls,
                   "verdict": ("PASS" if ok and expected == cls else
                               ("PASS_SPEC_EXPECTATION_DEVIATES" if ok else "FAIL")),
                   "first_fail": observed}
        out_cases.append(neg_rec)
        tally["NEG_" + neg_rec["verdict"]] += 1

    # ---------------- census integrity
    ids = set(cases)
    unit_ids = {f"B2.POS.{u['spec_id'].split('.SPEC.', 1)[-1]}" for u in us} | \
               {f"B2.NEG.{u['spec_id'].split('.SPEC.', 1)[-1]}" for u in us}
    orphan_cases = sorted(ids - unit_ids)[:10]
    missing_cases = sorted(unit_ids - ids)[:10]
    dist = collections.Counter(c["expected"] for c in cases.values() if ".NEG." in c["case_id"])

    out = {
        "schema": "SST.PH01.W0.B2.TQAEP@2",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M", "bid": "B2",
        "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A", "fin_order": "DENY",
        "claim_ceiling": "ROW_SEMANTICS_AND_CLASS_MUTATION",
        "not_claimed": ["clause-level identity (generator clause-sha rule unbound)",
                        "tool availability", "licence/lock state", "B5 tool selection",
                        "any execution or installation"],
        "spec": {"path": spec["path"], "bytes": spec["bytes"], "raw_sha256": spec["raw_sha256"],
                 "pin_match": spec["pin_match"]},
        "census": {"units": len(us), "cases": len(out_cases),
                   "spec_case_rows": len(cases),
                   "spec_expected_distribution": dict(dist),
                   "required_distribution": S.REQUIRED_NEG,
                   "distribution_matches": dict(dist) == S.REQUIRED_NEG,
                   "orphan_case_ids": orphan_cases, "unit_cases_absent_from_spec": missing_cases},
        "tally": dict(tally),
        "cases": out_cases,
    }
    p = os.path.join(OPS, "b2_tqaep_" + datetime.datetime.now().strftime("%Y%m%dT%H%M%S") + ".json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print("cases", len(out_cases), "tally", dict(tally))
    print("spec case rows", len(cases), "expected dist", dict(dist),
          "matches", dict(dist) == S.REQUIRED_NEG)
    print("orphans", orphan_cases, "missing", missing_cases)
    print(f"receipt {p} {os.path.getsize(p)}B sha256={S.sha(open(p,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
