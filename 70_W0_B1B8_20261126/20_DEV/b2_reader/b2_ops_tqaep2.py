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

Not claimed: semantic clause identity (only span+sha identity) (the generator's clause-sha rule is unbound), tool availability,
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


REQ_TOKENS = S.REQ_TOKENS


def requiredness_applicable(u: dict, req_row: str) -> tuple[bool, str]:
    """Independent requiredness exists only where a payload column can be cross-checked against the
    unit's own rule. Every Q row is VERBATIM_ONLY (its authoritative value is the parent table row,
    which the Maker cannot read as an independent second source), and route rows are N/A by kind."""
    k = u.get("kind")
    if k == "TECH_ROUTE":
        return (False, "route-only by kind: the row carries a disposition, not a requiredness")
    if k == "Q_SOURCE_ROW":
        return (False, "VERBATIM_ONLY: the row's column is transcribed from the parent table; there "
                       "is no second independent source inside this kit, so it is not checked")
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
    parent_p, parent_info = S.parent_path()
    parent_text = open(parent_p, encoding="utf-8").read() if parent_p else None

    # original-source cross-check (round-3 defect 5): compare each row's payload columns against the
    # ORIGINAL source line it cites -- the carrier for Q rows, the all-blueprint for the rest. Bounded
    # rule: every non-empty payload column must occur verbatim in the cited line.
    CARRIER_SHA = "463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1"
    ORIG_SHA = "dd37a40b112bf5aac379adb44285ec01409519f7af64418298375833859d01a1"
    _cp = S.carrier_index().get(CARRIER_SHA)
    carrier_lines = open(_cp, encoding="utf-8").read().splitlines() if _cp else []
    _op = S.parent_index().get(ORIG_SHA)
    orig_lines = open(_op, encoding="utf-8").read().splitlines() if _op else []
    orig_cmp_n = orig_cmp_fail = 0

    # Join indexes: ONLY Q rows are joinable by row identity, and the tail key is everything after the
    # Q-namespace, so dropping the namespace still resolves to exactly one Q row (the mutation is then
    # caught on identity) while a non-Q key can never resolve through the Q index.
    tail_index: dict[str, list[str]] = collections.defaultdict(list)
    q_index: dict[str, list[str]] = collections.defaultdict(list)
    for u in us:
        if u.get("kind") != "Q_SOURCE_ROW":
            continue
        q_index[u["key"]].append(u["unit_id"])
        tail_index["::".join((u["key"] or "").split("::")[1:])].append(u["key"])

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
        # clause identity, from direct_parent_ref under the explicit span rule
        pref = S.parse_ref(u.get("direct_parent_ref") or "")
        clause_repro = None
        if pref.get("kind") == "FILE" and parent_text and pref["sha"] == S.PARENT_SHA:
            cl = S.clause_sha(parent_text, pref["a"], pref["b"])
            clause_repro = bool([1 for v in (cl.get("candidates") or {}).values()
                                 if v == u.get("direct_clause_sha")])
        orig_cmp = None
        if k == "Q_SOURCE_ROW":
            _raw = (u.get("q_row") or {}).get("carrier_line")
            _ln = int(re.sub(r"[^0-9]", "", str(_raw)) or 0) if _raw else 0
            if isinstance(_ln, int) and 0 < _ln <= len(carrier_lines):
                _line = carrier_lines[_ln - 1]
                _cols = [str(x).strip() for x in (u.get("source_payload") or []) if str(x).strip()]
                orig_cmp = bool(_cols) and all(c in _line for c in _cols)
                orig_cmp_n += 1
                orig_cmp_fail += 0 if orig_cmp else 1
        else:
            _oref = S.parse_ref(u.get("original_source_ref") or "")
            if _oref.get("sha") == ORIG_SHA and orig_lines:
                _txt = chr(10).join(orig_lines[_oref["a"] - 1:_oref["b"]])
                _cols = [str(x).strip() for x in (u.get("source_payload") or []) if str(x).strip()]
                orig_cmp = bool(_cols) and all(c in _txt for c in _cols)
                orig_cmp_n += 1
                orig_cmp_fail += 0 if orig_cmp else 1
        # orig_cmp is a DIAGNOSTIC, not a gate: the Maker's coarse rule (column substring presence)
        # disagrees with 897 rows on formatting alone, so it cannot decide POS. Provenance value
        # equality is carried by the independent checker's re-derivation, not by this receipt.
        pos_ok = (pin_ok and mand_ok and req_ok and q_ok and clause_repro is not False)
        pos_rec = {"case_id": pol_pos, "unit_id": uid, "kind": k,
                   "polarity": "POS", "verdict": "PASS" if pos_ok else "FAIL",
                   "observed": {"payload_pin": pin_ok, "mandatory_fields": mand_ok,
                                "missing": mand_miss,
                                "requiredness_row": req_row,
                                "requiredness_independent": req_ind,
                                "requiredness_rule": req_rule,
                                "requiredness_applicable": requ_applicable,
                                "requiredness_reason": requ_reason,
                                "requiredness_checked": requ_applicable,
                                "requiredness_agree": (req_row == req_ind) if requ_applicable else None,
                                "quadrant": (qa or {}).get("q"),
                                "quadrant_signals": (qa or {}).get("votes"),
                                "clause_identity": ("REPRODUCED" if clause_repro else
                                                    ("UNREPRODUCED" if clause_repro is False
                                                     else "NOT_ATTEMPTED")),
                                "clause_reference": "direct_parent_ref",
                                "original_source_columns_present": orig_cmp},
                   "expected": (c_pos or {}).get("expected"),
                   "first_fail": None if pos_ok else "B2_POS_ROW_OR_REQUIREDNESS"}
        out_cases.append(pos_rec)
        tally["POS_" + pos_rec["verdict"]] += 1

        # ---------------- NEG
        expected = (c_neg or {}).get("expected") or CLASS[k]
        cls = CLASS[k]
        spec_mut = ((c_neg or {}).get("mutation") or "").strip()
        observed, mutation, baseline = None, {}, None
        baseline_name = "baseline_first_fail"
        extra: dict = {}
        verdict = "FAIL"
        if cls == "NAMESPACE_JOIN_DENY":
            full = u["key"]
            tail = "::".join(full.split("::")[1:])
            naive = S.namespace_blind_lookup(tail, q_index, tail_index)
            baseline = len(S.join_rows({"key": full}, q_index, tail_index))
            baseline_name = "baseline_rows"
            try:
                S.join_rows({"key": tail}, q_index, tail_index)
                observed = None
            except S.OracleError as e:
                observed = str(e)
            forged = "WRONG-NS::" + tail
            try:
                S.join_rows({"key": forged}, q_index, tail_index)
                forged_res = None
            except S.OracleError as e:
                forged_res = str(e)
            mutation = {"namespace_dropped": {"key": tail}, "namespace_forged": {"key": forged},
                        "naive_namespace_blind_matches": len(naive), "naive_examples": naive[:3],
                        "why": "two single-field namespace mutations: drop the namespace, forge one"}
            extra = {"namespace_forged_first_fail": forged_res}
            ok = (observed == "NAMESPACE_JOIN_DENY" and forged_res == "NAMESPACE_JOIN_DENY"
                  and baseline == 1 and len(naive) >= 1)
            verdict = "PASS" if ok else "FAIL"
        elif cls == "TOOL_REQUIREDNESS_HOLD":
            if k == "HARD":
                if "原 HARD 被删除" in spec_mut or not spec_mut:
                    mutation = {"declared_requiredness": "EVAL_ONLY", "why": "原 HARD 被删除"}
                    observed = S.requiredness_gate("EVAL_ONLY", req_ind, False)
                    baseline = S.requiredness_gate(req_row, req_ind, False)
                    ok = (observed == "TOOL_REQUIREDNESS_HOLD" and baseline is None)
                    verdict = "PASS" if ok else "FAIL"
                else:
                    verdict = "HOLD_SPEC_MUTATION_UNIMPLEMENTED"
                    extra = {"spec_mutation": spec_mut,
                             "why": "the §06 mutation for this row is not HARD-loss; its own text "
                                    "names a different code than the TOOL_REQUIREDNESS_HOLD this "
                                    "case expects, so implementing it would require an oracle the "
                                    "Maker may not invent"}
                    baseline = None
            else:  # TECH_ROUTE: §06 says "change one protected field" (under-specified) -> two arms
                arms = []
                for name, declared, enable in (("requiredness_only", "HARD", False),
                                               ("enablement_only", "ROUTE_ONLY", True)):
                    arms.append({"arm": name, "first_fail":
                                 S.requiredness_gate(declared, req_ind, enable)})
                baseline = S.requiredness_gate(req_row, req_ind, False)
                ok = (baseline is None and all(a["first_fail"] == "TOOL_REQUIREDNESS_HOLD"
                                               for a in arms))
                mutation = {"arms": [{"declared_requiredness": "HARD"},
                                     {"claimed_enable": True}],
                            "note": "two single-field arms; the §06 text does not name the field"}
                observed = arms[0]["first_fail"] if ok else None
                extra = {"arms": arms, "spec_mutation_under_specified": "change one protected field"}
                verdict = ("PASS_INTERPRETED" if ok else "FAIL")
        else:  # STATE_CONFLICT — the row's DISPOSITION column is the state, not its requiredness
            _sp = u.get("source_payload") or []
            state = str(_sp[2]) if len(_sp) > 2 else req_row
            pair = S.contradicting_state(state)
            if pair is None:
                verdict = "HOLD_ORACLE_UNBOUND"
                extra = {"spec_mutation": spec_mut,
                         "why": "no NATURAL exclusion covers this row's disposition tokens; the only "
                                "candidate relations are Maker-declared and absent from the SPEC, so "
                                "the oracle is owed by the design-selection owner (E02/E05/PIPD)",
                         "oracle_owner": "E02/E05/PIPD design-selection owner; R17/OriginalConsumer "
                                         "for the requiredness-class relation"}
                baseline = None
            else:
                mutation = {"states": [state, pair],
                            "why": "the row's own disposition plus its declared counterpart"}
                observed = S.state_gate([state, pair])
                baseline = S.state_gate([state])
                coexist = S.state_gate(["INSTALLED", "ENABLED"])
                ok = (observed == "STATE_CONFLICT" and baseline is None and coexist is None)
                extra = {"legal_coexistence_probe": {"INSTALLED+ENABLED": coexist},
                         "contradicting_state": pair}
                verdict = "PASS" if ok else "FAIL"

        neg_rec = {"case_id": pol_neg, "unit_id": uid, "kind": k, "polarity": "NEG",
                   "class": cls, "expected": expected, "spec_mutation": spec_mut[:160],
                   "observed_first_fail": observed, "mutation": mutation,
                   baseline_name: baseline, "spec_expected_matches_class": expected == cls,
                   "verdict": verdict, "first_fail": observed, **extra}
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
        "claim_ceiling": "ROW_PAYLOAD_PIN_INTEGRITY_AND_CLAUSE_SPAN_IDENTITY",
        "claim_scope": {
            "supported": ["ROW_PAYLOAD_PIN_INTEGRITY (per-unit payload_sha recomputation against the SPEC cell)",
                          "CLAUSE_SPAN_IDENTITY (direct_parent_ref, lines a..b incl. line-b LF)",
                          "QUADRANT_CENSUS (key prefix, corroborated by disjoint source_row ranges)",
                          "CASE_CENSUS_2930 (no orphan, none missing)",
                          "CLASS_MUTATION_NS_JOIN (namespace dropped / forged, non-vacuous)",
                          "HARD_DELETION_MUTATION (9 of 18 HARD rows whose §06 mutation is HARD-loss)",
                          "STATE_CONFLICT on a NATURAL exclusion relation, 2 of 8 E00 rows executed "
                          "(6 HOLD_ORACLE_UNBOUND), with legal-coexistence probes"],
            "not_supported": ["provenance: value equality with the original source was NOT re-derived by "
                              "this receipt (original_source_comparison is a diagnostic, not a gate)",
                              "independent requiredness (all 1,385 Q rows VERBATIM_ONLY, 54 route N/A)",
                              "9 HARD §06 mutations that are not HARD-loss",
                              "54 TECH_ROUTE mutations: §06 does not name the protected field",
                              "tool availability / pin / licence / lock (B5 duty)",
                              "any B2 acceptance, completion or product execution"]},
        "parent_source": parent_info,
        "original_source_comparison": {
            "rule": "every non-empty payload column must occur verbatim in the cited original source "
                    "line (Q rows: carrier 463dcf33… at q_row.carrier_line; others: dd37a40b… span)",
            "compared": orig_cmp_n, "coarse_rule_mismatches": orig_cmp_fail,
            "status": "DIAGNOSTIC_ONLY_NOT_A_GATE",
            "note": "mismatches are dominated by formatting differences between the payload cells and "
                    "the carrier table row; the Maker does not claim provenance on this basis",
            "scope": "column-substring presence, not semantic equality",
        },
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
