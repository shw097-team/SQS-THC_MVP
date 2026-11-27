#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the pinned receiver deployment descriptor (prod) and the T1 baseline receipt.

This script is a *preflight measurement*: it does not read the envelope to derive any
expectation.  Every expectation comes from the original B0 descriptor, the original
RequiredSetSpec files and the real source bytes on this host.

Writes (create-only, preimage must be ABSENT):
  00_PREFLIGHT/DEPLOYMENT_prod_20261127.json
  00_PREFLIGHT/T1_BASELINE_20261127.json
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

W = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127")
OLDD = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
K = Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04")
OWNER_WS = Path(r"C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws")
RECEIPT = OWNER_WS / "artifacts" / "OWNER_WINDOW.json"
WINDOW = Path(os.path.expanduser("~/.hgk-owner/window.json"))

DESCRIPTOR = OLDD / "00_PREFLIGHT" / "B0_READ_CONTEXT_2026-11-26.json"
RS_BP = OLDD / "00_PREFLIGHT" / "required_set_req12_read_all_2026-11-25.json"
RS_W0 = OLDD / "00_PREFLIGHT" / "required_set_req12_read_w0m_2026-11-25.json"
ENVELOPE = OLDD / "71_W0_B0-B3_R7_20261127" / "40_OPS" / "b0_current_sourcereadset.json"
R7_RECEIPTS = OLDD / "71_W0_B0-B3_R7_20261127" / "40_OPS" / "r7_consumer_receipts.json"
R7_SELFTEST = OLDD / "71_W0_B0-B3_R7_20261127" / "40_OPS" / "r7_consumer_selftest.json"
NATIVE_OFF = OLDD / "40_OPS" / "native_off_r4.json"
PROMOTION = OLDD / "71_W0_B0-B3_R7_20261127" / "40_OPS" / "PROMOTION_RECORD.json"
SESSION = OLDD / "71_W0_B0-B3_R7_20261127" / "docs" / "SESSION_CLOSEOUT_2026-11-27.md"
R5_CHECKER = OLDD / "30_VERIFY" / "verify_r1_receipt_round5.json"

B0_ENTRY = (K / "SST_PLP_PH01_W0_B0-B8" / "W0_B0-B8_NATIVE_r4" / "W0_B0_NATIVE_r4"
            / "B0_NATIVE_FIRST_2026-11-25_r4_CODEX_FINAL" / "00_唯一交付入口_2026-11-25_r4.md")
B0_BODY = B0_ENTRY.parent / "SST_PLP_PH01_W0_B0_執行控制小包_實質正文_2026-11-25_r4_Native-first_定案.md"
B1_R7 = (K / "SST_PLP_PH01_W0_B0-B8" / "W0_B0-B3_r7"
         / "SST_PLP_PH01_W0_B1_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md")
B2_R7 = B1_R7.parent / "SST_PLP_PH01_W0_B2_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md"
B3_R7 = B1_R7.parent / "SST_PLP_PH01_W0_B3_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md"
R7_ENTRY = B1_R7.parent / "00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md"
PLAN = K / "SST_PLP_PH01_W0_B0-B8" / "SST_PH01_W0_B0_剩餘阻斷定向解阻_必要差額閉合暨正式結案工程_方案.md"
CONTROL = K / "SST_PLP_PH01_W0_B0-B8" / "SST_PH01_W0_B0_HERMES_最小執行控制包.md"

EXPECTED_ANCHORS = {
    "plan": "303484a9f3f74ace4d19287b5cf3674cf3367d4f9ae1f13c1c09d376c3daf27a",
    "b0_entry": "eab6fda836349f4f960bb34f43df348d890e0faece5602610e603cb29148dda9",
    "b0_body": "582a54048d8b63e37be3d803c829a12ffe164be72963f026cea1a1b6183345d9",
    "b1_r7": "28437e1b249291f9a89c54c35c23fa11f515d1803c770d4a65e6b28f394f63f7",
}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(Path(p).read_bytes())


def long_sha(p: Path) -> str:
    """SHA-256 over git-blob style content with CRLF normalised, used only as an
    equivalence marker for text carriers (never as an identity replacement)."""
    return sha_bytes(Path(p).read_bytes().replace(b"\r\n", b"\n"))


