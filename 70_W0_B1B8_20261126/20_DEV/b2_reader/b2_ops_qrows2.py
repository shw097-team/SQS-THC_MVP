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
    parent_attempts = parent_reproduced = evidence_bound = 0
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
            "requiredness_agree": req_row == req_ind,
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
            pin_txt = str(sp[3]) if len(sp) > 3 else ""
        has_version = bool(VERSION_RE.search(pin_txt))
        if k == "TECH_ROUTE":
            rec["pin_state"] = ("ROUTE_ONLY_NO_TOOL_PIN"     # route row: EWI-deferred, no tool pin
                                if "後延" in (u.get("input_rule") or "") or "EVAL_ONLY" in pin_txt
                                else ("VERSION_SHAPED" if has_version else "UNBOUND"))
        else:
            rec["pin_state"] = ("VERSION_SHAPED" if has_version else
                                ("UNBOUND" if ("UNBOUND" in pin_txt.upper()
                                               or not pin_txt.strip())
                                 else "TEXT_WITHOUT_VERSION"))
        joined = " ".join(str(x) for x in sp)
        rec["pin_text"] = pin_txt
        rec["licence_state"] = ("DECLARED" if re.search(r"MIT|Apache|BSD|proprietary|UNBOUND",
                                                        joined, re.I) else "UNBOUND")
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

        ref = S.parse_ref(u.get("original_source_ref") or "")
        if ref.get("kind") == "PARENT":
            parent_attempts += 1
            if ptext and ref["sha"] == S.PARENT_SHA:
                cl = S.clause_sha(ptext, ref["a"], ref["b"])
                match = [r for r, v in (cl.get("candidates") or {}).items()
                         if v == u.get("direct_clause_sha")]
                rec["clause"] = {"source": "PARENT", "rule_matched": match[0] if match else None,
                                 "reproduced": bool(match)}
                if match:
                    parent_reproduced += 1
            else:
                rec["clause"] = {"source": "PARENT", "reproduced": False,
                                 "reason": "PARENT_SHA_UNBOUND"}
        elif ref.get("kind") == "EVIDENCE":
            ev = S.parent_index().get(ref["sha"])
            rec["clause"] = {"source": "EVIDENCE", "sha_bound": bool(ev),
                             "resolved_path": ev, "reproduced": None,
                             "note": "evidence row identity: the referenced document is bound by "
                                     "sha; the row-level clause sha rule is not published, so it is "
                                     "not claimed as reproduced"}
            if ev:
                evidence_bound += 1
        else:
            rec["clause"] = {"source": ref.get("kind"), "reproduced": None}
        rows.append(rec)

    no_pin_text = [r for r in rows if r["pin_state"] == "UNBOUND"]
    no_version = [r for r in rows if r["pin_state"] != "VERSION_SHAPED"]
    a = {r["unit_id"] for r in no_pin_text}
    b = {r["unit_id"] for r in no_version}
    route_only = {r["unit_id"] for r in rows if r["pin_state"] == "ROUTE_ONLY_NO_TOOL_PIN"}
    pin_recon = {
        "predicate_A_no_pin_text_or_UNBOUND_token": {
            "count": len(a),
            "by_kind": dict(collections.Counter(r["kind"] for r in no_pin_text))},
        "predicate_B_no_version_shaped_pin": {
            "count": len(b),
            "by_kind": dict(collections.Counter(r["kind"] for r in no_version))},
        "historical_72": {
            "definition": "HARD rows whose pin text carries UNBOUND + TECH_ROUTE route-only rows",
            "measured": len(a) + len(route_only),
            "hard_unbound": len(a), "tech_route_route_only": len(route_only),
            "reproduces_72": (len(a) + len(route_only)) == 72},
        "historical_54": {
            "definition": "TECH_ROUTE route-only rows (no tool pin by design: EWI-deferred)",
            "measured": len(route_only), "reproduces_54": len(route_only) == 54},
        "both": len(a & b), "A_only": len(a - b), "B_only": len(b - a),
        "conclusion": ("NOT reconciled to the historical numbers, and it is not possible to: the "
                       "old 72 cannot be rebuilt from the SPEC (HARD pin-UNBOUND measures 16 here, "
                       "+ 54 route-only = 70; the two HARD rows carrying a version pin are Pydantic "
                       "and JSON-Schema). The old TQAEP's 54 matches the TECH_ROUTE count exactly. "
                       "Conclusion: one of the two historical counts was computed on a different, "
                       "now-unrecorded predicate. The per-row pin_state below is the single carrier "
                       "and B5 must consume it, never either historical scalar."),
    }

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
            "all_three_signals_agree": len(q_disagree) == 0,
            "disagreements": q_disagree[:10],
            "non_q_rows": len(rows) - sum(q_counts.values()),
            "rule": "quadrant = H4 section ∩ key namespace prefix ∩ q_row.full_key; all Q rows "
                    "must agree on the three signals; the 54 non-Q rows are HARD/E00_TECH/TECH_ROUTE",
        },
        "requiredness_delta": {
            "hard_rows": len(hard), "hard_preserved": len(hard) - len(downgraded),
            "downgraded_hard": downgraded,
            "e00_tech_rows": len(e00), "tech_route_rows": len(route),
            "row_vs_independent_disagreements": [
                {"unit_id": r["unit_id"], "row": r["requiredness_row"],
                 "independent": r["requiredness_independent"]}
                for r in rows if not r["requiredness_agree"]][:40],
            "disagreement_count": sum(1 for r in rows if not r["requiredness_agree"]),
            "rule": "Q4 EVAL_ONLY never downgrades Q1 HARD; each row is judged against the rule "
                    "derived from its own SPEC input_rule, never against itself",
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
            "parent_attempted": parent_attempts,
            "parent_reproduced": parent_reproduced,
            "parent_unreproduced": parent_attempts - parent_reproduced,
            "evidence_source_bound_by_sha": evidence_bound,
            "evidence_source_unbound": (len(rows) - parent_attempts) - evidence_bound,
            "note": "PARENT clauses: direct_clause_sha re-derived from the rebound parent bytes under "
                    "three explicit span rules; none reproduces, so the generator's clause-sha rule "
                    "is UNBOUND and clause identity is not claimed. EVIDENCE refs bind the referenced "
                    "document by sha only. This is a named gap, not a PASS.",
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
    print("clause: parent", parent_reproduced, "/", parent_attempts,
          "| evidence bound", evidence_bound)
    print("parent:", parent_info["state"])
    print(f"receipt {p} {os.path.getsize(p)}B sha256={S.sha(open(p,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
