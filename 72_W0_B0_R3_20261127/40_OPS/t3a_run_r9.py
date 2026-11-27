#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3a: renew the trusted-context descriptor under the live window, re-mint the envelope,
rebuild the receiver deployment against the new receipt, and run the three batch entries.

Every step is create-only; the chain refuses as a whole if the window is not the exact
authorised one.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127")
CODE = WAVE / "10_CODE"
RECEIPT = Path(r"C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws\artifacts\OWNER_WINDOW.json")
WINDOW = Path(os.path.expanduser("~/.hgk-owner/window.json"))
TEMPLATE = WAVE / "00_PREFLIGHT" / "B0_READ_CONTEXT_20261127_r7.json"
REV = os.environ.get("B0_REV", "r8")
_suffix = int(REV.lstrip("r")) + 1
NEW_DESCRIPTOR = WAVE / "00_PREFLIGHT" / f"B0_READ_CONTEXT_20261127_{REV}.json"
NATIVE_ENTRY = WAVE / "20_DEV" / "b0_reader" / "native_entry.py"
OPS = WAVE / "40_OPS"
ENVELOPE = OPS / f"b0_sourcereadset_r{_suffix}_20261127.json"
DEPLOYMENT = WAVE / "00_PREFLIGHT" / f"DEPLOYMENT_prod_20261127_r{_suffix + 1}.json"

# Independent pin for the inherited SourceManifest (provenance: the K documents listed in
# build_deployment_r8.py).  Never taken from the envelope under test; still UNVERIFIED.
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
    "20_DEV/b0_reader/__init__.py", "20_DEV/b0_reader/bytes_.py", "20_DEV/b0_reader/cli.py",
    "20_DEV/b0_reader/controls.py", "20_DEV/b0_reader/errors.py", "20_DEV/b0_reader/fields.py",
    "20_DEV/b0_reader/native_entry.py", "20_DEV/b0_reader/requiredset.py",
    "20_DEV/b0_reader/return_.py", "20_DEV/b0_reader/root.py", "20_DEV/b0_reader/winio.py",
    "20_DEV/tests/test_b0_bytes.py", "20_DEV/tests/test_b0_cases.py",
    "20_DEV/tests/test_b0_fields.py", "20_DEV/tests/test_b0_return.py",
    "20_DEV/tests/test_b0_root.py", "20_DEV/tests/test_contract_probe.py",
    "20_DEV/tests/test_native_off.py", "20_DEV/tests/test_product_read.py",
    "20_DEV/tests/test_windows_security.py", "20_DEV/tests/trust_fixture.py",
)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def candidate_digest(root: Path) -> tuple[str, list[dict]]:
    rows = []
    for rel in sorted(CANDIDATE_PATHS):
        p = root / rel
        raw = p.read_bytes()
        rows.append({"path": rel, "sha256": sha(raw), "bytes": len(raw)})
    body = "".join(f'{r["path"]}\t{r["sha256"]}\t{r["bytes"]}\n' for r in rows).encode()
    return sha(body), rows


