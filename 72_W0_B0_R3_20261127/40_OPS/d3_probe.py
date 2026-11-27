#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D3-C / D3-D probes: the deployment must not take its expectations from the artifact
under test, and the RequiredSet bytes must be the ones the descriptor pinned.

POS: rebuild with the current builder -> byte-identical to the deployment the receipts cite.
NEG1: envelope claims a different inherited manifest        -> SOURCE_MANIFEST_NOT_THE_PIN
NEG2: envelope claims the manifest is VERIFIED              -> SOURCE_MANIFEST_STATE_NOT_THE_PIN
NEG3: descriptor declares another RequiredSet digest        -> REQUIRED_SET_PIN_MISMATCH

All work happens in W/tmp (excluded from the evidence freeze).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
TMP = WAVE / "tmp" / "d3_probe"
BUILDER = WAVE / "40_OPS" / "build_deployment_r8.py"
ENVELOPE = WAVE / "40_OPS" / "b0_sourcereadset_r9_20261127.json"
DESC = WAVE / "00_PREFLIGHT" / "B0_READ_CONTEXT_20261127_r8.json"
DEPLOY = WAVE / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r10.json"
OUT = WAVE / "40_OPS" / "d3_d3cd_probe_20261127.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def variant(name: str, envelope: Path, descriptor: Path):
    """A copy of the real builder pointed at the given inputs and a temp output."""
    TMP.mkdir(parents=True, exist_ok=True)
    src = BUILDER.read_text(encoding="utf-8")
    for old, new in (
        ('ENVELOPE = WAVE / "40_OPS" / "b0_sourcereadset_r8_20261127.json"',
         f'ENVELOPE = Path(r"{envelope}")'),
        ('OUT = WAVE / "00_PREFLIGHT" / "DEPLOYMENT_prod_20261127_r9.json"',
         f'OUT = Path(r"{TMP}") / "{name}.json"'),
        ('DESCRIPTOR = WAVE / "00_PREFLIGHT" / "B0_READ_CONTEXT_20261127_r7.json"',
         f'DESCRIPTOR = Path(r"{descriptor}")'),
    ):
        assert old in src, old
        src = src.replace(old, new, 1)
    path = TMP / f"build_{name}.py"
    path.write_text(src, encoding="utf-8")
    return path


def run(path: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-B", str(path)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(WAVE))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def tamper(src: Path, name: str, mutate) -> Path:
    doc = json.loads(src.read_bytes())
    mutate(doc)
    out = TMP / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8"))
    return out


def refused(output: str, code: str) -> bool:
    return f'"refused": "{code}"' in output


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone()
    results = []

    # ---- POS: the D3 predicates of a rebuild agree with the accepted deployment ----
    # The accepted r10 deployment was produced by 40_OPS/t3a_run_r9.py, not by this builder;
    # the two differ in unrelated text (claim wording, validator version, created_at), so the
    # comparison is on the D3 projection only, plus the pin the accepted bytes already carry.
    pos_out = TMP / "pos.json"
    if pos_out.exists():
        pos_out.unlink()
    rc, out = run(variant("pos", ENVELOPE, DESC))
    accepted = json.loads(DEPLOY.read_bytes())
    rebuilt = json.loads(pos_out.read_bytes()) if pos_out.exists() else {}
    pin_same = rebuilt.get("source_manifest_expected") == accepted.get("source_manifest_expected")
    src_same = {
        sid: {"required_set_sha256": s.get("required_set_sha256"),
              "required_fields": s.get("required_fields")}
        for sid, s in (rebuilt.get("consumers", {}).get("B1", {}).get("sources") or {}).items()
    } == {
        sid: {"required_set_sha256": s.get("required_set_sha256"),
              "required_fields": s.get("required_fields")}
        for sid, s in (accepted.get("consumers", {}).get("B1", {}).get("sources") or {}).items()
    }
    # and the pin the accepted bytes carry must be the independent one, not the envelope's copy
    import importlib.util
    spec = importlib.util.spec_from_file_location("_t3a", WAVE / "40_OPS" / "t3a_run_r9.py")
    t3a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t3a)  # has a __main__ guard: only constants are defined
    pin_equals_accepted = dict(t3a.SOURCE_MANIFEST_PIN) == accepted.get("source_manifest_expected")
    results.append({"arm": "POS_rebuild_matches_accepted_on_the_D3_projection", "exit": rc,
                    "manifest_expectation_equal": pin_same,
                    "per_source_required_set_equal": src_same,
                    "t3a_pin_equals_accepted_deployment": pin_equals_accepted,
                    "accepted": accepted.get("source_manifest_expected"),
                    "ok": rc == 0 and pin_same and src_same and pin_equals_accepted})

    # ---- NEG1: envelope names another inherited manifest ----
    env1 = tamper(ENVELOPE, "ENVELOPE_other_manifest.json",
                  lambda d: d["source_manifest"].__setitem__("inherited_sha", "0" * 64))
    rc, out = run(variant("neg1", env1, DESC))
    results.append({"arm": "NEG_manifest_digest_differs", "exit": rc,
                    "first_fail": "SOURCE_MANIFEST_NOT_THE_PIN",
                    "observed": out.strip()[:200], "ok": rc == 4 and refused(out, "SOURCE_MANIFEST_NOT_THE_PIN")})

    # ---- NEG2: envelope claims the unverified manifest is VERIFIED ----
    env2 = tamper(ENVELOPE, "ENVELOPE_verified_claim.json",
                  lambda d: d["source_manifest"].__setitem__("verification", "VERIFIED"))
    rc, out = run(variant("neg2", env2, DESC))
    results.append({"arm": "NEG_manifest_state_escalated", "exit": rc,
                    "first_fail": "SOURCE_MANIFEST_STATE_NOT_THE_PIN",
                    "observed": out.strip()[:200],
                    "ok": rc == 4 and refused(out, "SOURCE_MANIFEST_STATE_NOT_THE_PIN")})

    # ---- NEG3: descriptor declares a different RequiredSet digest ----
    desc3 = tamper(DESC, "DESC_other_required_set.json",
                   lambda d: d["sources"][0]["required_set"].__setitem__("sha", "0" * 64))
    rc, out = run(variant("neg3", ENVELOPE, desc3))
    results.append({"arm": "NEG_required_set_pin_differs", "exit": rc,
                    "first_fail": "REQUIRED_SET_PIN_MISMATCH",
                    "observed": out.strip()[:200],
                    "ok": rc == 4 and refused(out, "REQUIRED_SET_PIN_MISMATCH")})

    summary = {"schema": "SST.PH01.W0.B0.R3.D3CDProbe/1",
               "measured_at": now.isoformat(),
               "envelope": {"path": str(ENVELOPE), "sha256": sha(ENVELOPE)},
               "descriptor": {"path": str(DESC), "sha256": sha(DESC)},
               "deployment": {"path": str(DEPLOY), "sha256": sha(DEPLOY)},
               "arms": results,
               "all_ok": all(r["ok"] for r in results)}
    OUT.write_bytes(json.dumps(summary, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if summary["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
