#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B1 TQAEP runner — executes the 60 original cases of the pinned r5 spec.

Rules applied (from the spec, not from convenience):
  * POS is only PASS when the product really read an identity for every declared
    target of that key, or when the refusal/absence is *recorded*, never fabricated.
  * NEG is only PASS when the product really refuses with the original FirstFail
    for the original single-variable mutation. An unbound oracle stays HOLD, it is
    never re-labelled PASS and never re-labelled N/A.
  * FIXTURE_ONLY results are kept in their own bucket; they are NOT original
    semantic PASS and do not close D-3.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1_engine as E
import b1_spec

OUT_DIR = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\71_W0_B0-B3_R7_20261127\40_OPS"
REPO = r"C:\Projects\Agent_Workspace\SQS-THC"


def original_case_table(spec: b1_spec) -> dict:
    text = open(spec["path"], encoding="utf-8").read()
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|") or "case-" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        cid = cells[0].split("</a>")[-1].strip()
        rows[cid] = {
            "case_id": cid,
            "key": cells[1],
            "fixture": cells[2],
            "mutation": cells[3],
            "predicate": cells[4],
            "expected_first_fail": cells[5],
            "reader_consumer": cells[6],
            "op_recipe": cells[7],
        }
    return rows


# ---- fixture validators (author fixture domain, explicitly NOT original schema) ----
def fixture_slot_check(slot: str, rec: dict) -> dict:
    """Single-field refusals described by the spec §04.R5 table. FIXTURE domain."""
    g = lambda k: rec.get(k, "")
    if slot == "watch_ui":
        if g("window_id") != g("lease_ref"):
            return {"deny": True, "first_fail": "FDA_WINDOW_HOLD", "field": "window_id!=lease_ref"}
        if g("valid_until") < g("observed_at"):
            return {"deny": True, "first_fail": "FDA_WINDOW_HOLD", "field": "valid_until<observed_at"}
        return {"deny": False}
    if slot == "radar_signal":
        if g("signal_known_at") > g("decision_asof"):
            return {"deny": True, "first_fail": "SIGNAL_TIME_HOLD", "field": "signal_known_at>decision_asof"}
        return {"deny": False}
    if slot == "xs_compile":
        if g("script_sha") == "":
            return {"deny": True, "first_fail": "COMPILE_RAW_MISSING", "field": "script_sha"}
        if not g("compiler_build"):
            return {"deny": True, "first_fail": "COMPILE_RAW_MISSING", "field": "compiler_build"}
        return {"deny": False}
    if slot == "xs_backtest":
        if g("pit_status") == "LOOKAHEAD":
            return {"deny": True, "first_fail": "BACKTEST_SCOPE_HOLD", "field": "pit_status"}
        if g("rights_epoch") == "":
            return {"deny": True, "first_fail": "BACKTEST_SCOPE_HOLD", "field": "rights_epoch"}
        return {"deny": False}
    if slot == "at_simulated_order":
        if g("fill_type") != "SIM_FILL":
            return {"deny": True, "first_fail": "SIM_BROKER_TYPE_DENY", "field": "fill_type"}
        return {"deny": False}
    if slot == "broker_external_event_read":
        if g("origin") == "GUI_ACK":
            return {"deny": True, "first_fail": "BROKER_FACT_MISSING", "field": "origin"}
        for f in ("broker_seq", "broker_receipt_ref", "book_of_record_version", "provenance_sha"):
            if not g(f):
                return {"deny": True, "first_fail": "BROKER_FACT_MISSING", "field": f}
        return {"deny": False}
    return {"deny": False, "note": "no fixture predicate"}


FIXTURE_BASELINES = {
    "watch_ui": {"window_id": "W-1", "lease_ref": "W-1", "build_ref": "b1", "sku": "XQ",
                 "observed_at": "2026-11-26T09:00:00+08:00",
                 "valid_until": "2026-11-26T10:00:00+08:00", "capture_sha": "a" * 64},
    "radar_signal": {"signal_id": "S-1", "signal_known_at": "2026-11-26T09:00:00+08:00",
                     "decision_asof": "2026-11-26T09:30:00+08:00", "source_sha": "b" * 64},
    "xs_compile": {"script_sha": "c" * 64, "compiler_build": "build-1", "diagnostics": []},
    "xs_backtest": {"pit_status": "PIT_OK", "rule_snapshot_ref": "R-1",
                    "rights_epoch": "rights-1", "period_start": "2026-01-01",
                    "period_end": "2026-06-30"},
    "at_simulated_order": {"sim_receipt_ref": "SIM-1", "fill_type": "SIM_FILL", "qty": 1,
                           "simulator_build": "sim-1"},
    "broker_external_event_read": {"broker_seq": 1, "broker_receipt_ref": "BR-1",
                                   "book_of_record_version": "bor-1", "provenance_sha": "d" * 64,
                                   "origin": "BROKER"},
}


