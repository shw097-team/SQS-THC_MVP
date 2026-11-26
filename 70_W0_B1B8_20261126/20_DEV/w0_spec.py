#!/usr/bin/env python3
"""Shared W0 SPEC loader — locate each batch SPEC by raw sha256 identity.

The upstream library was reorganised during this session (batch SPECs moved under
`SST_PLP_PH01_W0_B1-B8_執行控制小包/`) and it also holds older r2/r3 copies under the same filename
pattern. Identity is therefore the pinned sha256, never a path or a name.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

KBASE = r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
PINS = {
    "B1": "13294cada156a2c0beb485bb940a316dd540173273c90dc721570604ca4a3753",
    "B2": "140de5bc1249dbb6e2d199dae336cf3a57741097aaf5cd883a7ec280e9199d3b",
    "B3": "a1d759c7157c4ca8d34acb3f0730b74f653baaa86eb5c3c4302837d0df6deac1",
    "B4": "15a74095f1f0855c9d3efeb0efb7897564fa175d43e3b70e454358f7981bc5ae",
    "B5": "4c8af9a9fc1c8941d97bf6f3273ba51b4e331446f25788b762ebf33972dea29e",
    "B6": "bab32ae40e0caca101f1fe87c28b5aaf77ce3249dbaecc927cf05f68b59c2f00",
    "B7": "a78f3dc38f410bd9e72b247cc8de0853820b4d397ae4401ee51bd3c3ef2d0a55",
    "B8": "fdd364a767dcfad1f12d56884c779a9b9a592e4b667cadc54ac7ec30fbb3efe8",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def find_spec(batch: str) -> str:
    want = PINS[batch]
    cands = []
    for dp, dn, fn in os.walk(KBASE, onerror=lambda e: None, followlinks=False):
        dn[:] = [d for d in dn if d not in {".git", "__pycache__"}]
        for f in fn:
            if f.startswith(f"SST_PLP_PH01_W0_{batch}_") and "實質正文" in f and f.endswith(".md"):
                cands.append(os.path.join(dp, f))
    hits = [p for p in cands
            if os.path.getsize(p) <= 12_000_000 and sha(open(p, "rb").read()) == want]
    if len(hits) != 1:
        raise RuntimeError(f"{batch}_SPEC_NOT_UNIQUE_BY_SHA: {hits} (candidates {cands})")
    return hits[0]


def load(batch: str) -> dict:
    p = find_spec(batch)
    raw = open(p, "rb").read()
    return {"path": p, "bytes": len(raw), "raw_sha256": sha(raw),
            "expected_sha256": PINS[batch], "pin_match": sha(raw) == PINS[batch],
            "text": raw.decode("utf-8")}


def units(t: str) -> list[dict]:
    out = []
    for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t):
        a = t.find("```json", m.end())
        z = t.find("```", a + 7)
        try:
            d = json.loads(t[a + 7:z])
        except Exception as e:
            out.append({"unit_id": m.group(1), "_error": f"json: {e}"})
            continue
        d["_span"] = (m.start(), z)
        out.append(d)
    return out


def case_table(t: str, batch: str) -> dict[str, dict]:
    i, j = t.find("\n## 06"), t.find("\n## 07")
    block = t[i:j if j > 0 else len(t)]
    out = {}
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 8:
            continue
        cid = re.sub(r"<[^>]+>", "", c[0]).strip()
        if not cid.startswith(batch + "."):
            continue
        out[cid] = {"case_id": cid, "key": c[1], "source": c[2], "mutation": c[3],
                    "predicate": c[4], "expected": c[5], "reader": c[6], "op": c[7]}
    return out
