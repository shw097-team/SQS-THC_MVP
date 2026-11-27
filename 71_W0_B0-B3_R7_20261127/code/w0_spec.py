#!/usr/bin/env python3
"""Shared W0 SPEC loader for the r7 active bounded SPEC.

Identity is the pinned raw sha256 of the 2026-11-27_r7_Native-first_CODEX_FINAL
bodies (entry `00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md`, A5 mechanical PASS,
A6 adoption 2026-11-27T14:47+08:00). Paths and filenames are never identity:
the upstream tree keeps r4/r5/r6 copies under the same filename pattern.

Differences from the r5 loader, stated explicitly:
  * B1/B2/B3 pins are the r7 digests;
  * hashing is streamed and there is no size pre-filter, because the r7 B2 body
    is 12,552,061 bytes and a 12 MB cut-off silently excluded it.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

KBASE = r"<LOCAL_ROOT>\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
SPEC_VERSION = "2026-11-27_r7_Native-first_CODEX_FINAL"
PINS = {
    "B1": "28437e1b249291f9a89c54c35c23fa11f515d1803c770d4a65e6b28f394f63f7",
    "B2": "acd3282319116142cf55b1bd7d109d1cf08a62907cd05dee8e65eef49554c340",
    "B3": "c1c9c5326a36c1e0e0b00dc1231b39b4f7c21e10a4f9320f2a4dbaabe6125ec5",
    "B4": "15a74095f1f0855c9d3efeb0efb7897564fa175d43e3b70e454358f7981bc5ae",
    "B5": "4c8af9a9fc1c8941d97bf6f3273ba51b4e331446f25788b762ebf33972dea29e",
    "B6": "bab32ae40e0caca101f1fe87c28b5aaf77ce3249dbaecc927cf05f68b59c2f00",
    "B7": "a78f3dc38f410bd9e72b247cc8de0853820b4d397ae4401ee51bd3c3ef2d0a55",
    "B8": "fdd364a767dcfad1f12d56884c779a9b9a592e4b667cadc54ac7ec30fbb3efe8",
}


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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
    hits = [p for p in cands if sha_file(p) == want]
    if not hits:
        raise RuntimeError(f"{batch}_SPEC_ABSENT_BY_SHA: {want} (candidates {cands})")
    # Two byte-identical carriers of one body are one source in two locations, not a
    # collision: every hit equals the pin by construction. The primary is the shallowest
    # path (the entry's own directory); the others are recorded as mirror carriers.
    hits.sort(key=lambda x: (x.count(os.sep), x))
    return hits[0]


def carriers(batch: str) -> list[str]:
    """Every path in KBASE whose bytes equal this batch's r7 pin (byte-identical mirrors)."""
    want = PINS[batch]
    out = []
    for dp, dn, fn in os.walk(KBASE, onerror=lambda e: None, followlinks=False):
        dn[:] = [d for d in dn if d not in {".git", "__pycache__"}]
        for f in fn:
            if f.startswith(f"SST_PLP_PH01_W0_{batch}_") and "實質正文" in f and f.endswith(".md"):
                fp = os.path.join(dp, f)
                if sha_file(fp) == want:
                    out.append(fp)
    return sorted(out)


def load(batch: str) -> dict:
    p = find_spec(batch)
    raw = open(p, "rb").read()
    got = sha(raw)
    return {"path": p, "bytes": len(raw), "raw_sha256": got,
            "expected_sha256": PINS[batch], "pin_match": got == PINS[batch],
            "spec_version": SPEC_VERSION, "text": raw.decode("utf-8")}


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


def payload_sha(obj) -> str:
    return sha(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


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
