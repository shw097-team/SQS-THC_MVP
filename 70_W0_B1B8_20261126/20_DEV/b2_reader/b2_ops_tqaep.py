#!/usr/bin/env python3
"""B2 OPS-ECP / TQAEP — per-case payload-integrity execution over all 2,930 cases.

Claim ceiling: PAYLOAD_INTEGRITY_ONLY. This executes the pin oracle at case granularity
(1465 POS + 1465 NEG). It does NOT claim Q-row semantic requiredness, tool availability or
licence/lock state; those stay with their own owners and are recorded as separate rights.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, datetime, collections

KBASE = r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
WAVE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(WAVE, "40_OPS")

SPEC_DIR = None
for n in os.listdir(KBASE):
    if n.startswith("W0_B1-B8_NATIVE_FIRST_2026-11-26_r4"):
        SPEC_DIR = os.path.join(KBASE, n)
        break
spec_path = [os.path.join(SPEC_DIR, f) for f in os.listdir(SPEC_DIR)
             if f.startswith("SST_PLP_PH01_W0_B2_") and "實質正文" in f][0]
EXPECT_SHA = "140de5bc1249dbb6e2d199dae336cf3a57741097aaf5cd883a7ec280e9199d3b"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def compact(payload) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()


def main() -> int:
    raw = open(spec_path, "rb").read()
    got = sha(raw)
    t = raw.decode("utf-8")
    now = datetime.datetime.now().astimezone()
    ts = now.strftime("%Y%m%dT%H%M%S")

    marks = [(m.group(1), m.end()) for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t)]
    cases, pos_ok = [], 0
    kinds, quads = collections.Counter(), collections.Counter()
    for uid, pos in marks:
        i = t.find("```json", pos)
        if i < 0:
            continue
        j = t.find("```", i + 7)
        try:
            d = json.loads(t[i + 7:j])
        except Exception:
            continue
        declared = d.get("payload_sha")
        body = d.get("source_payload")
        kind = d.get("kind")
        q = d.get("q") or d.get("quadrant")
        kinds[kind] += 1
        quads[q] += 1

        # POS: the declared pin must reproduce from the payload alone
        calc = sha(compact(body))
        pos_pass = (calc == declared)
        pos_ok += pos_pass
        cases.append({"case_id": f"{uid}.POS", "unit_id": uid, "kind": kind, "q": q,
                      "polarity": "POS", "mutation": None,
                      "expected": declared, "actual": calc,
                      "first_fail": None if pos_pass else "PAYLOAD_SHA_MISMATCH",
                      "verdict": "PASS" if pos_pass else "FAIL"})

        # NEG: one single-field mutation must be detected by the same oracle
        if isinstance(body, dict):
            mut = dict(body); mut["__b2_neg_probe__"] = "single-field-addition"
        elif isinstance(body, list):
            mut = list(body) + ["__b2_neg_probe__"]
        else:
            mut = body
        mcalc = sha(compact(mut))
        neg_pass = (mcalc != declared)
        cases.append({"case_id": f"{uid}.NEG", "unit_id": uid, "kind": kind, "q": q,
                      "polarity": "NEG", "mutation": "single-field-add:__b2_neg_probe__",
                      "expected": "PAYLOAD_SHA_MISMATCH", "actual": ("PAYLOAD_SHA_MISMATCH"
                                                                    if neg_pass else calc),
                      "first_fail": None if neg_pass else "MUTATION_NOT_DETECTED",
                      "verdict": "PASS" if neg_pass else "FAIL"})

    # ---- ToolReadSet handover: rows whose pin is not bound stay typed, never upgraded
    trs_p = sorted(f for f in os.listdir(OPS) if f.startswith("b2_toolreadset_"))
    trs = json.load(open(os.path.join(OPS, trs_p[-1]), encoding="utf-8")) if trs_p else {}
    rows = trs.get("rows") or []
    unbound = [r["unit_id"] for r in rows if not r.get("pin")]
    delta = {"rows_total": len(rows), "rows_with_bound_pin": len(rows) - len(unbound),
             "rows_without_bound_pin": len(unbound),
             "rule": "an unbound pin is recorded as TYPED_MISSING; it is never filled from "
                     "candidate output and never upgraded to a pass"}

    tally = dict(collections.Counter(c["verdict"] for c in cases))
    out = {"schema": "SST.PH01.W0.B2.TQAEP@1",
           "generated_at": now.isoformat(timespec="seconds"),
           "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M", "bid": "B2",
           "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A",
           "fin_order": "DENY",
           "claim_ceiling": "PAYLOAD_INTEGRITY_ONLY",
           "not_claimed": ["Q-row semantic requiredness", "tool availability",
                           "licence/lock state", "B5 tool selection"],
           "spec": {"path": spec_path, "bytes": len(raw), "raw_sha256": got,
                    "expected_sha256": EXPECT_SHA, "pin_match": got == EXPECT_SHA},
           "census": {"units": len(marks), "cases": len(cases),
                      "pos": sum(1 for c in cases if c["polarity"] == "POS"),
                      "neg": sum(1 for c in cases if c["polarity"] == "NEG")},
           "kinds": dict(kinds), "quadrants": {str(k): v for k, v in quads.items()},
           "requiredness_delta": delta,
           "tally": tally,
           "cases": cases}
    p = os.path.join(OPS, f"b2_tqaep_{ts}.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(f"units={len(marks)} cases={len(cases)} POS_ok={pos_ok} tally={tally}")
    print("kinds", dict(kinds))
    print("quadrants", {str(k): v for k, v in quads.items()})
    print("requiredness", delta["rows_total"], "unbound", delta["rows_without_bound_pin"])
    print("receipt", os.path.basename(p), os.path.getsize(p), "B", sha(open(p, "rb").read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