def whoami() -> str:
    out = subprocess.run(["whoami"], capture_output=True, text=True, check=True).stdout.strip()
    return out


def physical_lines(raw: bytes) -> list[bytes]:
    """Split keeping terminators, CRLF aware (B0 §04.BYTES convention)."""
    lines, pos = [], 0
    while pos < len(raw):
        nl = raw.find(b"\n", pos)
        cr = raw.find(b"\r", pos)
        if nl == -1 and cr == -1:
            lines.append(raw[pos:])
            break
        if cr != -1 and (nl == -1 or cr < nl):
            end = cr + 2 if raw[cr:cr + 2] == b"\r\n" else cr + 1
            lines.append(raw[pos:end])
        else:
            lines.append(raw[pos:nl + 1])
        pos += len(lines[-1])
    return lines


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    pre = W / "00_PREFLIGHT"
    pre.mkdir(parents=True, exist_ok=True)

    # ---------- anchor measurement (identity, not path) ----------
    anchors = {}
    for key, path in (("plan", PLAN), ("control", CONTROL), ("b0_entry", B0_ENTRY),
                      ("b0_body", B0_BODY), ("b1_r7", B1_R7), ("b2_r7", B2_R7),
                      ("b3_r7", B3_R7), ("r7_entry", R7_ENTRY),
                      ("r5_checker", R5_CHECKER), ("legacy_receiver", W / "10_CODE" / "legacy_reference" / "receiver_r6_20261126.py"),
                      ("legacy_r5_consumers", W / "10_CODE" / "legacy_reference" / "r5_consumers_r7_20261127.py"),
                      ("envelope_r7", ENVELOPE), ("r7_receipts", R7_RECEIPTS),
                      ("r7_selftest", R7_SELFTEST), ("native_off_r4", NATIVE_OFF),
                      ("promotion", PROMOTION), ("session_closeout", SESSION),
                      ("b0_descriptor_r4", OLDD / "00_PREFLIGHT" / "B0_READ_CONTEXT_2026-11-25_r4.json"),
                      ("b0_descriptor_r6", DESCRIPTOR)):
        anchors[key] = {
            "path": str(path),
            "present": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha_file(path) if path.exists() else None,
        }
    for key, want in EXPECTED_ANCHORS.items():
        a = anchors[key]
        a["declared_sha256"] = want
        a["match"] = a["sha256"] == want

    # ---------- real sources, verified from bytes ----------
    descriptor = json.loads(DESCRIPTOR.read_text(encoding="utf-8"))
    sources = {}
    for src in descriptor["sources"]:
        sid = src["source_id"]
        loc = Path(src["locator"])
        raw = loc.read_bytes() if loc.exists() else b""
        rs = json.loads(Path(src["required_set"]["ref"]).read_text(encoding="utf-8"))
        rule = rs["rules"][0]
        a, b = src["required_set"]["span"]
        lines = physical_lines(raw)
        slice_bytes = b"".join(lines[a - 1:b]) if raw else b""
        prefix = rule["prefix"]
        value = None
        for ln in lines[a - 1:b]:
            txt = ln.decode("utf-8")
            if txt.startswith(prefix):
                value = txt[len(prefix):].strip()
                break
        sources[sid] = {
            "locator": str(loc),
            "present": loc.exists(),
            "bytes": len(raw),
            "raw_sha256": sha_bytes(raw),
            "declared_expected_sha": src["expected_sha"],
            "sha_match": sha_bytes(raw) == src["expected_sha"],
            "namespace": src["namespace"],
            "source_version": src["source_version"],
            "requirement_span": [a, b],
            "clause_sha256": sha_bytes(slice_bytes),
            "required_set_ref": src["required_set"]["ref"],
            "required_set_sha256": sha_file(Path(src["required_set"]["ref"])),
            "required_set_declared_sha": src["required_set"]["sha"],
            "required_fields": rs["required_fields"],
            "extraction_rule": rule,
            "extracted_value": value,
            "extracted_value_sha": sha_bytes(value.encode("utf-8")) if value is not None else None,
            "requirement_ref": rs["requirement_ref"],
            "child_id": rs.get("child_id"),
            "original_id": rs.get("original_id"),
            "owner": rs.get("owner"),
            "polarity": rs.get("polarity"),
            "requiredness": rs.get("requiredness"),
        }

    # ---------- live rights state (measured, not inferred) ----------
    receipt_bytes = RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    window = json.loads(WINDOW.read_text(encoding="utf-8")) if WINDOW.exists() else {}
    rights_state = {
        "receipt_ref": str(RECEIPT),
        "receipt_bytes": len(receipt_bytes),
        "receipt_sha256": sha_bytes(receipt_bytes),
        "receipt_window_id": receipt.get("window_id"),
        "receipt_task_id": receipt.get("task_id"),
        "receipt_scope": receipt.get("scope"),
        "receipt_expires_at": receipt.get("expires_at"),
        "receipt_effect_ceiling": receipt.get("effect_class_ceiling"),
        "live_state_ref": str(WINDOW),
        "live_window_id": window.get("window_id"),
        "live_state": window.get("state"),
        "live_expires_at": window.get("expires_at"),
        "live_observed_at": now.isoformat(),
        "live_state_open": window.get("state") == "OPEN",
        "live_same_window": window.get("window_id") == receipt.get("window_id"),
        "owner_public_hex": window.get("owner_public_hex"),
        "os_principal": whoami(),
    }

    # ---------- consumer deployment (each consumer, both requested sources) ----------
    consumer_use = {
        "B1": "B1 REPO/BASE/FDA/ROOTS inbound consumption of the B0 SourceReadSet",
        "B2": "B2 QROWS/HARD/META/RETURN inbound consumption of the B0 SourceReadSet",
        "B3": "B3 JOIN/CHILD/ROUTE inbound consumption of the B0 SourceReadSet",
    }
    consumers = {}
    for cid in ("B1", "B2", "B3"):
        consumers[cid] = {
            "consumer_id": cid,
            "validator_name": f"{cid.lower()}_b0_r3_receiver",
            "validator_version": "b0-r3-receiver/1.0.0",
            "consumer_use": consumer_use[cid],
            "source_ids": sorted(sources),
            "sources": {sid: {
                "source_id": sid,
                "namespace": s["namespace"],
                "source_version": s["source_version"],
                "locator": s["locator"],
                "expected_raw_sha256": s["raw_sha256"],
                "byte_length": s["bytes"],
                "requirement_span": s["requirement_span"],
                "expected_clause_sha256": s["clause_sha256"],
                "required_fields": s["required_fields"],
                "required_set_ref": s["required_set_ref"],
                "required_set_sha256": s["required_set_sha256"],
                "extraction_rule": s["extraction_rule"],
                "expected_value": s["extracted_value"],
                "expected_value_sha256": s["extracted_value_sha"],
                "mandatory": True,
            } for sid, s in sources.items()},
        }

    env = json.loads(ENVELOPE.read_bytes())
    deployment = {
        "schema": "SST.PH01.W0.B0.R3.Deployment/1",
        "deployment_id": "b0-r3-prod-20261127",
        "created_at": now.isoformat(),
        "trust_root_kind": "OWNER_AUTHORED_CONFIG_FILE",
        "subject": "SST/SQS-THC/PH01/E00",
        "original_wave": "P1-W00M",
        "bid": 0,
        "spec_version": "2026-11-25_r4_Native-first",
        "producer_candidate_digest": env["candidate_digest"],
        "producer_candidate_digest_basis": (
            "value declared by the B0 producer freeze in force at 2026-11-27 (envelope "
            "b0_current_sourcereadset.json / PROMOTION_RECORD); pinned here before receive, "
            "never copied from the envelope under test"),
        "scope": env["scope"],
        "scope_purpose": env["scope"]["purpose"],
        "scope_id": env["scope"]["scope_id"],
        "consumer_ids": env["scope"]["consumer_ids"],
        "source_manifest_expected": env["source_manifest"],
        "os_principal": rights_state["os_principal"],
        "owner_public_hex": rights_state["owner_public_hex"],
        "rights": {
            "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
            "scope": ["b0_source_read_authority", "sqs_thc_ph01_e00"],
            "receipt_ref": str(RECEIPT),
            "receipt_sha256": rights_state["receipt_sha256"],
            "receipt_window_id": rights_state["receipt_window_id"],
            "state_ref": str(WINDOW),
            "required_effect_ceiling": "READ_ONLY_PROBE",
            "revocation_state_ref": str(WINDOW) + "#state",
            "allowed_disclosure": ["LOCAL_ONLY", "APPROVED_CONSUMER"],
            "epoch_strategy_allowed": ["PROVIDER_VERSIONED", "LIVE_REVALIDATE"],
        },
        "consumers": consumers,
        "claim_ceiling": (
            "This descriptor binds one consumer deployment to the original B0 wire contract. "
            "It grants no rights of its own: the rights in force are the owner window receipt "
            "and the live window state, both re-verified at receive time."),
    }

    out = pre / "DEPLOYMENT_prod_20261127.json"
    if out.exists():
        print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(out)}))
        return 3
    body = json.dumps(deployment, ensure_ascii=False, indent=1).encode("utf-8")
    with open(out, "xb") as fh:
        fh.write(body)
    readback = sha_file(out)
    if readback != sha_bytes(body):
        print(json.dumps({"refused": "POSTIMAGE_MISMATCH"}))
        return 4

    baseline = {
        "schema": "SST.PH01.W0.B0.R3.T1Baseline/1",
        "generated_at": now.isoformat(),
        "workspace_root": str(W),
        "old_workspace_readonly": str(OLDD),
        "knowledge_root_readonly": str(K),
        "anchors": anchors,
        "sources": sources,
        "rights_state": rights_state,
        "envelope_under_test": {
            "path": str(ENVELOPE), "bytes": len(ENVELOPE.read_bytes()),
            "sha256": sha_file(ENVELOPE),
            "candidate_digest": env["candidate_digest"],
            "entries": [{"source_id": e["source_ref"]["source_id"], "sha": e["sha"],
                          "clause_span": e["clause_span"], "required_fields": e["required_fields"],
                          "observed": sorted(e["observed"]), "missing": e["missing"],
                          "authority_valid_from": e["authority"]["valid_from"],
                          "authority_expires_at": e["authority"]["expires_at"],
                          "authority_usage_evidence_sha": e["authority"]["usage_evidence_sha"]}
                         for e in env["entries"]],
            "errors": env["errors"],
        },
        "deployment": {"path": str(out), "bytes": len(body), "sha256": readback},
        "deltas": {
            "G03_G04_valid_from_offset": "open: r5 used mktime/strptime[:19]; repaired receiver uses aware RFC3339",
            "G05_cross_window_currency": "open: r5 recorded currency without deciding; repaired receiver refuses non-current",
            "G06_authority_truth": "open: r5 checked 14 keys exist; repaired receiver verifies receipt signature + interval",
            "G07_candidate_digest": "open: r5 only required non-empty; repaired receiver exact-compares the pinned freeze",
            "G08_wire_tuple": "open: r5 had no strict parser, no duplicate-key/NaN/type checks, next() first match",
            "G09_caller_locator": "open: r5 opened envelope locator; repaired receiver reads only the trusted mapping",
            "G10_three_consumers": "open: r5 expected one source for all three; repaired receiver pins both sources per consumer",
            "sibling_accounting": "open: r5 refused the whole envelope on any errors[]; repaired receiver splits per source",
        },
    }
    out2 = pre / "T1_BASELINE_20261127.json"
    if out2.exists():
        print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(out2)}))
        return 3
    with open(out2, "xb") as fh:
        fh.write(json.dumps(baseline, ensure_ascii=False, indent=1).encode("utf-8"))

    print(json.dumps({
        "deployment": {"path": str(out), "bytes": len(body), "sha256": readback},
        "baseline": str(out2),
        "anchors_match": {k: v.get("match") for k, v in anchors.items() if "match" in v},
        "sources": {k: {"sha_match": v["sha_match"], "bytes": v["bytes"],
                        "value": v["extracted_value"]} for k, v in sources.items()},
        "rights": {k: rights_state[k] for k in
                   ("receipt_sha256", "receipt_window_id", "live_window_id", "live_state",
                    "live_same_window", "os_principal")},
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
