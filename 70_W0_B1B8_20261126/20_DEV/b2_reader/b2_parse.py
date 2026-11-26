#!/usr/bin/env python3
"""B2 DEV-1 — spec identity, unit census and payload-pin recomputation.

B2 is the tool/Q-row batch (1465 units / 2930 cases). This module only reads the SPEC and
recomputes independent facts about it; it does not touch the wheel rows' semantics.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, datetime, collections

KBASE = r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
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


def main() -> int:
    raw = open(spec_path, "rb").read()
    got = sha(raw)
    t = raw.decode("utf-8")
    out = {"schema": "SST.PH01.W0.B2.PARSE@1",
           "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "spec": {"path": spec_path, "bytes": len(raw), "raw_sha256": got,
                    "expected_sha256": EXPECT_SHA, "pin_match": got == EXPECT_SHA}}

    # ---- unit census
    marks = [(m.group(1), m.end()) for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t)]
    units, pin_bad, pin_ok = [], [], 0
    for uid, pos in marks:
        i = t.find("```json", pos)
        if i < 0:
            units.append({"unit_id": uid, "error": "no json fence"})
            continue
        j = t.find("```", i + 7)
        body = t[i + 7:j]
        try:
            d = json.loads(body)
        except Exception as e:
            units.append({"unit_id": uid, "error": f"json: {e}"})
            continue
        declared = d.get("payload_sha")
        calc = sha(json.dumps(d.get("source_payload"), ensure_ascii=False,
                              separators=(",", ":")).encode())
        ok = declared == calc
        pin_ok += ok
        if not ok:
            pin_bad.append({"unit_id": uid, "declared": declared, "recomputed": calc})
        units.append({"unit_id": uid, "kind": d.get("kind"),
                      "key": d.get("key") or d.get("tool_key"),
                      "q": d.get("q") or d.get("quadrant"),
                      "requiredness": d.get("requiredness"),
                      "payload_sha_ok": ok})

    out["census"] = {"unit_markers": len(marks), "parsed": len(units),
                     "payload_pin_ok": pin_ok, "payload_pin_failures": pin_bad}
    out["kinds"] = dict(collections.Counter(u.get("kind") for u in units if u.get("kind")))
    out["quadrants"] = dict(collections.Counter(u.get("q") for u in units if u.get("q")))
    out["requiredness"] = dict(collections.Counter(u.get("requiredness") for u in units
                                                   if u.get("requiredness")))

    # ---- case census
    cases = re.findall(r"<!--\s*CASE_BEGIN\s+(\S+)\s*-->", t)
    out["cases"] = {"case_markers": len(cases),
                    "pos": sum(1 for c in cases if ".POS." in c),
                    "neg": sum(1 for c in cases if ".NEG." in c)}

    # ---- declared denominators (must not be inferred from counts)
    for label, pat in (("Q1", r"Q1[\s\S]{0,120}?440"), ("Q2", r"Q2[\s\S]{0,120}?513"),
                       ("Q3", r"Q3[\s\S]{0,120}?378"), ("Q4", r"Q4[\s\S]{0,120}?54")):
        out.setdefault("declared_denominators", {})[label] = bool(re.search(pat, t))

    p = os.path.join(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126",
                     "40_OPS", "b2_parse_" + datetime.datetime.now().strftime("%Y%m%dT%H%M%S") + ".json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump({**out, "units": units}, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"spec pin_match={out['spec']['pin_match']} bytes={out['spec']['bytes']}")
    print(f"unit markers={len(marks)} parsed={len(units)} payload_pin_ok={pin_ok} failures={len(pin_bad)}")
    print("kinds:", out["kinds"])
    print("quadrants:", out["quadrants"])
    print("requiredness:", out["requiredness"])
    print("cases:", out["cases"])
    print("denominators:", out.get("declared_denominators"))
    print(f"receipt {p} {os.path.getsize(p)}B sha256={sha(open(p,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
