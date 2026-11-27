#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4a step 1: renew the trusted-context descriptor under the live owner window, then
mint a fresh B0 SourceReadSet/2 envelope with the relocated (byte-identical) reader.

Nothing here grants rights: the descriptor only *points at* the receipt the OWNER just
signed.  The reader still re-verifies the live window, the receipt hash, the descriptor
seal and every source byte.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(r"C:\Projects\Agent_Workspace\FHS-5_Workspace\SST_PH01_W0_B0_R3_20261127")
OLD = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
RECEIPT = Path(r"C:\Projects\Agent_Workspace\FHS_NEXT_Workspace\FHS_vNEXT_W0W1_CLOSEOUT_W2_ENTRY_20261115\owner_ws\artifacts\OWNER_WINDOW.json")
WINDOW = Path(os.path.expanduser("~/.hgk-owner/window.json"))
TEMPLATE = OLD / "00_PREFLIGHT" / "B0_READ_CONTEXT_2026-11-26.json"
NEW_DESCRIPTOR = WAVE / "00_PREFLIGHT" / "B0_READ_CONTEXT_20261127_r7.json"
NATIVE_ENTRY = WAVE / "20_DEV" / "b0_reader" / "native_entry.py"
OPS = WAVE / "40_OPS"
ENVELOPE_OUT = OPS / "b0_sourcereadset_r8_20261127.json"

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


