#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic parser for the pinned r5 B1/B2 spec documents.

Everything here reads bytes from FINAL_SPEC_MANIFEST.tsv-verified files only and
extracts the machine-readable JSON blocks the spec itself declares inside
<!-- UNIT_BEGIN --> / <!-- R5_PARAMETERS_BEGIN --> / <!-- R5_CASE_PARAMETERS_BEGIN -->.
No LLM interpretation, no author memory: the spec is the oracle.
"""
from __future__ import annotations

import json
import os
import re
import hashlib

W_ROOT = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace"
SPEC_DIR = os.path.join(W_ROOT, "70_W0_B1B8_20261126", "spec_delta_r5", "CODEX_FINAL")
SPEC_B1 = os.path.join(SPEC_DIR,
    "SST_PLP_PH01_W0_B1_執行控制小包_實質正文_2026-11-26_r5_Native-first_CODEX_FINAL.md")
SPEC_B2 = os.path.join(SPEC_DIR,
    "SST_PLP_PH01_W0_B2_執行控制小包_實質正文_2026-11-26_r5_Native-first_CODEX_FINAL.md")
MANIFEST = os.path.join(SPEC_DIR, "FINAL_SPEC_MANIFEST.tsv")


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def verify_manifest() -> dict:
    rows = {}
    for line in open(MANIFEST, encoding="utf-8").read().splitlines():
        if not line.strip():
            continue
        p, sha, size = line.split("\t")
        rows[p] = (sha, int(size))
    checked = {}
    for p, (sha, size) in rows.items():
        fp = os.path.join(SPEC_DIR, p)
        ok = os.path.exists(fp) and sha256_file(fp) == sha and os.path.getsize(fp) == size
        checked[p] = ok
    return {"manifest_verdict": "ALL_MATCH" if all(checked.values()) else "MISMATCH",
            "files": checked}


def _units(text: str) -> dict:
    out = {}
    for uid, body in re.findall(r"<!-- UNIT_BEGIN ([A-Z0-9.]+) -->(.*?)<!-- UNIT_END -->", text, re.S):
        m = re.search(r"```json\s*(\{.*?\})\s*```", body, re.S)
        if not m:
            continue
        d = json.loads(m.group(1))
        out[d["unit_id"]] = d
    return out


def _block(text: str, name: str) -> dict:
    m = re.search(r"<!-- %s_BEGIN -->\s*```json\s*(\{.*?\})\s*```" % name, text, re.S)
    return json.loads(m.group(1)) if m else {}


def load_b1() -> dict:
    text = open(SPEC_B1, encoding="utf-8").read()
    units = _units(text)
    return {
        "path": SPEC_B1, "sha256": sha256_file(SPEC_B1), "bytes": os.path.getsize(SPEC_B1),
        "units": units,
        "params": _block(text, "R5_PARAMETERS"),
        "case_params": _block(text, "R5_CASE_PARAMETERS"),
        "common": _block(text, "COMMON_BY_KIND"),
        "unit_id_set_sha": hashlib.sha256(
            "\n".join(sorted(units)).encode()).hexdigest(),
        "case_id_set_sha": hashlib.sha256(
            "\n".join(sorted(_block(text, "R5_CASE_PARAMETERS"))).encode()).hexdigest(),
    }


def load_b2(units_only: bool = False) -> dict:
    text = open(SPEC_B2, encoding="utf-8").read()
    units = _units(text)
    d = {
        "path": SPEC_B2, "sha256": sha256_file(SPEC_B2), "bytes": os.path.getsize(SPEC_B2),
        "units": units,
        "unit_id_set_sha": hashlib.sha256("\n".join(sorted(units)).encode()).hexdigest(),
        "case_id_set_sha": hashlib.sha256(
            "\n".join(sorted(_block(text, "R5_CASE_PARAMETERS"))).encode()).hexdigest(),
    }
    if not units_only:
        d["params"] = _block(text, "R5_PARAMETERS")
        d["case_params"] = _block(text, "R5_CASE_PARAMETERS")
    return d


if __name__ == "__main__":
    print(json.dumps(verify_manifest(), ensure_ascii=False, indent=1))
    b1 = load_b1()
    print("B1 units", len(b1["units"]), "cases", len(b1["case_params"]))
    print("B1 unit set", b1["unit_id_set_sha"])
    print("B1 case set", b1["case_id_set_sha"])
