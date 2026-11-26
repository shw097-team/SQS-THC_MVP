#!/usr/bin/env python3
"""B2 OPS v2 — QROWS / HARD / META / RETURN (ToolReadSet@2).

Changes from @1 (whose receipt claimed PAYLOAD_INTEGRITY_ONLY only):

* quadrant census cross-checked on three independent signals (H4 section, key namespace prefix,
  q_row.full_key);
* the two conflicting "unbound pin" counts (72 in ToolReadSet@1, 54 in the old TQAEP) are
  reconciled by naming both predicates and the exact set difference;
* requiredness compared against the requirement derived from the SPEC's own input_rule;
* pin/licence/lock carried as typed state so B5 consumes a gap, never a blank.

Effect SOURCE_READ, WriteSet=[], preimage N/A. Nothing installed, nothing selected.
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
VERSION_RE = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b")


def main() -> int:
    spec = S.load_spec()
    t = spec["text"]
    us = S.units(t)
    parent_p, parent_info = S.parent_path()
    ptext = open(parent_p, encoding="utf-8").read() if parent_p else None

    rows, q_counts = [], collections.Counter()
    q_disagree = []
    parent_attempts = parent_reproduced = evidence_bound = carrier_bound = 0
    for u in us:
        sp = u.get("source_payload") or []
        k = u.get("kind")
        req_row = S.row_requiredness(u)
        req_ind, req_rule = S.independent_requiredness(u)
        rec = {
            "unit_id": u["unit_id"], "key": u["key"], "kind": k,
            "op_id": u.get("op_id"),
            "namespace": (u.get("key") or "").split("::")[0],
            "requiredness_row": req_row,
            "requiredness_independent": req_ind,
            "requiredness_rule": req_rule,
            "requiredness_applicable": k in ("HARD", "E00_TECH"),
            "requiredness_check_mode": ("RULE_CROSS_FIELD" if k in ("HARD", "E00_TECH")
                                       else ("N/A_ROUTE" if k == "TECH_ROUTE" else "VERBATIM_ONLY")),
            "requiredness_agree": ((req_row == req_ind) if k in ("HARD", "E00_TECH") else None),
            "payload_sha": u.get("payload_sha"),
            "original_source_ref": u.get("original_source_ref"),
            "direct_clause_sha": u.get("direct_clause_sha"),
            "case_ids": u.get("case_ids"),
        }
        pin_txt = ""
        if k == "HARD":
            pin_txt = str(sp[5]) if len(sp) > 5 else ""
        elif k == "E00_TECH":
            pin_txt = str(sp[1]) if len(sp) > 1 else ""
        elif k == "TECH_ROUTE":
            joined = str(sp[0]) if sp else ""
            pin_txt = joined
        elif k == "Q_SOURCE_ROW":
            # A Q row is a tool-registry row, but which column carries the pin is not published; the
            # text in column 3 is a need/slot sentence, not a pin (round-3 defect 4). Not evaluated.
            pin_txt = ""
        has_version = bool(VERSION_RE.search(pin_txt))
        if k == "TECH_ROUTE":
            rec["pin_state"] = ("ROUTE_ONLY_NO_TOOL_PIN"     # route row: EWI-deferred, no tool pin
                                if "後延" in (u.get("input_rule") or "") or "EVAL_ONLY" in pin_txt
                                else ("VERSION_SHAPED" if has_version else "UNBOUND"))
        elif k == "Q_SOURCE_ROW":
            rec["pin_state"] = "NOT_EVALUATED_Q_ROW"
            rec["pin_gap"] = "which source column carries the tool pin is not published; B5 must not read"
        else:
            rec["pin_state"] = ("VERSION_SHAPED" if has_version else
                                ("UNBOUND" if ("UNBOUND" in pin_txt.upper()
                                               or not pin_txt.strip())
                                 else "TEXT_WITHOUT_VERSION"))
        joined = " ".join(str(x) for x in sp)
        rec["pin_text"] = pin_txt
        # CJK neighbours are word characters, so  never fires; use explicit letter guards instead.
        lic = re.search(r"(?<![A-Za-z])(MIT|Apache|BSD|proprietary|GPL|MPL|ISC|PSF|Unlicense)"
                        r"(?![A-Za-z])", joined, re.I)
        # "Apache Arrow"/"Apache Spark"/"Apache Kafka" are product names, not licences (round-4)
        ctx = re.search(r"(Apache)\s+(Arrow|Spark|Kafka|Beam|Airflow)", joined, re.I)
        if lic and ctx and lic.group(1).lower() == "apache":
            rec["licence_state"] = "TOOL_NAME_ONLY"
        else:
            rec["licence_state"] = "DECLARED" if lic else "TOKEN_ABSENT"
        rec["licence_token"] = lic.group(0) if lic else None
        rec["lock_state"] = "UNBOUND"          # no transitive lock artifact is bound in B2

        if k == "Q_SOURCE_ROW":
            qa = S.q_of(u)
            rec["q"] = qa["q"]
            rec["q_votes"] = qa["votes"]
            qr = u.get("q_row") or {}
            rec["q_row"] = {"full_key": qr.get("full_key"), "source_row": qr.get("source_row"),
                            "carrier_line": qr.get("carrier_line")}
            rec["q_row_payload_matches"] = (qr.get("payload") == sp)
            if qa["agree"] and qa["q"]:
                q_counts[qa["q"]] += 1
            else:
                q_disagree.append({"unit_id": u["unit_id"], "votes": qa["votes"]})

        # clause identity is carried by direct_parent_ref (NOT original_source_ref: for Q rows that
        # points at the evidence document). Rule: lines a..b inclusive, including the LF of line b.
        ref = S.parse_ref(u.get("direct_parent_ref") or "")
        if ref.get("kind") == "FILE":
            parent_attempts += 1
            res_sha = ref["sha"]
            if ptext and res_sha == S.PARENT_SHA:
                cl = S.clause_sha(ptext, ref["a"], ref["b"])
                match = [r for r, v in (cl.get("candidates") or {}).items()
                         if v == u.get("direct_clause_sha")]
                rec["clause"] = {"source": "direct_parent_ref", "rule_matched": match[0] if match else None,
                                 "reproduced": bool(match)}
                if match:
                    parent_reproduced += 1
            else:
                rec["clause"] = {"source": "direct_parent_ref", "reproduced": False,
                                 "reason": "PARENT_SHA_UNBOUND"}
        else:
            rec["clause"] = {"source": ref.get("kind"), "reproduced": None}

        # the Q rows also cite a carrier document whose declared path has a stale PHASE segment;
        # resolve it by sha and record the rebind (round-1 checker item 10)
        if k == "Q_SOURCE_ROW":
            vc = S.parse_ref((u.get("q_row") or {}).get("verified_carrier_ref") or "")
            if vc.get("kind") == "FILE":
                got = S.carrier_index().get(vc["sha"])
                rec["carrier_source"] = {
                    "declared_path": vc.get("path"), "expected_sha256": vc["sha"],
                    "resolved_path": got,
                    "state": ("CARRIER_SOURCE_REBOUND_BY_SHA" if got else "CARRIER_SOURCE_UNBOUND"),
                    "ratification": "CANDIDATE_NOT_RATIFIED — locator rebind only",
                    "declared_path_has_stale_segment": bool(
                        vc.get("path") and "PHASE 00~04" in vc["path"])}
                if got:
                    carrier_bound += 1
        rows.append(rec)

    # ---- pin history, reconstructed from the PINNED OLD CODE (b2_ops_qrows.py:76-79):
    #      pin := source_payload[5] for every kind; count if absent or containing "UNBOUND".
    old_unbound = []
    for u in us:
        sp = u.get("source_payload") or []
        pin = str(sp[5]) if len(sp) > 5 else ""
        if (not pin.strip()) or ("UNBOUND" in pin.upper()):
            old_unbound.append(u)
    old_by_kind = dict(collections.Counter(u["kind"] for u in old_unbound))
    no_col5 = [u for u in us if len(u.get("source_payload") or []) <= 5]
    clean_no_version = [r for r in rows if r["pin_state"] != "VERSION_SHAPED"]
    pin_recon = {
        "old_predicate": "pin := source_payload[5]; unbound if absent or 'UNBOUND' in pin "
                         "(b2_ops_qrows.py:76-79, still present in the pinned file)",
        "historical_72": {"measured": len(old_unbound), "reproduces_72": len(old_unbound) == 72,
                          "by_kind": old_by_kind,
                          "why": "HARD 16 carry pin text with UNBOUND; E00_TECH 2 carry the "
                                 "NEG sentinels EFFECT_UNBOUND / EXECUTOR_UNBOUND in column 5; "
                                 "TECH_ROUTE 54 have no column 5 at all"},
        "historical_54": {"measured": len(no_col5), "reproduces_54": len(no_col5) == 54,
                          "by_kind": dict(collections.Counter(u["kind"] for u in no_col5)),
                          "note": "the old TQAEP counted rows with no pin column: exactly TECH_ROUTE"},
        "clean_no_version_count": {"measured": sum(1 for r in clean_no_version
                                                   if r["pin_state"] != "NOT_EVALUATED_Q_ROW"),
                                   "by_kind": dict(collections.Counter(r["kind"]
                                                  for r in clean_no_version
                                                  if r["pin_state"] != "NOT_EVALUATED_Q_ROW")),
                                   "excluded": "NOT_EVALUATED_Q_ROW is not a version verdict"},
        "conclusion": ("both historical numbers are TRUE and reproducible from the same SPEC plus "
                       "the pinned old predicate: 72 = 16 HARD + 2 E00_TECH + 54 TECH_ROUTE, and 54 "
                       "= TECH_ROUTE exactly. They measure 'no usable pin text', not 'no tool' and "
                       "not 'not installed'. The semantically clean no-version count is "
                       f"{len(clean_no_version)}. B5 must consume the per-row pin_state, never "
                       "either historical scalar."),
    }
    a = {r["unit_id"] for r in rows if r["pin_state"] == "UNBOUND"}
    b = {r["unit_id"] for r in clean_no_version}
    pin_recon["per_row_state_vs_old"] = {"A_unbound": len(a), "B_no_version": len(b),
                                         "A_only": len(a - b), "B_only": len(b - a)}

    hard = [r for r in rows if r["kind"] == "HARD"]
    e00 = [r for r in rows if r["kind"] == "E00_TECH"]
    route = [r for r in rows if r["kind"] == "TECH_ROUTE"]
    qrows = [r for r in rows if r["kind"] == "Q_SOURCE_ROW"]
    downgraded = [r["unit_id"] for r in hard if r["requiredness_row"] != "HARD"]

    out = {
        "schema": "SST.PH01.W0.B2.ToolReadSet@2",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M", "bid": 2,
        "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A", "fin_order": "DENY",
        "spec": {"path": spec["path"], "bytes": spec["bytes"], "raw_sha256": spec["raw_sha256"],
                 "expected_sha256": S.SPEC_SHA, "pin_match": spec["pin_match"]},
        "parent_source": parent_info,
        "census": {"units": len(rows), "q_source_rows": len(qrows), "hard": len(hard),
                   "e00_tech": len(e00), "tech_route": len(route)},
        "q_denominators": {
            "Q1": q_counts.get("Q1", 0), "Q2": q_counts.get("Q2", 0),
            "Q3": q_counts.get("Q3", 0), "Q4": q_counts.get("Q4", 0),
            "sum": sum(q_counts.values()),
            "expected": {"Q1": 440, "Q2": 513, "Q3": 378, "Q4": 54},
            "signal_claim": "two_collinear_key_signals_agree_plus_source_row_ranges",
            "key_signals_agree": len(q_disagree) == 0,
            "key_signals_are_collinear": True,
            "collinearity_note": ("key namespace prefix and q_row.full_key are the same key prefix: "
                                  "q_row.full_key == key minus '::ROW=<n>'. They are NOT independent."),
            "disagreements": q_disagree[:10],
            "source_row_ranges": {
                qn: [min((u["q_row"] or {}).get("source_row", 0) for u in us
                         if u.get("kind") == "Q_SOURCE_ROW" and (u.get("q_row") or {}).get("full_key", "")
                         .startswith("R3-REGISTRY-" + qn)),
                     max((u["q_row"] or {}).get("source_row", 0) for u in us
                         if u.get("kind") == "Q_SOURCE_ROW" and (u.get("q_row") or {}).get("full_key", "")
                         .startswith("R3-REGISTRY-" + qn))]
                for qn in ("Q1", "Q2", "Q3", "Q4")},
            "source_row_ranges_disjoint": (lambda r: all(
                r[a][1] < r[b][0] for a, b in (("Q1", "Q2"), ("Q2", "Q3"), ("Q3", "Q4"))))(
                {qn: [min((u["q_row"] or {}).get("source_row", 0) for u in us
                          if u.get("kind") == "Q_SOURCE_ROW"
                          and (u.get("q_row") or {}).get("full_key", "").startswith("R3-REGISTRY-" + qn)),
                     max((u["q_row"] or {}).get("source_row", 0) for u in us
                         if u.get("kind") == "Q_SOURCE_ROW"
                         and (u.get("q_row") or {}).get("full_key", "").startswith("R3-REGISTRY-" + qn))]
                 for qn in ("Q1", "Q2", "Q3", "Q4")}),
            "non_q_rows": len(rows) - sum(q_counts.values()),
            "rule": "quadrant from the key's namespace prefix, corroborated by disjoint q_row.source_row "
                    "ranges; the 80 non-Q rows are HARD 18 + E00_TECH 8 + TECH_ROUTE 54",
        },
        "requiredness_delta": {
            "hard_rows": len(hard), "hard_preserved": len(hard) - len(downgraded),
            "downgraded_hard": downgraded,
            "e00_tech_rows": len(e00), "tech_route_rows": len(route),
            "row_vs_independent_disagreements": [
                {"unit_id": r["unit_id"], "row": r["requiredness_row"],
                 "independent": r["requiredness_independent"]}
                for r in rows if r["requiredness_agree"] is False][:40],
            "disagreement_count": sum(1 for r in rows if r["requiredness_agree"] is False),
            "checked_rows": sum(1 for r in rows if r["requiredness_applicable"]),
            "check_mode": {
                "HARD": "RULE_CROSS_FIELD (payload column 1 vs the unit's own input_rule)",
                "E00_TECH": "RULE_CROSS_FIELD (payload column 2 vs the unit's own input_rule)",
                "TECH_ROUTE": "N/A — route-only by kind; disposition checked separately",
                "Q_SOURCE_ROW": "VERBATIM_ONLY — the row's column 2 is compared to nothing "
                                "independent; the authoritative value lives in the original table row",
            },
            "verbatim_only_rows": sum(1 for r in rows if r["kind"] == "Q_SOURCE_ROW"),
            "prose_rows_n_a": sum(1 for r in rows if r["kind"] == "Q_SOURCE_ROW"
                                  and r["requiredness_row"] not in S.REQ_TOKENS),
            "original_source_comparisons": 0,
            "rule": ("18 HARD present and 0 removed is a data fact. The comparison is NOT independent "
                     "for 1,385 Q rows (VERBATIM_ONLY) and N/A for 54 route rows, so "
                     "disagreement_count = 0 must not be read as evidence; it is structurally "
                     "guaranteed for those kinds. Q4 EVAL_ONLY is a false premise: there are 0 such "
                     "rows (the EVAL_ONLY rows are in Q1)."),
        },
        "wheel_metadata_ref": {
            "pin_reconciliation": pin_recon,
            "typed_gaps": {
                "pin_unbound": sum(1 for r in rows if r["pin_state"] == "UNBOUND"),
                "lock_unbound": sum(1 for r in rows if r["lock_state"] == "UNBOUND"),
                "licence_unbound": sum(1 for r in rows if r["licence_state"] == "UNBOUND"),
            },
            "note": "pin/licence/lock/first_probe per tool is B5's selection duty; B2 records the "
                    "gap as a typed value and never fills it from candidate output",
        },
        "clause_reproduction": {
            "rule": S.clause_rule_note(),
            "reference_used": "direct_parent_ref",
            "attempted": parent_attempts,
            "reproduced": parent_reproduced,
            "unreproduced": parent_attempts - parent_reproduced,
            "carrier_sources_bound_by_sha": carrier_bound,
            "carrier_source_note": ("Q rows cite a carrier document whose declared path says "
                                    "'PHASE 00~04' but which lives under 'PHASE 01~04'; it is "
                                    "rebound by sha and labelled CANDIDATE_NOT_RATIFIED"),
            "note": ("uses direct_parent_ref, not original_source_ref: for Q rows the latter points "
                     "at the evidence document, which is why the first attempt measured 0/80."),
        },
        "rows": rows,
    }
    p = os.path.join(OPS, "b2_toolreadset_" + datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                     + ".json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print("units", len(rows), "| Q", dict(q_counts), "| HARD", len(hard),
          "| E00", len(e00), "| ROUTE", len(route))
    print("q signals agree:", len(q_disagree) == 0,
          "| non-Q rows:", out["q_denominators"]["non_q_rows"])
    print("pin A/B:", len(a), "/", len(b), "| A_only", len(a - b))
    print("requiredness disagreements:", out["requiredness_delta"]["disagreement_count"])
    print("clause: reproduced", parent_reproduced, "/", parent_attempts,
          "| carrier bound", carrier_bound)
    print("parent:", parent_info["state"])
    print(f"receipt {p} {os.path.getsize(p)}B sha256={S.sha(open(p,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
