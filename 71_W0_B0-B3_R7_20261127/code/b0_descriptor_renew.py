#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Renew the B0 trusted-context descriptor against a live OWNER window.

What this changes, and only this:
  * `authorization_sha` and every `usage_evidence_sha` become the sha256 of the CURRENT
    owner-signed window receipt (`owner_ws/artifacts/OWNER_WINDOW.json`);
  * `valid_from` / `expires_at` become that window's interval (the reader refuses a window
    whose expiry exceeds the descriptor's, so they are equal by construction);
  * `authorization_note` names the new window id.

It does NOT touch the sources, their pinned shas, the required sets or the scope: those are
what the SPEC pinned and re-pinning them would be a different authorisation.

The previous descriptor is archived byte-for-byte before the rewrite; the product constants
that pin the descriptor (`EXPECTED_DESCRIPTOR_SHA`, `EXPECTED_DESCRIPTOR_BYTES`) are updated
and the delta is written to `40_OPS/b0_descriptor_renewal.json`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

W = r"<LOCAL_ROOT>"
R7 = os.path.join(W, "71_W0_B0-B3_R7_20261127")
DESC = os.path.join(W, "00_PREFLIGHT", "B0_READ_CONTEXT_2026-11-26.json")
NATIVE = os.path.join(W, "20_DEV", "b0_reader", "native_entry.py")
WINDOW = os.path.expanduser("~/.hgk-owner/window.json")
RECEIPT = (r"<LOCAL_ROOT>"
           r"\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws\artifacts\OWNER_WINDOW.json")


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def iso(ts: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime(ts))


def main() -> int:
    win = json.load(open(WINDOW, encoding="utf-8"))
    if win.get("state") != "OPEN":
        raise SystemExit("WINDOW_NOT_OPEN")
    if win.get("task_id") != "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH":
        raise SystemExit("WINDOW_TASK_MISMATCH")
    if win.get("effect_class_ceiling") != "READ_ONLY_PROBE":
        raise SystemExit("WINDOW_CEILING_MISMATCH")
    receipt_sha = sha_file(RECEIPT)
    old_raw = open(DESC, "rb").read()
    old = json.loads(old_raw)
    doc = json.loads(old_raw)
    doc["authorization_sha"] = receipt_sha
    doc["valid_from"] = iso(int(win["expires_at"]) - int(win["ttl_hours"]) * 3600)
    doc["expires_at"] = iso(int(win["expires_at"]))
    doc["authorization_note"] = (
        "授權引用為 Owner 於本回合本人以 tkinter 視窗簽發之收據（window_id "
        f"{win['window_id']}、ed25519、ceiling READ_ONLY_PROBE、scope "
        "b0_source_read_authority,sqs_thc_ph01_e00、max_ops "
        f"{win['max_ops']}）。口令未經代理；收據存於 owner_ws/artifacts。"
        "本檔為 2026-11-27 續期：僅更新 authorization_sha／usage_evidence_sha／時窗，"
        "來源、pin、required_set 與 scope 未改。")
    for s in doc.get("sources") or []:
        s["usage_evidence_sha"] = receipt_sha
    body = (json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")

    arch = DESC.replace(".json", ".superseded-2026-11-27.json")
    if not os.path.exists(arch):
        with open(arch, "wb") as f:
            f.write(old_raw)
    with open(DESC, "wb") as f:
        f.write(body)
    new_sha, new_bytes = hashlib.sha256(body).hexdigest(), len(body)

    src = open(NATIVE, encoding="utf-8").read()
    src2 = re.sub(r'EXPECTED_DESCRIPTOR_SHA = \(\n    "[0-9a-f]{64}"\n\)',
                  f'EXPECTED_DESCRIPTOR_SHA = (\n    "{new_sha}"\n)', src)
    src2 = re.sub(r'EXPECTED_DESCRIPTOR_BYTES = \d+', f'EXPECTED_DESCRIPTOR_BYTES = {new_bytes}', src2)
    changed = src2 != src
    if changed:
        open(NATIVE, "w", encoding="utf-8", newline="\n").write(src2)

    rec = {
        "schema": "SST.PH01.W0.B0.DescriptorRenewal@1",
        "renewed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "window": {"window_id": win["window_id"], "task_id": win["task_id"],
                   "scope": win["scope"], "ceiling": win["effect_class_ceiling"],
                   "expires_at": win["expires_at"], "max_ops": win["max_ops"],
                   "ops_used": win["ops_used"], "receipt_sha256": receipt_sha},
        "descriptor": {"path": DESC, "superseded_path": arch,
                       "old_sha256": hashlib.sha256(old_raw).hexdigest(),
                       "old_bytes": len(old_raw),
                       "new_sha256": new_sha, "new_bytes": new_bytes},
        "unchanged": ["sources[].expected_sha", "sources[].required_set", "scope", "epoch_strategy"],
        "product_constant_delta": {"file": NATIVE,
                                   "EXPECTED_DESCRIPTOR_SHA": new_sha,
                                   "EXPECTED_DESCRIPTOR_BYTES": new_bytes,
                                   "applied": changed},
    }
    out = os.path.join(R7, "40_OPS", "b0_descriptor_renewal.json")
    json.dump(rec, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"descriptor_sha": new_sha, "bytes": new_bytes,
                      "old_sha": rec["descriptor"]["old_sha256"], "written": out,
                      "constant_applied": changed}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