def run_case(case: dict, spec: dict, unit: dict, ctx_via_cli: list[str]) -> dict:
    cid, key = case["case_id"], case["key"]
    kind = unit["kind"]
    rec = {"case_id": cid, "unit_id": unit["unit_id"], "key": key, "kind": kind,
           "expected_first_fail": case["expected_first_fail"],
           "oracle_domain": case["predicate"][:180],
           "actual": None, "verdict": None, "arms": []}

    if kind == "BASE":
        if cid.startswith("B1.POS."):
            out = E.op_base(REPO, CTX, [unit], HEAD)
            e = out["entries"][0]
            statuses = [t["status"] for t in e["targets"]]
            rec["actual"] = {"statuses": statuses,
                             "identities": [{k2: t.get(k2) for k2 in
                                             ("path", "commit", "blob", "raw_sha256", "disk_sha256", "bytes")}
                                            for t in e["targets"]],
                             "missing": e["missing"]}
            identity_ok = all(t["status"] in IDENTITY_STATUSES and t.get("raw_sha256")
                              for t in e["targets"]) and bool(e["targets"])
            unresolved = [s2 for s2 in statuses if s2 not in IDENTITY_STATUSES]
            rec["actual"]["identity_ok"] = identity_ok
            rec["actual"]["unresolved_statuses"] = unresolved
            if "NOT_IN_OWNER_ALLOWLIST" in statuses:
                rec["verdict"] = "HOLD"
                rec["hold_reason"] = "D-2 read right (owner allow-list) not granted for this declared cell"
            elif identity_ok:
                rec["verdict"] = "PASS"
            elif statuses:
                # a read-set with unresolved targets is NOT a POS pass: the identity of that
                # declared target was not established, even though the absence is recorded
                rec["verdict"] = "PARTIAL"
                rec["hold_reason"] = ("declared target(s) unresolved: " + ", ".join(unresolved) +
                                      " -- recorded as missing, never as PASS")
            else:
                rec["verdict"] = "FAIL"
        else:
            # arm 1: the original single mutation — delete this BASE row
            saved = E.BASE_TARGETS.pop(key, None)
            try:
                out = E.op_base(REPO, CTX, [unit], HEAD)
                errs = [x for x in out["errors"] if x["key"] == key]
                arm1 = {"arm": "DELETE_ROW", "expected_first_fail": "BASE_ROW_MISSING",
                        "observed": errs[0]["first_fail"] if errs else None,
                        "pass": bool(errs and errs[0]["first_fail"] == "BASE_ROW_MISSING")}
            finally:
                if saved is not None:
                    E.BASE_TARGETS[key] = saved
            rec["arms"].append(arm1)
            # arm 2: declared / remote masqueraded as local qualified
            declared = (saved or [(None, None)])[0][0] if saved else None
            probes = []
            if declared:
                for _, spec_str in saved:
                    rel = spec_str.split(":", 1)[1]
                    if spec_str.startswith("ext") or spec_str.startswith("glob"):
                        probes.append(E.resolve_target(CTX, REPO, HEAD, "repo:" + rel))
                    else:
                        present, _ = E.git(REPO, "cat-file", "-e", FOREIGN_COMMIT + "^{commit}")
                        # a real call with the foreign commit as the candidate pin, not a
                        # synthesised verdict
                        probe = E.resolve_target(CTX, REPO, FOREIGN_COMMIT, spec_str)
                        probe["foreign_commit"] = FOREIGN_COMMIT
                        probe["foreign_commit_present_locally"] = present is not None
                        probe["foreign_commit_provenance"] = ("SQS-THC_MVP remote main "
                                                              "(different repository)")
                        probes.append(probe)
            arm2 = {"arm": "FOREIGN_OR_REMOTE_AS_LOCAL",
                    "oracle_predeclared": ARM2_ORACLE,
                    "accepted_statuses_predeclared": list(ARM2_ACCEPTED_STATUSES),
                    "expected_first_fail": "FOREIGN_AS_LOCAL_REFUSED",
                    "observed": [{k2: p2.get(k2) for k2 in
                                  ("status", "commit", "blob", "raw_sha256",
                                   "foreign_commit_present_locally")} for p2 in probes],
                    "pass": bool(probes) and all(
                        p2["status"] in ARM2_ACCEPTED_STATUSES
                        and p2.get("commit") is None and p2.get("blob") is None
                        and p2.get("raw_sha256") is None for p2 in probes)}
            rec["arms"].append(arm2)
            rec["arms"] = [arm1]
            rec["added_safety_arm"] = arm2
            rec["actual"] = {"original_mutation": arm1,
                             "added_safety_regression": arm2["pass"]}
            # the case verdict rests on the ORIGINAL mutation only; the extra arm is an
            # added regression and can never be the reason a case passes
            rec["verdict"] = "PASS" if arm1["pass"] else "FAIL"
            if not arm2["pass"]:
                rec["added_safety_regression_failed"] = True

    elif kind == "KERNEL":
        if cid.startswith("B1.POS."):
            out = E.op_base(REPO, CTX, [unit], HEAD)
            t = out["entries"][0]["targets"][0]
            rec["actual"] = {"content_identity": t.get("content_identity"),
                             "symbols_ok": t.get("symbols_ok"), "symbols_total": t.get("symbols_total"),
                             "pinned_commit_present_locally": t.get("pinned_commit_present_locally"),
                             "raw_sha256": t.get("raw_sha256"), "observed_commit": t.get("observed_commit")}
            if t.get("content_identity") == "RAW_SHA_MATCH_AT_LOCAL_HEAD" and \
               t.get("symbols_ok") == t.get("symbols_total") and t.get("symbols_total"):
                rec["verdict"] = "PASS_SOURCE_BOUND"
                rec["claim"] = "CONTENT_IDENTITY_AND_SYMBOL_SPAN_ONLY"
                rec["hold_reason"] = ("D-4 semantic part stays HOLD: the 10 author rules are not "
                                     "ratified by the original Kernel Domain Owner; evidence PASS only")
            else:
                rec["verdict"] = "FAIL"
        else:
            rec["verdict"] = "HOLD"
            rec["hold_reason"] = ("D-4: 'change one protected field' needs the original protected "
                                  "field/path/old/new and the Kernel domain callable; an AST symbol or "
                                  "a SECOND_WRITER constant is not that oracle")

    elif kind == "FDA":
        slot = key.split(":", 1)[1]
        if slot == "broker_live_submit":
            pol = E.fda_live_broker_policy()
            if cid.startswith("B1.POS."):
                ctl = E.fda_live_submit_guard("read", pol["value"])
                arms_probe = [E.fda_live_submit_guard(a, pol["value"])
                              for a in ("submit", "replace", "cancel")]
                ok = (ctl["decision"] == "ALLOW_READ_CONTROL"
                      and ctl["order_path_reached"] is False
                      and ctl.get("artefact_sha256") == pol["sha256"]
                      and ctl.get("artefact_line") == pol["line"]
                      and pol["value"] == "DENY_ALWAYS"
                      and all(a["decision"] == "DENY" for a in arms_probe))
                rec["actual"] = {"pos_is_deny_invariant": True, "read_control": ctl,
                                 "policy": pol, "allowed_effect_pos": None}
                rec["verdict"] = "PASS" if ok else "FAIL"
            else:
                arms = [E.fda_live_submit_guard(a, pol["value"])
                        for a in ("submit", "replace", "cancel")]
                unk = E.fda_live_submit_guard("replace_all_orders", pol["value"])
                flip = E.fda_live_submit_guard("submit", "ALLOW")
                ok = (all(a["decision"] == "DENY" and a["first_fail"] == "FIN_ORDER_DENY_ALWAYS"
                          and a["order_path_reached"] is False for a in arms + [unk])
                      and flip["first_fail"] != "FIN_ORDER_DENY_ALWAYS")
                rec["actual"] = {"arms": arms, "unknown_action": unk,
                                 "policy_flip_probe": flip,
                                 "policy": {"value": pol["value"], "artefact": pol["artefact"],
                                            "line": pol["line"], "sha256": pol["sha256"]}}
                rec["verdict"] = "PASS" if ok else "FAIL"
        else:
            base = dict(FIXTURE_BASELINES[slot])
            b = fixture_slot_check(slot, base)
            if cid.startswith("B1.POS."):
                rec["actual"] = {"fixture_baseline_valid": not b["deny"], "check": b}
                # A fixture-domain check is not a product call: the slot's real Reader/
                # schema is unbound (D-3), so this is HOLD, never a PASS family member.
                rec["verdict"] = "HOLD" if not b["deny"] else "FAIL"
                rec["hold_reason"] = ("FIXTURE_ONLY_NO_PRODUCT_CALLABLE: D-3 author fixture domain only; "
                                      "no original typed schema/Reader, so this is not an original "
                                      "semantic PASS")
            else:
                mut = dict(base)
                if slot == "watch_ui":
                    mut["valid_until"] = "2026-11-26T08:00:00+08:00"
                elif slot == "radar_signal":
                    mut["signal_known_at"] = "2026-11-26T10:00:00+08:00"
                elif slot == "xs_compile":
                    mut["script_sha"] = ""
                elif slot == "xs_backtest":
                    mut["pit_status"] = "LOOKAHEAD"
                elif slot == "at_simulated_order":
                    mut["fill_type"] = "BROKER_FILL"
                elif slot == "broker_external_event_read":
                    mut["origin"] = "GUI_ACK"
                r = fixture_slot_check(slot, mut)
                rec["actual"] = {"mutation_field": r.get("field"), "deny": r.get("deny"),
                                 "first_fail": r.get("first_fail")}
                rec["verdict"] = ("HOLD" if r.get("deny") and
                                  r.get("first_fail") == case["expected_first_fail"] else "FAIL")
                rec["hold_reason"] = ("FIXTURE_ONLY_NO_PRODUCT_CALLABLE: the refusal fires in the author "
                                      "fixture domain with the original FirstFail string, but the original "
                                      "slot mapping/schema is unbound (D-3)")
    # both polarities recorded: the SPEC's declared first-fail beside what the product returned
    obs = None
    if isinstance(rec.get("actual"), dict):
        for k in ("first_fail", "observed_first_fail"):
            if rec["actual"].get(k):
                obs = rec["actual"][k]
                break
    rec["observed_first_fail"] = obs
    rec["first_fail_matches"] = (None if obs is None else
                                 rec["expected_first_fail"] == obs)
    return rec


