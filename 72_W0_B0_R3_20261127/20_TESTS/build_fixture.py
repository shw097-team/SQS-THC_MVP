#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the isolated fixture trust anchor + a valid fixture envelope (algorithm tests).

Fixture content is authored here on purpose: it contains no LOCAL_ONLY source text, so
this directory can be published.  The fixture receipt is signed with a *test* Ed25519 key
that lives beside it; the receiver runs the identical signature/interval/currency code
path for fixture and prod — there is no bypass branch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FX = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127\20_TESTS\fixture")
CANDIDATE = "0" * 63 + "1"
SPEC_VERSION = "2026-11-25_r4_Native-first"
SUBJECT = "SST/SQS-THC/PH01/E00"
WAVE = "P1-W00M"
BID = 0
SCOPE_ID = "FIXTURE-SCOPE-B0-R3"
PURPOSE = "B0 SOURCE_READ under SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH (fixture)"
TASK = "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH"
RIGHTS_SCOPE = ["b0_source_read_authority", "sqs_thc_ph01_e00"]
FAR = 4102444800  # 2100-01-01T00:00:00Z
PREFIX = "- **How／Predicate**："

SOURCE_TEXT = """# FIXTURE｜B0 SourceReadSet reception fixture (authored, not an SST source)

- **Requirement**：FIX-REQ-01 fixture requirement used only by the receiver tests.
- **Owner**：fixture
- **How／Predicate**：READ FROM THE FIXTURE SOURCE ONLY; NO DEV EFFECT.
- **Polarity**：POSITIVE_READ_AND_DEV_DENY
- **Note**：this document exists so the receive path can be exercised without any
  original-domain bytes.

| key | value |
|---|---|
| requirement | FIX-REQ-01 |
| span | 4-6 |
"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write(path: Path, data: bytes) -> None:
    if path.exists():
        path.unlink()
    path.write_bytes(data)


def main() -> int:
    FX.mkdir(parents=True, exist_ok=True)
    src = FX / "source_fixture.md"
    write(src, SOURCE_TEXT.encode("utf-8"))
    raw = src.read_bytes()
    lines = raw.decode("utf-8").split("\n")
    value = None
    for ln in lines[3:6]:
        if ln.startswith(PREFIX):
            value = ln[len(PREFIX):].strip()
    assert value, "fixture label not found"
    clause_span = [4, 6]
    clause_bytes = "\n".join(lines[3:6]) + "\n"

    required_set = {
        "child_id": "FIX-REQ-01::FIXTURE-CHILD",
        "original_id": "FIX-REQ-01",
        "owner": "fixture",
        "polarity": "POSITIVE_READ_AND_DEV_DENY",
        "required_fields": ["read"],
        "required_set_spec_version": "B0RequiredSetSpec/1",
        "requiredness": "FIXTURE_ONLY",
        "requirement_ref": str(src),
        "requirement_sha": sha(raw),
        "requirement_span": clause_span,
        "rules": [{
            "expected_literal": value,
            "field": "read",
            "method": "MD_LABEL",
            "prefix": PREFIX,
            "source_id": "FIXTURE.SOURCE",
            "span": [5, 5],
        }],
    }
    rs_path = FX / "required_set_fixture.json"
    write(rs_path, json.dumps(required_set, ensure_ascii=False, indent=1).encode("utf-8"))

    # ---- test-only key pair ----
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    kp_path = FX / "TEST_ONLY_keypair.json"
    if kp_path.exists():
        kp = json.loads(kp_path.read_text(encoding="utf-8"))
        priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(kp["private_hex"]))
    else:
        priv = Ed25519PrivateKey.generate()
        kp = {
            "label": "TEST_ONLY_FIXTURE_KEY — signs fixture receipts only, never an owner decision",
            "private_hex": priv.private_bytes(serialization.Encoding.Raw,
                                              serialization.PrivateFormat.Raw,
                                              serialization.NoEncryption()).hex(),
            "public_hex": priv.public_key().public_bytes(serialization.Encoding.Raw,
                                                         serialization.PublicFormat.Raw).hex(),
        }
        write(kp_path, json.dumps(kp, ensure_ascii=False, indent=1).encode("utf-8"))
    pub_hex = kp["public_hex"]

    receipt = {
        "window_id": "FIXTURE-WIN-0001",
        "task_id": TASK,
        "opened_at": "2026-11-27T00:00:00",
        "expires_at": FAR,
        "scope": RIGHTS_SCOPE,
        "max_ops": 10,
        "effect_class_ceiling": "READ_ONLY_PROBE",
        "policy_epoch_at_open": 13,
        "enrollments_sha256_at_open": "0" * 64,
        "owner_fingerprint": "fixture-fingerprint",
    }
    receipt["owner_signature_hex"] = priv.sign(canon(receipt)).hex()
    receipt["alg"] = "ed25519"
    receipt["claim_ceiling"] = "FIXTURE ONLY: signed by a test key, confers no owner authority"
    rc_path = FX / "receipt.json"
    write(rc_path, json.dumps(receipt, ensure_ascii=False, indent=1).encode("utf-8"))

    window = {
        "schema": "OwnerSigningWindow@1",
        "window_id": "FIXTURE-WIN-0001",
        "task_id": TASK,
        "scope": RIGHTS_SCOPE,
        "opened_at": "2026-11-27T00:00:00",
        "expires_at": FAR,
        "max_ops": 10,
        "ops_used": 0,
        "effect_class_ceiling": "READ_ONLY_PROBE",
        "state": "OPEN",
        "owner_public_hex": pub_hex,
    }
    wn_path = FX / "window.json"
    write(wn_path, json.dumps(window, ensure_ascii=False, indent=1).encode("utf-8"))

    import subprocess
    principal = subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip().lower()

    source_entry = {
        "source_id": "FIXTURE.SOURCE",
        "namespace": "FIXTURE/PH01/B0",
        "source_version": "fixture_r1",
        "locator": str(src),
        "expected_raw_sha256": sha(raw),
        "byte_length": len(raw),
        "requirement_span": clause_span,
        "expected_clause_sha256": sha(clause_bytes.encode("utf-8")),
        "required_fields": ["read"],
        "required_set_ref": str(rs_path),
        "required_set_sha256": sha(rs_path.read_bytes()),
        "extraction_rule": required_set["rules"][0],
        "expected_value": value,
        "expected_value_sha256": sha(value.encode("utf-8")),
        "mandatory": True,
    }
    dep = {
        "schema": "SST.PH01.W0.B0.R3.Deployment/1",
        "deployment_id": "fixture",
        "trust_root_kind": "FIXTURE_TEST_ANCHOR",
        "subject": SUBJECT,
        "original_wave": WAVE,
        "bid": BID,
        "spec_version": SPEC_VERSION,
        "producer_candidate_digest": CANDIDATE,
        "scope": {"scope_id": SCOPE_ID, "source_ids": ["FIXTURE.SOURCE"],
                  "purpose": PURPOSE, "consumer_ids": ["B1", "B2", "B3"]},
        "scope_purpose": PURPOSE,
        "scope_id": SCOPE_ID,
        "consumer_ids": ["B1", "B2", "B3"],
        "source_ids": ["FIXTURE.SOURCE"],
        "os_principal": principal,
        "owner_public_hex": pub_hex,
        "rights": {
            "task_id": TASK,
            "scope": RIGHTS_SCOPE,
            "receipt_ref": str(rc_path),
            "receipt_sha256": sha(rc_path.read_bytes()),
            "receipt_window_id": "FIXTURE-WIN-0001",
            "state_ref": str(wn_path),
            "required_effect_ceiling": "READ_ONLY_PROBE",
            "revocation_state_ref": str(wn_path) + "#state",
            "allowed_disclosure": ["LOCAL_ONLY", "APPROVED_CONSUMER"],
            "epoch_strategy_allowed": ["PROVIDER_VERSIONED", "LIVE_REVALIDATE"],
        },
        "consumers": {
            cid: {
                "consumer_id": cid,
                "validator_name": f"{cid.lower()}_b0_r3_receiver",
                "validator_version": "b0-r3-receiver/1.0.0",
                "consumer_use": f"{cid} fixture inbound consumption",
                "source_ids": ["FIXTURE.SOURCE"],
                "sources": {"FIXTURE.SOURCE": source_entry},
            } for cid in ("B1", "B2", "B3")
        },
        "claim_ceiling": "FIXTURE ONLY — exercises the receive algorithm; confers no product rights",
    }
    dep_path = FX / "DEPLOYMENT_fixture_20261127.json"
    write(dep_path, json.dumps(dep, ensure_ascii=False, indent=1).encode("utf-8"))

    envelope = {
        "wire_version": "SST.B0.SourceReadSet/2",
        "subject": SUBJECT,
        "original_wave": WAVE,
        "bid": BID,
        "spec_version": SPEC_VERSION,
        "candidate_digest": CANDIDATE,
        "scope": dep["scope"],
        "source_manifest": {"inherited_sha": "2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e",
                            "verification": "UNVERIFIED", "evidence_ref": None},
        "entries": [{
            "source_ref": {"source_id": "FIXTURE.SOURCE", "namespace": source_entry["namespace"],
                           "locator": source_entry["locator"],
                           "source_version": source_entry["source_version"]},
            "sha": sha(raw),
            "byte_length": len(raw),
            "encoding": "UTF-8",
            "clause_span": clause_span,
            "clause_sha": sha(clause_bytes.encode("utf-8")),
            "original_id": "FIX-REQ-01",
            "child_id": "FIX-REQ-01::FIXTURE-CHILD",
            "polarity": "POSITIVE_READ_AND_DEV_DENY",
            "requiredness": "FIXTURE_ONLY",
            "owner": "fixture",
            "provenance": {
                "requirement_ref": str(src),
                "requirement_sha": sha(raw),
                "requirement_span": clause_span,
                "rule_ref": str(rs_path),
                "rule_sha": sha(rs_path.read_bytes()),
            },
            "required_fields": ["read"],
            "observed": {"read": {"value": value, "source_sha": sha(raw),
                                   "span": [5, 5],
                                   "value_sha": sha(value.encode("utf-8"))}},
            "missing": [],
            "authority": {
                "source_owner": "fixture",
                "usage_evidence_ref": str(rc_path),
                "usage_evidence_sha": sha(rc_path.read_bytes()),
                "os_principal": principal,
                "verification_method": "fixture-anchor",
                "rights_check_ref": "FIXTURE-WIN-0001",
                "checked_at": "2026-11-27T00:00:00+00:00",
                "valid_from": "2026-11-27T00:00:00+00:00",
                "expires_at": "2099-01-01T00:00:00+00:00",
                "revocation_check_ref": str(wn_path) + "#state",
                "epoch_strategy": "LIVE_REVALIDATE",
                "epoch_provider_ref": None,
                "epoch_evidence_ref": None,
                "disclosure": "LOCAL_ONLY",
            },
            "acl_epoch": None,
            "rights_epoch": None,
        }],
        "errors": [],
        "write_set": [],
        "preimage": "N/A",
        "fin_order": "DENY",
        "extensions": {},
    }
    env_path = FX / "envelope_fixture.json"
    write(env_path, json.dumps(envelope, ensure_ascii=False, indent=1).encode("utf-8"))

    print(json.dumps({
        "fixture_dir": str(FX),
        "deployment_sha256": sha(dep_path.read_bytes()),
        "envelope_sha256": sha(env_path.read_bytes()),
        "source_sha256": sha(raw),
        "value": value,
        "os_principal": principal,
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