def physical_lines(raw: bytes) -> list[bytes]:
    lines, pos = [], 0
    while pos < len(raw):
        nl, cr = raw.find(b"\n", pos), raw.find(b"\r", pos)
        if nl == -1 and cr == -1:
            lines.append(raw[pos:]); break
        if cr != -1 and (nl == -1 or cr < nl):
            end = cr + 2 if raw[cr:cr + 2] == b"\r\n" else cr + 1
            lines.append(raw[pos:end])
        else:
            lines.append(raw[pos:nl + 1])
        pos += len(lines[-1])
    return lines


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    window = json.loads(WINDOW.read_text(encoding="utf-8"))
    receipt_bytes = RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    checks = {
        "window_id": window.get("window_id"),
        "state": window.get("state"),
        "task": window.get("task_id"),
        "scope": window.get("scope"),
        "ceiling": window.get("effect_class_ceiling"),
        "remaining_s": int(window.get("expires_at", 0)) - int(now.timestamp()),
        "receipt_sha256": sha(receipt_bytes),
        "window_matches_receipt": receipt.get("window_id") == window.get("window_id"),
    }
    if not (checks["state"] == "OPEN"
            and checks["task"] == "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH"
            and list(window.get("scope") or []) == ["b0_source_read_authority", "sqs_thc_ph01_e00"]
            and checks["ceiling"] == "READ_ONLY_PROBE"
            and checks["remaining_s"] > 300
            and checks["window_matches_receipt"]):
        print(json.dumps({"refused": "OWNER_WINDOW_NOT_USABLE", "checks": checks},
                         ensure_ascii=False, indent=1))
        return 3

    # ---- 1. renew (or reuse) the descriptor ----
    if NEW_DESCRIPTOR.exists():
        doc = json.loads(NEW_DESCRIPTOR.read_bytes())
        if doc.get("authorization_sha") != checks["receipt_sha256"]:
            print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(NEW_DESCRIPTOR),
                              "detail": "an earlier renewal points at a different receipt"}))
            return 3
        body = NEW_DESCRIPTOR.read_bytes()
        new_sha = sha(body)
        prior = {"path": str(TEMPLATE), "note": "renewed earlier in this session"}
        print(json.dumps({"reused_descriptor": str(NEW_DESCRIPTOR), "sha256": new_sha}))
    else:
        doc = json.loads(TEMPLATE.read_bytes())
        prior = {k: doc[k] for k in ("authorization_sha", "valid_from", "expires_at")}
        doc["authorization_ref"] = str(RECEIPT)
        doc["authorization_sha"] = checks["receipt_sha256"]
        doc["valid_from"] = now.replace(microsecond=0).isoformat()
        doc["expires_at"] = datetime.fromtimestamp(int(window["expires_at"]), timezone.utc) \
            .astimezone().replace(microsecond=0).isoformat()
        doc["authorization_note"] = (
            "Owner 本人以 tkinter 視窗簽發（window_id " + str(window["window_id"])
            + "、ed25519、ceiling READ_ONLY_PROBE、scope b0_source_read_authority,sqs_thc_ph01_e00、max_ops "
            + str(window.get("max_ops")) + "）；口令未經代理，收據僅存於 owner_ws/artifacts。"
            "本檔為 W 內之第二度續期，非新授權。")
        doc["revocation_ref"] = str(WINDOW) + "#state"
        for src in doc["sources"]:
            src["usage_evidence_ref"] = str(RECEIPT)
            src["usage_evidence_sha"] = checks["receipt_sha256"]
            src["revocation_check_ref"] = str(WINDOW) + "#state"
        body = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
        with open(NEW_DESCRIPTOR, "xb") as fh:
            fh.write(body)
        new_sha = sha(NEW_DESCRIPTOR.read_bytes())

    # ---- 2. repin the reader's three descriptor constants (rewritten by name, then counted) ----
    code = NATIVE_ENTRY.read_text(encoding="utf-8")
    code2, n_path = re.subn(
        r"EXPECTED_DESCRIPTOR_PATH = \(\n(?:.*\n)*?\)\n",
        lambda m: ('EXPECTED_DESCRIPTOR_PATH = (\n'
                   '    r"C:\\Projects\\Agent_Workspace\\FHS-5_Workspace"\n'
                   '    r"\\SST_PH01_W0_B0_R3_20261127\\00_PREFLIGHT"\n'
                   '    r"\\' + NEW_DESCRIPTOR.name + '"' + '\n'
                   ')\n'), code, count=1)
    code2, n_sha = re.subn(r'EXPECTED_DESCRIPTOR_SHA = \(\n    "[0-9a-f]{64}"\n\)',
                           lambda m: f'EXPECTED_DESCRIPTOR_SHA = (\n    "{new_sha}"\n)',
                           code2, count=1)
    code2, n_bytes = re.subn(r"EXPECTED_DESCRIPTOR_BYTES = \d+",
                             lambda m: f"EXPECTED_DESCRIPTOR_BYTES = {len(body)}", code2, count=1)
    if (n_path, n_sha, n_bytes) != (1, 1, 1):
        print(json.dumps({"refused": "CONSTANT_REWRITE_FAILED",
                          "counts": [n_path, n_sha, n_bytes]}))
        return 4
    NATIVE_ENTRY.write_text(code2, encoding="utf-8", newline="\n")
    digest, manifest = candidate_digest(WAVE)

    # ---- 3. one real SOURCE_READ ----
    request = {
        "request_version": "B0ReadRequest/2", "subject": "SST/SQS-THC/PH01/E00",
        "original_wave": "P1-W00M", "bid": 0, "effect": "SOURCE_READ", "write_set": [],
        "scope_id": doc["scope"]["scope_id"],
        "sources": [{"source_id": s["source_id"], "expected_sha": s["expected_sha"],
                     "clause_span": s["required_set"]["span"]} for s in doc["sources"]],
    }
    req = json.dumps(request, ensure_ascii=False).encode("utf-8")
    (OPS / "b0_read_request_r9_20261127.json").write_bytes(req)
    env = dict(os.environ, PYTHONPATH=str(WAVE / "20_DEV"), PYTHONDONTWRITEBYTECODE="1")
    if ENVELOPE.exists():
        out = ENVELOPE.read_bytes()
        envdoc = json.loads(out)
        if envdoc.get("candidate_digest") != digest:
            print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(ENVELOPE),
                              "detail": "existing envelope binds another freeze"}))
            return 3
        print(json.dumps({"reused_envelope": str(ENVELOPE), "sha256": sha(out)}))
    else:
        proc = subprocess.run([sys.executable, "-B", "-m", "b0_reader.cli", "read",
                               "--request-json", "-"],
                              input=req, cwd=str(WAVE / "20_DEV"), capture_output=True, env=env)
        (OPS / "b0_read_stderr_r9_20261127.txt").write_bytes(proc.stderr)
        if proc.returncode != 0 or not proc.stdout:
            print(json.dumps({"refused": "PRODUCER_REFUSED", "exit": proc.returncode,
                              "stderr": proc.stderr.decode("utf-8", "replace")[-800:]},
                             ensure_ascii=False, indent=1))
            return 5
        out = proc.stdout
        with open(ENVELOPE, "xb") as fh:
            fh.write(out)
        envdoc = json.loads(out)
    freeze_ok = envdoc.get("candidate_digest") == digest

    # ---- 4. rebuild the receiver deployment against the new receipt ----
    env_manifest = envdoc.get("source_manifest") or {}
    if env_manifest.get("inherited_sha") != SOURCE_MANIFEST_PIN["inherited_sha"] or             env_manifest.get("verification") != SOURCE_MANIFEST_PIN["verification"]:
        print(json.dumps({"refused": "SOURCE_MANIFEST_NOT_THE_PIN",
                          "envelope": env_manifest, "pin": SOURCE_MANIFEST_PIN},
                         ensure_ascii=False, indent=1))
        return 4

    sources = {}
    for src in doc["sources"]:
        loc = Path(src["locator"])
        raw = loc.read_bytes()
        rs_bytes = Path(src["required_set"]["ref"]).read_bytes()
        if sha(rs_bytes) != src["required_set"]["sha"]:
            print(json.dumps({"refused": "REQUIRED_SET_PIN_MISMATCH",
                              "source": src["source_id"],
                              "declared": src["required_set"]["sha"],
                              "actual": sha(rs_bytes)}, ensure_ascii=False))
            return 4
        rs = json.loads(rs_bytes.decode("utf-8"))
        rule = rs["rules"][0]
        a, b = src["required_set"]["span"]
        lines = physical_lines(raw)
        clause = b"".join(lines[a - 1:b])
        value = next((ln.decode("utf-8")[len(rule["prefix"]):].strip()
                      for ln in lines[a - 1:b] if ln.decode("utf-8").startswith(rule["prefix"])), None)
        if value is None:
            print(json.dumps({"refused": "RULE_YIELDS_NOTHING", "source": src["source_id"]}))
            return 4
        sources[src["source_id"]] = {
            "source_id": src["source_id"], "namespace": src["namespace"],
            "source_version": src["source_version"], "locator": str(loc),
            "expected_raw_sha256": sha(raw), "byte_length": len(raw),
            "requirement_span": [a, b], "expected_clause_sha256": sha(clause),
            "required_fields": rs["required_fields"],
            "required_set_ref": src["required_set"]["ref"],
            "required_set_sha256": sha(rs_bytes),
            "source_owner": src["source_owner"],
            "usage_evidence_ref": src["usage_evidence_ref"],
            "revocation_check_ref": src["revocation_check_ref"],
            "authorization_valid_from": doc["valid_from"],
            "authorization_expires_at": doc["expires_at"],
            "extraction_rule": rule, "expected_value": value,
            "expected_value_sha256": sha(value.encode("utf-8")), "mandatory": True,
        }
        if sources[src["source_id"]]["expected_raw_sha256"] != src["expected_sha"]:
            print(json.dumps({"refused": "SOURCE_CHANGED_SINCE_PIN", "source": src["source_id"]}))
            return 4
    use = {"B1": "B1 REPO/BASE/FDA/ROOTS inbound consumption of the B0 SourceReadSet",
           "B2": "B2 QROWS/HARD/META/RETURN inbound consumption of the B0 SourceReadSet",
           "B3": "B3 JOIN/CHILD/ROUTE inbound consumption of the B0 SourceReadSet"}
    dep = {
        "schema": "SST.PH01.W0.B0.R3.Deployment/1", "deployment_id": "prod",
        "created_at": now.isoformat(), "trust_root_kind": "OWNER_AUTHORED_CONFIG_FILE",
        "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M", "bid": 0,
        "spec_version": "2026-11-25_r4_Native-first",
        "producer_candidate_digest": digest,
        "producer_candidate_digest_basis": ("recomputed from the relocated producer tree (25-member "
                                            "candidate manifest) before the envelope was read"),
        "producer_candidate_manifest": manifest,
        "producer_descriptor": {"path": str(NEW_DESCRIPTOR), "bytes": len(body), "sha256": new_sha,
                                "supersedes": {"path": str(TEMPLATE), **prior}},
        "scope": doc["scope"], "scope_purpose": doc["scope"]["purpose"],
        "scope_id": doc["scope"]["scope_id"], "consumer_ids": doc["scope"]["consumer_ids"],
        "source_ids": doc["scope"]["source_ids"],
        "source_manifest_expected": dict(SOURCE_MANIFEST_PIN),
        "allowed_roots": sorted({s["allowed_root"] for s in doc["sources"]}),
        "os_principal": subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip().lower(),
        "owner_public_hex": window.get("owner_public_hex"),
        "rights": {
            "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
            "scope": ["b0_source_read_authority", "sqs_thc_ph01_e00"],
            "receipt_ref": str(RECEIPT), "receipt_sha256": checks["receipt_sha256"],
            "receipt_window_id": receipt.get("window_id"), "state_ref": str(WINDOW),
            "required_effect_ceiling": "READ_ONLY_PROBE",
            "revocation_state_ref": str(WINDOW) + "#state",
            "allowed_disclosure": ["LOCAL_ONLY", "APPROVED_CONSUMER"],
            "epoch_strategy_allowed": ["PROVIDER_VERSIONED", "LIVE_REVALIDATE"],
        },
        "consumers": {cid: {"consumer_id": cid, "validator_name": f"{cid.lower()}_b0_r3_receiver",
                            "validator_version": "b0-r3-receiver/1.1.0", "consumer_use": use[cid],
                            "source_ids": sorted(sources), "sources": sources}
                      for cid in ("B1", "B2", "B3")},
        "claim_ceiling": ("Binds one consumer deployment to the original B0 wire contract; grants no "
                          "rights of its own."),
    }
    dep_body = json.dumps(dep, ensure_ascii=False, indent=1).encode("utf-8")
    if DEPLOYMENT.exists():
        print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(DEPLOYMENT)}))
        return 3
    with open(DEPLOYMENT, "xb") as fh:
        fh.write(dep_body)
    summary = {
        "schema": "SST.PH01.W0.B0.R3.T3aRun/1", "ran_at": now.isoformat(),
        "owner_window": checks,
        "descriptor": {"path": str(NEW_DESCRIPTOR), "bytes": len(body), "sha256": new_sha,
                       "supersedes": {"path": str(TEMPLATE), **prior}},
        "envelope": {"path": str(ENVELOPE), "bytes": len(out), "sha256": sha(out),
                     "candidate_digest": envdoc.get("candidate_digest"),
                     "freeze_matches_replica": freeze_ok,
                     "entries": [{"source_id": e["source_ref"]["source_id"], "sha": e["sha"],
                                  "clause_span": e["clause_span"],
                                  "required_fields": e["required_fields"],
                                  "observed": sorted(e["observed"]), "missing": e["missing"],
                                  "authority_valid_from": e["authority"]["valid_from"],
                                  "authority_expires_at": e["authority"]["expires_at"]}
                                 for e in envdoc["entries"]],
                     "write_set": envdoc.get("write_set"), "fin_order": envdoc.get("fin_order"),
                     "errors": envdoc.get("errors")},
        "deployment": {"path": str(DEPLOYMENT), "bytes": len(dep_body), "sha256": sha(dep_body),
                       "receipt_sha256": checks["receipt_sha256"]},
    }
    (OPS / f"t3a_run_{REV}_20261127.json").write_bytes(
        json.dumps(summary, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:3000])
    return 0 if freeze_ok else 6


if __name__ == "__main__":
    raise SystemExit(main())
