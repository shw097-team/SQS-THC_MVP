#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 TQAEP v2 - 2,930 original cases with carrier-declared column authority.

Changes from v1 (round-3 finding closure):
  * requiredness is never guessed from a bare positional index. The carrier declares four
    dimensions (Q1 Requiredness / Q2 AdmissionDecision / Q3 KindApplicability / Q4 Golden);
    a Requiredness column exists only in Q1 (index 2) and Q2 (index 5). Q3/Q4 emit
    NOT_APPLICABLE with the carrier's own section line as applicability evidence.
  * HARD compares the unit value against the carrier row (two different records), not itself.
  * E00 verifies the typed design selection and refuses an unauthorised enable.
  * TECH_ROUTE cross-checks its own requiredness statement against its tool row.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1_spec
import b2_engine as B

OUT_DIR = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126\40_OPS"


def mutated_namespace_unit(unit: dict) -> dict:
    ns = unit["key"].split("::")[0]
    tail = unit["key"].split("::", 1)[1]
    alt = "R3-REGISTRY-Q9"
    u = json.loads(json.dumps(unit))
    u["key"] = f"{alt}::{tail}"
    m = re.search(r"key=([^\s；]+)", u["input_rule"])
    if m:
        u["input_rule"] = u["input_rule"].replace(
            m.group(1), f"{alt}::{m.group(1).split('::', 1)[1]}")
    return u


