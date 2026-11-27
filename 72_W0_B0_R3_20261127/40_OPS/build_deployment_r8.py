#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pin the receiver deployment against the r8 producer freeze and the current receipt.

Order matters: the producer freeze is recomputed from the relocated code tree *before*
the envelope is read, and the envelope's declared digest is then required to equal it.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127")
OLD = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
RECEIPT = Path(r"C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws\artifacts\OWNER_WINDOW.json")
WINDOW = Path(os.path.expanduser("~/.hgk-owner/window.json"))
ENVELOPE = WAVE / "40_OPS" / "b0_sourcereadset_r8_20261127.json"
OUT = WAVE / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r9.json"
DESCRIPTOR = WAVE / "00_PREFLIGHT" / "B0_READ_CONTEXT_20261127_r7.json"

# Independent pin for the inherited SourceManifest.  Provenance (not the envelope):
#   K:\...\SST_Native-first_重構\SST_PH01_W0M_第三代重構_藍圖.md
#   K:\...\SST_Native-first_重構\SST_PLP_PH01_W0M_實質正文_2026-11-27_r5_Native-first_GEN3.md
#   K:\...\產品＆施工雙去耦合_第二代\SST Native-first｜W0 B1–B2 最終收斂性結案…報告.md
# The original bytes were never obtained, so the state stays UNVERIFIED: this pins
# *which* inherited manifest the deployment expects, not that the file was verified.
SOURCE_MANIFEST_PIN = {
    "inherited_sha": "2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e",
    "verification": "UNVERIFIED",
    "evidence_ref": None,
}

