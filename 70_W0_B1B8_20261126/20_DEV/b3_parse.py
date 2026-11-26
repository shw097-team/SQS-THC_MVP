#!/usr/bin/env python3
"""B3 DEV-1 — identity, census and payload-pin recomputation (B3.PARSE@1).

This is the *first* B3 artefact and nothing more. It establishes, from bytes:

* the SPEC raw sha256 identity (a1d759c7…), size, and that no other copy shares it;
* the unit census per kind and the §06 case census, with the case_id ↔ unit join checked in both
  directions (orphan / missing);
* every unit's `payload_sha` recomputed from its own `source_payload`.

Claim ceiling: CENSUS_AND_PIN_ONLY. It does not claim semantic acceptance, requiredness,
clause identity, TQAEP execution or any B3 result product. No B3 draft (SourceChildLedger) is
written by this file.
"""
from __future__ import annotations

import collections
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w0_spec as W  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "40_OPS")


def main() -> int:
    spec = W.load("B3")
    t = spec["text"]
    us = W.units(t)
    cases = W.case_table(t, "B3")

    kinds = collections.Counter(u.get("kind") for u in us if u.get("kind"))
    pin_bad, pin_ok = [], 0
    for u in us:
        if u.get("_error"):
            pin_bad.append({"unit_id": u["unit_id"], "error": u["_error"]})
            continue
        calc = W.sha(json.dumps(u.get("source_payload"), ensure_ascii=False,
                                separators=(",", ":")).encode())
        if calc == u.get("payload_sha"):
            pin_ok += 1
        else:
            pin_bad.append({"unit_id": u["unit_id"], "declared": u.get("payload_sha"),
                            "recomputed": calc})

    unit_cases = set()
    for u in us:
        for c in (u.get("case_ids") or []):
            unit_cases.add(c)
    spec_cases = set(cases)
    pos = sum(1 for c in spec_cases if ".POS." in c)
    neg = sum(1 for c in spec_cases if ".NEG." in c)

    out = {
        "schema": "SST.PH01.W0.B3.PARSE@1",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M", "bid": 3,
        "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A",
        "claim_ceiling": "CENSUS_AND_PIN_ONLY",
        "not_claimed": ["B3 semantics", "requiredness", "clause identity", "TQAEP execution",
                        "SourceChildLedger draft", "any acceptance"],
        "spec": {k: spec[k] for k in ("path", "bytes", "raw_sha256", "expected_sha256",
                                      "pin_match")},
        "census": {"units": len(us), "kinds": dict(kinds),
                   "payload_pin_ok": pin_ok, "payload_pin_failures": pin_bad},
        "cases": {"spec_case_rows": len(spec_cases), "pos": pos, "neg": neg,
                  "unit_case_ids": len(unit_cases),
                  "spec_minus_unit": sorted(spec_cases - unit_cases)[:10],
                  "unit_minus_spec": sorted(unit_cases - spec_cases)[:10]},
    }
    p = os.path.join(OUT, "b3_parse_" + datetime.datetime.now().strftime("%Y%m%dT%H%M%S") + ".json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("spec", spec["raw_sha256"][:16], spec["bytes"], "pin", spec["pin_match"])
    print("units", len(us), dict(kinds))
    print("payload pins ok", pin_ok, "failures", len(pin_bad))
    print("cases", len(spec_cases), "pos", pos, "neg", neg,
          "| spec-unit", len(spec_cases - unit_cases), "| unit-spec", len(unit_cases - spec_cases))
    print(f"receipt {p} {os.path.getsize(p)}B sha256={W.sha(open(p,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
