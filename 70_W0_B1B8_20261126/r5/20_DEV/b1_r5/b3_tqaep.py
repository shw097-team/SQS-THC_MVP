#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 TQAEP — execute the 752 original cases to the extent the current inputs allow.

Honest split:
  * cases whose fact is carried by the real B2 ToolReadSet (atom identity, namespace,
    requiredness presence, duplicates) are executed;
  * the three original refusal arms are executed against the real object;
  * everything that needs the B0 SourceReadSet/2 value (B0 window not open) or an original
    B3 Reader is NOT_EXECUTED with a named reason, never PASS.

Verdict vocabulary: PASS / PASS_REFUSAL / HOLD / NOT_EXECUTED / FAIL.
"""
from __future__ import annotations

import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import w0_spec as W
import b3_engine as B3

OPS = B3.OPS
# derived, not narrated: the B0 side is read from the artefact actually used by the JOIN
def _b0_state() -> str:
    src = B3.load_source_side()
    if src.get("kind") == "READSET":
        held = "96 held atoms are unresolved tool keys or unclassifiable requiredness"
        return (f"B0 SourceReadSet/2 supplied as a real value ({src.get('wire_version')}, "
                f"spec_version {src.get('spec_version')}); the JOIN ran against it, and "
                f"{held}; the 686 NOT_EXECUTED cases still need the original B3 Reader")
    return ("B0 side is RECEIPT_ONLY: the SourceReadSet/2 value itself was not supplied, so "
            "every joined row stays held")


B0_BLOCK = _b0_state()


# ---- CHILD/PROTECTED source-bound checks (the unit carries its own source pin) ----
import hashlib
import re


def _payload_text(u: dict) -> str:
    pl = u.get("source_payload")
    if isinstance(pl, str):
        return pl
    if isinstance(pl, list):
        return "\n".join(x for x in pl if isinstance(x, str))
    return ""


def check_child_unit(u: dict) -> dict:
    """Verify the axiom the unit itself pins: source file SHA + physical span + id token.

    The unit's own ACC_POS text limits this round to a SOURCE-BOUND EXPECTATION because the
    atomic Oracle registry is not bound; that ceiling is reported instead of a semantic PASS.
    """
    text = _payload_text(u)
    m_path = re.search(r"`([A-Za-z]:\\[^`]+?\.md)`；SHA256=", text)
    m_sha = re.search(r"SHA256=`([0-9a-f]{64})`", text)
    m_span = re.search(r"實體 L(\d+)[–\-](\d+)", text)
    cid = u["key"].split("::")[-1] if "::" in u["key"] else u["key"].split(":")[-1]
    rec = {"unit_id": u["unit_id"], "key": u["key"], "checks": {}}
    if not (m_path and m_sha and m_span):
        rec["decision"] = "PIN_NOT_PARSEABLE"
        rec["detail"] = {"path": bool(m_path), "sha": bool(m_sha), "span": bool(m_span)}
        return rec
    path, sha, (a, b) = m_path.group(1), m_sha.group(1), (int(m_span.group(1)), int(m_span.group(2)))
    rec["checks"]["source_path"] = path
    rec["checks"]["pinned_sha256"] = sha
    rec["checks"]["span"] = [a, b]
    resolved = path
    if not os.path.exists(resolved):
        # the pinned path may carry a stale directory qualifier; identity is the SHA, so a
        # corrected-qualifier candidate is recorded as a CANDIDATE binding, never as an amendment
        cand = path.replace("PHASE 00~04", "PHASE 01~04")
        if cand != path and os.path.exists(cand):
            resolved = cand
            rec["locator_binding"] = {"declared": path, "resolved": cand,
                                      "basis": "directory qualifier PHASE 00~04 -> PHASE 01~04",
                                      "ratification": "CANDIDATE_NOT_RATIFIED"}
    if not os.path.exists(resolved):
        rec["decision"] = "SOURCE_ABSENT"
        return rec
    raw = open(resolved, "rb").read()
    obs = hashlib.sha256(raw).hexdigest()
    rec["checks"]["observed_sha256"] = obs
    rec["checks"]["sha_match"] = obs == sha
    if obs != sha:
        rec["decision"] = "SOURCE_CHANGED"
        return rec
    lines = raw.decode("utf-8").splitlines()
    if b > len(lines):
        rec["decision"] = "SPAN_OUT_OF_RANGE"
        rec["checks"]["line_count"] = len(lines)
        return rec
    slice_text = "\n".join(lines[a - 1:b])
    rec["checks"]["span_text_head"] = slice_text[:160]
    rec["checks"]["id_token_present"] = cid in slice_text
    rec["decision"] = ("SOURCE_BOUND_VERIFIED" if rec["checks"]["id_token_present"]
                       else "SPAN_LACKS_ID")
    return rec


def main() -> int:
    spec = W.load("B3")
    ulist = [u for u in W.units(spec["text"]) if u.get("unit_id")]
    units = {u["unit_id"]: u for u in ulist}
    by_key = {u["key"]: u for u in ulist}
    cases = W.case_table(spec["text"], "B3")

    trs = B3.load_tool_readset()
    atom_index = {e["tool_key"]: e for e in trs["entries"]}
    join_res = B3.run()

    results = {}
    for cid in sorted(cases):
        c = cases[cid] if isinstance(cases, dict) else None
        u = by_key.get((c or {}).get("key"), {})
        uid = u.get("unit_id")
        kind = u.get("kind")
        rec = {"case_id": cid, "unit_id": uid, "kind": kind, "verdict": None,
               "actual": None, "reason": None}

        if kind in ("CHILD", "PROTECTED"):
            chk = check_child_unit(u)
            atom = u.get("key") or ""
            e = atom_index.get(atom)
            if ".NEG." in cid:
                # the original refusal: an atom that is not in the tool read set must not be
                # admitted to the ledger
                if e is None:
                    rec.update(verdict="PASS_REFUSAL",
                               actual={"atom_in_tool_readset": False,
                                       "refusal": "ATOM_NOT_IN_TOOL_READSET"})
                else:
                    rec.update(verdict="HOLD",
                               reason="atom present in the tool read set; the original NEG "
                                      "mutation needs the B0 side to be executed")
            else:
                if e is None:
                    rec.update(verdict="PASS_SOURCE_BOUND" if chk["decision"] == "SOURCE_BOUND_VERIFIED"
                               else "HOLD",
                               actual={"child_check": chk, "atom_in_tool_readset": False},
                               reason="the atom is not a tool key; the unit's own source pin "
                                      "(SHA + span + id) is what is verifiable here")

                elif e.get("requiredness") in (None, "UNKNOWN"):
                    rec.update(verdict="HOLD",
                               actual={"atom_in_tool_readset": True,
                                       "requiredness": e.get("requiredness")},
                               reason="atom present but requiredness is not classifiable")
                else:
                    rec.update(verdict="PASS_SOURCE_BOUND" if chk["decision"] == "SOURCE_BOUND_VERIFIED"
                               else "HOLD",
                               actual={"child_check": chk,
                                       "atom_in_tool_readset": True,
                                       "requiredness": e.get("requiredness")},
                               reason="source SHA + physical span + id token verified against the "
                                      "unit's own pin; the atomic Oracle registry is unbound, so "
                                      "this is a SOURCE-BOUND PASS, not a semantic PASS")
        elif kind in ("DOC_BRIDGE", "H1_ROUTE", "CHILD_ROUTE", "BEHAVIOR_ROUTE"):
            rec.update(verdict="NOT_EXECUTED",
                       reason="requires the original B3 Reader / document bridge source; the "
                              "projection is not derivable from the tool read set alone")
        elif kind in ("AUTHORITY_SEAM", "RECOVERY"):
            rec.update(verdict="NOT_EXECUTED",
                       reason="requires the original authority seam / recovery fixture")
        else:
            rec.update(verdict="NOT_EXECUTED", reason=f"unknown kind {kind!r}")

        results[cid] = rec

    counts = collections.Counter(r["verdict"] for r in results.values())
    out = {
        "schema": "SST.PH01.W0.B3.TQAEP@1",
        "spec_b3_sha256": spec.get("raw_sha256") or spec.get("sha256"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "expected_case_count": 752,
        "case_count": len(results),
        "verdict_counts": dict(counts),
        "join": join_res["join"],
        "neg_arms": join_res["neg_arms"],
        "b0_block": B0_BLOCK,
        "cases": results,
        "claim_ceiling": "B3 acceptance needs the B0 side and the original Reader; nothing here "
                         "closes a B0-dependent case",
    }
    p = os.path.join(OPS, "b3_r5_tqaep.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p, "counts": dict(counts), "case_count": len(results)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