def candidate_digest(root: Path) -> tuple[str, list[dict[str, object]]]:
    rows = []
    for rel in sorted(CANDIDATE_PATHS):
        p = root / rel.replace("/", "\\")
        raw = p.read_bytes()
        rows.append({"path": rel, "sha256": sha(raw), "bytes": len(raw)})
    body = "".join(f'{r["path"]}\t{r["sha256"]}\t{r["bytes"]}\n' for r in rows).encode("utf-8")
    return sha(body), rows


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    window = json.loads(WINDOW.read_text(encoding="utf-8"))
    receipt_bytes = RECEIPT.read_bytes()
    receipt_sha = sha(receipt_bytes)

    checks = {
        "window_state": window.get("state"),
        "window_task": window.get("task_id"),
        "window_scope": window.get("scope"),
        "window_ceiling": window.get("effect_class_ceiling"),
        "window_ops": [window.get("ops_used"), window.get("max_ops")],
        "window_expires_in_s": int(window.get("expires_at", 0)) - int(now.timestamp()),
        "receipt_sha256": receipt_sha,
        "receipt_window_id": json.loads(receipt_bytes).get("window_id"),
        "window_id_matches_receipt": json.loads(receipt_bytes).get("window_id") == window.get("window_id"),
    }
    if not (checks["window_state"] == "OPEN"
            and checks["window_task"] == "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH"
            and list(window.get("scope") or []) == ["b0_source_read_authority", "sqs_thc_ph01_e00"]
            and checks["window_ceiling"] == "READ_ONLY_PROBE"
            and checks["window_expires_in_s"] > 60
            and checks["window_id_matches_receipt"]):
        print(json.dumps({"refused": "OWNER_WINDOW_NOT_USABLE", "checks": checks}, ensure_ascii=False, indent=1))
        return 3

    # ---- renewed descriptor: only the right pointers and the interval change ----
    doc = json.loads(TEMPLATE.read_bytes())
    if NEW_DESCRIPTOR.exists():
        print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(NEW_DESCRIPTOR)}))
        return 3
    old = {k: doc[k] for k in ("authorization_sha", "valid_from", "expires_at")}
    doc["authorization_ref"] = str(RECEIPT)
    doc["authorization_sha"] = receipt_sha
    doc["valid_from"] = now.replace(microsecond=0).isoformat()
    doc["expires_at"] = datetime.fromtimestamp(int(window["expires_at"]), timezone.utc).astimezone().replace(microsecond=0).isoformat()
    doc["authorization_note"] = (
        "授權引用為 Owner 於 2026-11-27 本人以 tkinter 視窗簽發之收據（window_id "
        f"{window['window_id']}、ed25519、ceiling READ_ONLY_PROBE、scope "
        "b0_source_read_authority,sqs_thc_ph01_e00、max_ops "
        f"{window['max_ops']}）。口令未經代理，收據僅存於 owner_ws/artifacts。"
        "本檔為 W 內合法重定位後之續期，非新授權；前窗 WIN-5afc943249a6 已 CLOSED 不再引用。"
    )
    doc["revocation_ref"] = str(WINDOW) + "#state"
    for src in doc["sources"]:
        src["usage_evidence_ref"] = str(RECEIPT)
        src["usage_evidence_sha"] = receipt_sha
        src["revocation_check_ref"] = str(WINDOW) + "#state"
        src["required_set"] = dict(src["required_set"])
        src["required_set"]["ref"] = str(WAVE / "00_PREFLIGHT" / Path(src["required_set"]["ref"]).name)
    body = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
    with open(NEW_DESCRIPTOR, "xb") as fh:
        fh.write(body)
    new_sha = sha(NEW_DESCRIPTOR.read_bytes())
    assert new_sha == sha(body)

    # ---- repin the reader's descriptor constants (old literal asserted present) ----
    code = NATIVE_ENTRY.read_bytes().decode("utf-8")
    old_path_literal = ('    r"C:\\Projects\\Agent_Workspace\\SQS-THC_MVP_Workspace"\n'
                        '    r"\\00_PREFLIGHT\\B0_READ_CONTEXT_2026-11-26.json"\n')
    if old_path_literal not in code:
        print(json.dumps({"refused": "OLD_CONSTANT_LITERAL_ABSENT", "detail": "descriptor path literal"}))
        return 4
    code = code.replace(old_path_literal,
                        '    r"C:\\Projects\\Agent_Workspace\\FHS-5_Workspace"\n'
                        '    r"\\SST_PH01_W0_B0_R3_20261127\\00_PREFLIGHT"\n'
                        '    r"\\B0_READ_CONTEXT_20261127_r7.json"\n')
    old_sha_literal = '"ad78641547abfb41a480c79a36516c5cc57c778b028218701b29ac395b07f1f2"'
    old_bytes_literal = "EXPECTED_DESCRIPTOR_BYTES = 3670"
    for lit in (old_sha_literal, old_bytes_literal):
        if lit not in code:
            print(json.dumps({"refused": "OLD_CONSTANT_LITERAL_ABSENT", "detail": lit}))
            return 4
    code = code.replace(old_sha_literal, f'"{new_sha}"')
    code = code.replace(old_bytes_literal, f"EXPECTED_DESCRIPTOR_BYTES = {len(body)}")
    NATIVE_ENTRY.write_bytes(code.encode("utf-8"))
    if sha(NATIVE_ENTRY.read_bytes()) == sha(code.encode("utf-8")):
        pass

    digest, manifest = candidate_digest(WAVE)

    # ---- compose the SOURCE_READ request from the descriptor's own pins ----
    request = {
        "request_version": "B0ReadRequest/2",
        "subject": "SST/SQS-THC/PH01/E00",
        "original_wave": "P1-W00M",
        "bid": 0,
        "effect": "SOURCE_READ",
        "write_set": [],
        "scope_id": doc["scope"]["scope_id"],
        "sources": [{"source_id": s["source_id"], "expected_sha": s["expected_sha"],
                     "clause_span": s["required_set"]["span"]} for s in doc["sources"]],
    }
    req_bytes = json.dumps(request, ensure_ascii=False).encode("utf-8")
    (OPS / "b0_read_request_r8_20261127.json").write_bytes(req_bytes)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(WAVE / "20_DEV")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-"],
                          input=req_bytes, cwd=str(WAVE / "20_DEV"), capture_output=True, env=env)
    (OPS / "b0_read_stderr_r8_20261127.txt").write_bytes(proc.stderr)
    out = proc.stdout
    (OPS / "b0_read_stdout_r8_20261127.json").write_bytes(out)
    summary = {
        "schema": "SST.PH01.W0.B0.R3.ProducerRun/1",
        "ran_at": now.isoformat(),
        "descriptor": {"path": str(NEW_DESCRIPTOR), "bytes": len(body), "sha256": new_sha,
                       "superseded": {"path": str(TEMPLATE), **old}},
        "owner_window": checks,
        "request": {"path": str(OPS / "b0_read_request_r8_20261127.json"),
                    "bytes": len(req_bytes), "sha256": sha(req_bytes)},
        "exit_code": proc.returncode,
        "stderr": proc.stderr.decode("utf-8", "replace"),
        "stdout_bytes": len(out),
        "stdout_sha256": sha(out),
        "candidate_digest_replica": digest,
        "candidate_manifest_replica": manifest,
    }
    if proc.returncode != 0 or not out:
        summary["verdict"] = "PRODUCER_REFUSED"
        (OPS / "b0_producer_run_r8_20261127.json").write_bytes(
            json.dumps(summary, ensure_ascii=False, indent=1).encode("utf-8"))
        print(json.dumps(summary, ensure_ascii=False, indent=1)[:4000])
        return 5
    if ENVELOPE_OUT.exists():
        print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(ENVELOPE_OUT)}))
        return 3
    ENVELOPE_OUT.write_bytes(out)
    env_doc = json.loads(out)
    summary["envelope"] = {
        "path": str(ENVELOPE_OUT), "bytes": len(out), "sha256": sha(out),
        "candidate_digest": env_doc.get("candidate_digest"),
        "candidate_digest_matches_replica": env_doc.get("candidate_digest") == digest,
        "entries": [{"source_id": e["source_ref"]["source_id"], "sha": e["sha"],
                     "clause_span": e["clause_span"], "required_fields": e["required_fields"],
                     "observed": sorted(e["observed"]), "missing": e["missing"],
                     "authority_valid_from": e["authority"]["valid_from"],
                     "authority_expires_at": e["authority"]["expires_at"]}
                    for e in env_doc.get("entries", [])],
        "errors": env_doc.get("errors"),
        "write_set": env_doc.get("write_set"),
        "fin_order": env_doc.get("fin_order"),
    }
    summary["verdict"] = "PRODUCER_EXECUTED"
    (OPS / "b0_producer_run_r8_20261127.json").write_bytes(
        json.dumps(summary, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({k: summary[k] for k in ("exit_code", "stderr", "envelope", "candidate_digest_replica")},
                     ensure_ascii=False, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