CANDIDATE_PATHS = (
    "00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json",
    "00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json",
    "00_PREFLIGHT/required_set_req12_read_w0m_2026-11-25.json",
    "20_DEV/RUN_TESTS.cmd",
    "20_DEV/b0_reader/__init__.py",
    "20_DEV/b0_reader/bytes_.py",
    "20_DEV/b0_reader/cli.py",
    "20_DEV/b0_reader/controls.py",
    "20_DEV/b0_reader/errors.py",
    "20_DEV/b0_reader/fields.py",
    "20_DEV/b0_reader/native_entry.py",
    "20_DEV/b0_reader/requiredset.py",
    "20_DEV/b0_reader/return_.py",
    "20_DEV/b0_reader/root.py",
    "20_DEV/b0_reader/winio.py",
    "20_DEV/tests/test_b0_bytes.py",
    "20_DEV/tests/test_b0_cases.py",
    "20_DEV/tests/test_b0_fields.py",
    "20_DEV/tests/test_b0_return.py",
    "20_DEV/tests/test_b0_root.py",
    "20_DEV/tests/test_contract_probe.py",
    "20_DEV/tests/test_native_off.py",
    "20_DEV/tests/test_product_read.py",
    "20_DEV/tests/test_windows_security.py",
    "20_DEV/tests/trust_fixture.py",
)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def physical_lines(raw: bytes) -> list[bytes]:
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
    descriptor = json.loads(DESCRIPTOR.read_bytes())
    receipt_bytes = RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    window = json.loads(WINDOW.read_text(encoding="utf-8"))

    rows = []
    for rel in sorted(CANDIDATE_PATHS):
        p = WAVE / rel.replace("/", "\\")
        raw = p.read_bytes()
        rows.append({"path": rel, "sha256": sha(raw), "bytes": len(raw)})
    digest = sha("".join(f'{r["path"]}\t{r["sha256"]}\t{r["bytes"]}\n' for r in rows).encode("utf-8"))

    env_bytes = ENVELOPE.read_bytes()
    env = json.loads(env_bytes)
    if env["candidate_digest"] != digest:
        print(json.dumps({"refused": "PRODUCER_FREEZE_IDENTITY",
                          "freeze_replica": digest, "envelope_declared": env["candidate_digest"]},
                         ensure_ascii=False, indent=1))
        return 4

    env_manifest = env.get("source_manifest") or {}
    if env_manifest.get("inherited_sha") != SOURCE_MANIFEST_PIN["inherited_sha"]:
        print(json.dumps({"refused": "SOURCE_MANIFEST_NOT_THE_PIN",
                          "envelope_declared": env_manifest.get("inherited_sha"),
                          "independent_pin": SOURCE_MANIFEST_PIN["inherited_sha"]},
                         ensure_ascii=False))
        return 4
    if env_manifest.get("verification") != SOURCE_MANIFEST_PIN["verification"]:
        print(json.dumps({"refused": "SOURCE_MANIFEST_STATE_NOT_THE_PIN",
                          "envelope_declared": env_manifest.get("verification")},
                         ensure_ascii=False))
        return 4

    sources = {}
    for src in descriptor["sources"]:
        loc = Path(src["locator"])
        raw = loc.read_bytes()
        rs = json.loads(Path(src["required_set"]["ref"]).read_text(encoding="utf-8"))
        rule = rs["rules"][0]
        a, b = src["required_set"]["span"]
        clause = b"".join(physical_lines(raw)[a - 1:b])
        value = None
        for ln in physical_lines(raw)[a - 1:b]:
            text = ln.decode("utf-8")
            if text.startswith(rule["prefix"]):
                value = text[len(rule["prefix"]):].strip()
                break
        if value is None:
            print(json.dumps({"refused": "RULE_YIELDS_NOTHING", "source": src["source_id"]}))
            return 4
        rs_bytes = Path(src["required_set"]["ref"]).read_bytes()
        if sha(rs_bytes) != src["required_set"]["sha"]:
            print(json.dumps({"refused": "REQUIRED_SET_PIN_MISMATCH",
                              "source": src["source_id"],
                              "declared": src["required_set"]["sha"],
                              "actual": sha(rs_bytes)}, ensure_ascii=False))
            return 4
        sources[src["source_id"]] = {
            "source_id": src["source_id"],
            "namespace": src["namespace"],
            "source_version": src["source_version"],
            "locator": str(loc),
            "expected_raw_sha256": sha(raw),
            "byte_length": len(raw),
            "requirement_span": [a, b],
            "expected_clause_sha256": sha(clause),
            "required_fields": rs["required_fields"],
            "required_set_ref": src["required_set"]["ref"],
            "required_set_sha256": sha(rs_bytes),
            "extraction_rule": rule,
            "expected_value": value,
            "expected_value_sha256": sha(value.encode("utf-8")),
            "mandatory": True,
        }
        if sources[src["source_id"]]["expected_raw_sha256"] != src["expected_sha"]:
            print(json.dumps({"refused": "SOURCE_CHANGED_SINCE_PIN", "source": src["source_id"]}))
            return 4

    consumer_use = {
        "B1": "B1 REPO/BASE/FDA/ROOTS inbound consumption of the B0 SourceReadSet",
        "B2": "B2 QROWS/HARD/META/RETURN inbound consumption of the B0 SourceReadSet",
        "B3": "B3 JOIN/CHILD/ROUTE inbound consumption of the B0 SourceReadSet",
    }
    consumers = {cid: {
        "consumer_id": cid,
        "validator_name": f"{cid.lower()}_b0_r3_receiver",
        "validator_version": "b0-r3-receiver/1.0.0",
        "consumer_use": consumer_use[cid],
        "source_ids": sorted(sources),
        "sources": sources,
    } for cid in ("B1", "B2", "B3")}

    dep = {
        "schema": "SST.PH01.W0.B0.R3.Deployment/1",
        "deployment_id": "prod",
        "created_at": now.isoformat(),
        "trust_root_kind": "OWNER_AUTHORED_CONFIG_FILE",
        "subject": "SST/SQS-THC/PH01/E00",
        "original_wave": "P1-W00M",
        "bid": 0,
        "spec_version": "2026-11-25_r4_Native-first",
        "producer_candidate_digest": digest,
        "producer_candidate_digest_basis": (
            "recomputed from the relocated producer code tree (25-member B0 candidate "
            "manifest) before the envelope was read; the envelope's own declaration is "
            "then required to equal it"),
        "producer_candidate_manifest": rows,
        "producer_descriptor": {"path": str(DESCRIPTOR), "bytes": len(DESCRIPTOR.read_bytes()),
                                "sha256": sha(DESCRIPTOR.read_bytes())},
        "scope": descriptor["scope"],
        "scope_purpose": descriptor["scope"]["purpose"],
        "scope_id": descriptor["scope"]["scope_id"],
        "consumer_ids": descriptor["scope"]["consumer_ids"],
        "source_ids": descriptor["scope"]["source_ids"],
        "source_manifest_expected": dict(SOURCE_MANIFEST_PIN),
        "allowed_roots": sorted({s["allowed_root"] for s in descriptor["sources"]}),
        "os_principal": window.get("owner_fingerprint") and subprocess.run(
            ["whoami"], capture_output=True, text=True).stdout.strip().lower(),
        "owner_public_hex": window.get("owner_public_hex"),
        "rights": {
            "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
            "scope": ["b0_source_read_authority", "sqs_thc_ph01_e00"],
            "receipt_ref": str(RECEIPT),
            "receipt_sha256": sha(receipt_bytes),
            "receipt_window_id": receipt.get("window_id"),
            "state_ref": str(WINDOW),
            "required_effect_ceiling": "READ_ONLY_PROBE",
            "revocation_state_ref": str(WINDOW) + "#state",
            "allowed_disclosure": ["LOCAL_ONLY", "APPROVED_CONSUMER"],
            "epoch_strategy_allowed": ["PROVIDER_VERSIONED", "LIVE_REVALIDATE"],
        },
        "consumers": consumers,
        "claim_ceiling": ("Binds one consumer deployment to the original B0 wire contract. "
                          "It grants no rights: the owner receipt and the live window are "
                          "re-verified at every receive."),
    }
    body = json.dumps(dep, ensure_ascii=False, indent=1).encode("utf-8")
    if OUT.exists():
        print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(OUT)}))
        return 3
    with open(OUT, "xb") as fh:
        fh.write(body)
    print(json.dumps({
        "deployment": {"path": str(OUT), "bytes": len(body), "sha256": sha(body)},
        "freeze": digest,
        "receipt_sha256": sha(receipt_bytes),
        "window": {"id": window.get("window_id"), "state": window.get("state"),
                   "expires_at": window.get("expires_at")},
        "sources": {k: {"sha": v["expected_raw_sha256"], "value": v["expected_value"]}
                    for k, v in sources.items()},
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