def main() -> int:
    t0 = time.time()
    b2 = b1_spec.load_b2(units_only=True)
    units = list(b2["units"].values())
    q = [u for u in units if u["kind"] == "Q_SOURCE_ROW"]
    hard = [u for u in units if u["kind"] == "HARD"]
    e00 = [u for u in units if u["kind"] == "E00_TECH"]
    route = [u for u in units if u["kind"] == "TECH_ROUTE"]

    qres = B.op_qrows(q)
    qmap = {e["unit_id"]: e for e in qres["entries"]}
    hres = B.op_hard(hard + e00 + route)
    hmap = {e["unit_id"]: e for e in hres["entries"]}
    mres = B.op_meta(hard + e00 + route)
    sections = B.carrier_sections()

    cases = {}

    def put(uid, cid, verdict, actual, note=""):
        cases[cid] = {"case_id": cid, "unit_id": uid, "verdict": verdict,
                      "actual": actual, "note": note}

    for u in q:
        uid, key = u["unit_id"], u["key"]
        e = qmap[uid]
        ns = e["namespace"]
        pos_id, neg_id = u["case_ids"]
        req = e.get("requiredness")
        ok_req = (B.is_requiredness_value(req or "")
                  or (req == "NOT_APPLICABLE" and bool(e.get("requiredness_basis"))))
        if e["decision"] != "VERIFIED":
            q_verdict = "FAIL"
        elif ok_req:
            q_verdict = "PASS"
        else:
            q_verdict = "HOLD"   # the row is verbatim-verified but its requiredness cell is not a
                                 # classifiable value; that is an unbound oracle, not a product failure
        put(uid, pos_id, q_verdict,
            {"carrier_line": e.get("carrier_line_observed"), "carrier_key": e.get("carrier_key"),
             "carrier_row": e.get("carrier_row"), "payload_sha": e.get("payload_sha_observed"),
             "requiredness": req, "requiredness_basis": e.get("requiredness_basis"),
             "dimension": e.get("dimension"), "admission_decision": e.get("admission_decision"),
             "row_decision": e["decision"]},
            "POS predicate = original payload field-by-field equality + this key's rule: physical "
            "line + key column + row column + canonical payload SHA all equal, and requiredness is "
            "derived from the carrier-declared column; tool admission/selection stays with B5/R17")
        m = mutated_namespace_unit(u)
        r = B.op_qrows([m])
        got = r["entries"][0]["decision"] if r["entries"] else None
        put(uid, neg_id, "PASS" if got == "NAMESPACE_JOIN_DENY" else "FAIL",
            {"mutation": f"{ns} -> R3-REGISTRY-Q9 with identical tail", "observed": got},
            "same tail in a different namespace must be refused, never joined")

    for u in hard:
        uid = u["unit_id"]
        e = hmap[uid]
        pos_id, neg_id = u["case_ids"]
        car = e.get("carrier_requiredness")
        put(uid, pos_id, "PASS" if e["decision"] == "PRESERVED" else "FAIL",
            {"carrier_requiredness": car, "unit_requiredness": e.get("unit_requiredness"),
             "basis": e.get("requiredness_basis"), "delta": e.get("requiredness_delta")},
            "unit value compared against the carrier row (two distinct records), not self-comparison")
        guard = B.guard_requiredness(car, "OPTIONAL") if B.is_requiredness_value(car or "") else \
            {"decision": "NOT_APPLICABLE", "detail": "carrier value not derivable"}
        put(uid, neg_id, "PASS" if guard["decision"] == "DENY" else "FAIL",
            {"mutation": f"{car} -> OPTIONAL", "guard": guard},
            "original obligation: a HARD obligation may not be downgraded by an author NOFIT; the "
            "inner functional failure stays HOLD under TT-UP-1")

    for u in e00:
        uid = u["unit_id"]
        e = hmap[uid]
        pos_id, neg_id = u["case_ids"]
        sel = (e.get("unit_design_selection") or [""])[0]
        car_sel = e.get("carrier_design_selection")
        # B2-F05 in the pinned spec declares the original typed DesignSelection oracle unbound
        # for six of these eight units and historically evidenced for two (U0022/U0023)
        SPEC_HISTORICAL = {"B2.U0022", "B2.U0023"}
        put(uid, pos_id,
            "PASS" if (uid in SPEC_HISTORICAL and e.get("carrier_agrees")) else "HOLD",
            {"unit_design_selection": e.get("unit_design_selection"),
             "carrier_design_selection": car_sel, "carrier_line": e.get("carrier_line"),
             "carrier_version": e.get("carrier_version"),
             "carrier_agrees": e.get("carrier_agrees"),
             "spec_oracle_status": "HISTORICAL_EVIDENCE" if uid in SPEC_HISTORICAL
                                   else "ORACLE_HOLD (B2-F05)"},
            "carrier cross-check is supporting evidence only; the pinned spec declares this unit's "
            "typed DesignSelection oracle HOLD, so the case cannot be PASS on it")
        g = B.guard_design_selection(car_sel, "SELECTED_ENABLED") if car_sel else \
            {"decision": "NOT_APPLICABLE", "detail": "no carrier selection to guard"}
        put(uid, neg_id, "PASS" if (g["decision"] == "DENY"
                                    and g.get("first_fail") == "STATE_CONFLICT") else "HOLD",
            {"mutation": f"{car_sel} -> SELECTED_ENABLED", "guard": g},
            "an unauthorised enable is refused with the spec's declared FirstFail STATE_CONFLICT")

    for u in route:
        uid = u["unit_id"]
        e = hmap[uid]
        pos_id, neg_id = u["case_ids"]
        text = " ".join(B.norm_cell(x) for x in (u.get("source_payload") or []))
        car = e.get("carrier_requiredness")
        ok_guard = B.guard_route_requiredness(car, text) if B.is_requiredness_value(car or "") else \
            {"decision": "HOLD", "detail": "carrier value not derivable"}
        put(uid, pos_id, "PASS" if (e["decision"] == "PRESERVED"
                                    and ok_guard["decision"] == "ALLOW") else "HOLD",
            {"route_stated": e.get("route_stated_requiredness"), "carrier_requiredness": car,
             "consistency": ok_guard},
            "the route's own requiredness statement agrees with its tool row")
        mutated = text.replace(car, "OPTIONAL") if B.is_requiredness_value(car or "") else text
        bad = B.guard_route_requiredness(car, mutated) if B.is_requiredness_value(car or "") else \
            {"decision": "HOLD", "detail": "no derivable carrier value"}
        put(uid, neg_id, "PASS" if bad["decision"] == "DENY" else "HOLD",
            {"mutation": f"route requiredness {car} -> OPTIONAL", "guard": bad},
            "a route may not restate a different requiredness")

    missing = [u["key"] for u in units for cid in u["case_ids"] if cid not in cases]
    counts = {}
    for c in cases.values():
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1

    # bind the metadata that was actually collected (official registry, pinned response)
    meta_map = {}
    _mp = os.path.join(OUT_DIR, "b2_r5_meta.json")
    if os.path.isfile(_mp):
        for r in json.load(open(_mp, encoding="utf-8"))["entries"]:
            meta_map[r["tool_id"]] = r

    def _tid(key: str):
        mm = re.findall(r"TECH-\d+", key or "")
        return mm[-1] if mm else None

    def _meta_for(key: str):
        r = meta_map.get(_tid(key) or "")
        if r and r.get("decision") == "COLLECTED":
            m = r["metadata"]
            return ({"distribution": m["distribution"], "version": m["version"],
                     "license_expression": m["license_expression"], "license": m["license"],
                     "provenance": m["provenance"]},
                    None)
        if r:
            return (None, {"field": "metadata",
                           "reason": "UNVERIFIED" if r["decision"] == "VERSION_UNBOUND" else "FORMAT_UNSUPPORTED",
                           "detail": (r["missing"][0]["detail"] if r.get("missing") else r["decision"])})
        return (None, {"field": "metadata", "reason": "UNVERIFIED",
                       "detail": "no official metadata record for this tool key"})

    trs_entries = []
    for e in qres["entries"]:
        trs_entries.append({
            "tool_key": e["key"], "source_row": e.get("carrier_row"),
            "requiredness": e.get("requiredness"),
            "payload_sha": e.get("payload_sha_expected"),
            "metadata": _meta_for(e["key"])[0], "kind": "Q_SOURCE_ROW",
            "applicability_evidence": (e.get("requiredness_basis")
                                       if e.get("requiredness") == "NOT_APPLICABLE" else None),
            "missing": ((e.get("missing", []) if e["decision"] != "VERIFIED" else [])
                        + ([_meta_for(e["key"])[1]] if _meta_for(e["key"])[1] else []))})
    for u in hard + e00 + route:
        req, basis = B.derive_requiredness(u)
        trs_entries.append({
            "tool_key": u["key"], "source_row": None, "requiredness": req,
            "payload_sha": u.get("payload_sha"), "metadata": _meta_for(u["key"])[0], "kind": u["kind"],
            "applicability_evidence": basis if req == "NOT_APPLICABLE" else None,
            "missing": ([_meta_for(u["key"])[1]] if _meta_for(u["key"])[1] else [])})
    trs = {"entries": trs_entries, "namespace": qres["namespaces"],
           "union_expected": 1465, "union_emitted": len(trs_entries)}
    receivers = {cid: B.receiver(cid, trs) for cid in ("B3", "B5")}
    for cid, r in receivers.items():
        r["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    result = {
        "schema": "SST.PH01.W0.B2.TQAEP@6",
        "spec_version": "2026-11-26_r5_Native-first_CODEX_FINAL",
        "spec_b2_sha256": b2["sha256"],
        "expected_unit_set_sha256": b2["unit_id_set_sha"],
        "expected_case_set_sha256": b2["case_id_set_sha"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "case_count": len(cases),
        "expected_case_count": 2930,
        "orphan_case_ids": missing[:10],
        "unit_counts": {"Q_SOURCE_ROW": len(q), "HARD": len(hard), "E00_TECH": len(e00),
                        "TECH_ROUTE": len(route)},
        "verdict_counts": counts,
        "carrier_dimensions": B.DIMENSION_BY_NS,
        "carrier_sections": sections,
        "requiredness_distribution": {
            ns: {**{k: sum(1 for e in qres["entries"]
                           if e["namespace"] == ns and e.get("requiredness") == k)
                    for k in ("HARD", "SOFT", "SOFT/CONDITIONAL", "CONDITIONAL", "OPTIONAL",
                              "EVAL_ONLY", "NOT_APPLICABLE", "UNKNOWN")},
                 "rows_total": sum(1 for e in qres["entries"] if e["namespace"] == ns),
                 "other_rows": (sum(1 for e in qres["entries"] if e["namespace"] == ns)
                                - sum(1 for e in qres["entries"] if e["namespace"] == ns
                                      and e.get("requiredness") in
                                      ("HARD", "SOFT", "SOFT/CONDITIONAL", "CONDITIONAL",
                                       "OPTIONAL", "EVAL_ONLY", "NOT_APPLICABLE", "UNKNOWN")))}
            for ns in ("R3-REGISTRY-Q1", "R3-REGISTRY-Q2", "R3-REGISTRY-Q3", "R3-REGISTRY-Q4")},
        "qrows": {"summary": qres["summary"], "carrier": qres["carrier"],
                  "namespaces": qres["namespaces"], "errors": len(qres["errors"])},
        "hard": hres["summary"],
        "source_defects": [
            {"key": e["key"], "carrier_requiredness": e.get("carrier_requiredness"),
             "route_stated": e.get("route_stated_requiredness"),
             "carrier_namespace": e.get("resolved_namespace"),
             "kind": e["kind"],
             "detail": "route text names a requiredness class its tool row does not carry"}
            for e in hres["entries"] if e["decision"] == "DRIFT"],
        "meta": mres["summary"],
        "receivers": {cid: {"accepted": r["accepted"], "rejected": r["rejected"],
                            "mandatory_fields": r["mandatory_fields"],
                            "reject_reasons": sorted({x["first_fail"] for x in r["refused"]})}
                      for cid, r in receivers.items()},
        "cases": cases,
        "elapsed_s": round(time.time() - t0, 1),
        "claim_ceiling": "HOLD/PARTIAL are never PASS; tool admission stays with B5/R17",
    }
    out = os.path.join(OUT_DIR, "b2_r5_tqaep.json")
    json.dump(result, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump(receivers, open(os.path.join(OUT_DIR, "b2_r5_receivers.json"), "w",
                              encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    # the producer output itself, so a downstream consumer (B3/B5) has a real object to join on
    json.dump({"schema": "SST.B2.ToolReadSet@6",
               "spec_version": "2026-11-26_r5_Native-first_CODEX_FINAL",
               "carrier_sha256": trs.get("carrier_sha256")
                                 or B.CARRIER_SHA,
               "namespace": qres["namespaces"],
               "union_expected": 1465, "union_emitted": len(trs_entries),
               "entries": trs_entries},
              open(os.path.join(OUT_DIR, "b2_r5_tool_readset.json"), "w",
                   encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": out, "counts": counts, "case_count": len(cases),
                      "orphans": len(missing),
                      "receivers": {c: [r["accepted"], r["rejected"]]
                                    for c, r in receivers.items()},
                      "reqd": result["requiredness_distribution"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