# Ore-defined BEFORE any execution, never adjusted after seeing results.
IDENTITY_STATUSES = ("TRACKED", "TRACKED_CONTENT_MATCH", "ALLOWLIST_VERIFIED")
ARM2_ORACLE = ("a target that is not tracked at the pinned commit must never be given a "
               "commit/blob/raw_sha identity, whatever else exists on disk or in another repository")
ARM2_ACCEPTED_STATUSES = ("ABSENT_TREE", "NOT_IN_TREE", "COMMIT_UNRESOLVED", "DISK_BUT_UNTRACKED")
FOREIGN_COMMIT = "0489ac84a390a7172c6cce8322caefeb66b8942c"  # SQS-THC_MVP remote main: a DIFFERENT repo

CTX = E.load_trusted_context([])
HEAD = E.op_repo(REPO, CTX)["local_head"]


def main() -> int:
    spec = b1_spec.load_b1()
    table = original_case_table(spec)
    cases = {}
    for cid in sorted(spec["case_params"]):
        unit = spec["units"][spec["case_params"][cid]["unit_id"]]
        cases[cid] = run_case(table[cid], spec, unit, [])
    counts = {}
    for c in cases.values():
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    result = {
        "schema": "SST.PH01.W0.B1.TQAEP@5",
        "spec_version": E.SPEC_VERSION,
        "spec_b1_sha256": spec["sha256"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo_head": HEAD,
        "case_count": len(cases),
        "expected_case_set_sha256": spec["case_id_set_sha"],
        "verdict_counts": counts,
        "cases": cases,
        "claim_ceiling": ("B1_ACCEPTED requires every applicable case to be PASS with the original "
                          "oracle. HOLD and FIXTURE_ONLY are NOT PASS."),
    }
    out = os.path.join(OUT_DIR, "b1_r7_tqaep.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps({"written": out, "counts": counts,
                      "case_count": len(cases)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
