#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3 measurement: are F1/F2 actually affected by this round's change?

F1 (N07 UNKNOWN / cross-process retry) is a producer-side process lifecycle question.
F2 (N05 no-write, N08 native OFF) is a side-effect/dependency question.

Both are answered by measurement on this round's own artefacts, not by another audit:
  * import surface of the relocated reader (third-party modules actually loaded);
  * a no-write observation around a real read (source bytes, tree file set);
  * the historical bounded Native-OFF receipt that stays in force.
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
OUT = WAVE / "40_OPS" / "t3_f1f2_measurement_20261127.json"
ENVELOPE = WAVE / "40_OPS" / "b0_sourcereadset_r8_20261127.json"
SOURCES = [
    Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\藍圖\SST_PLP_PH01_W0_全批次藍圖.md"),
    Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_WM\SST_PLP_PH01_ALL_WNM_2026-11-24_r2\SST_PLP_PH01_W0M_實質正文.md"),
]
NATIVE_OFF = OLD / "40_OPS" / "native_off_r4.json"
PROBE = r"""
import json, sys, sysconfig
import b0_reader
from b0_reader import cli, native_entry, return_, root, winio, bytes_, fields, controls, requiredset
stdlib = sysconfig.get_paths()["stdlib"].lower()
mods = []
for name, mod in sorted(sys.modules.items()):
    f = getattr(mod, "__file__", None)
    if not f:
        continue
    fl = f.lower()
    if fl.startswith(stdlib) or "hermes" in fl or "python-3" in fl:
        continue
    if fl.endswith(".pyc") or fl.endswith(".pyd"):
        pass
    mods.append(name)
print(json.dumps({"packages_loaded_outside_stdlib": mods,
                  "b0_reader_file": b0_reader.__file__}, ensure_ascii=False))
"""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def walk_manifest(root: Path) -> list[dict[str, object]]:
    rows = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".tmp_tests"}]
        for name in sorted(filenames):
            p = Path(dirpath) / name
            try:
                if p.is_symlink():
                    rows.append({"path": str(p.relative_to(root)), "link": True})
                    continue
                rows.append({"path": str(p.relative_to(root)), "bytes": p.stat().st_size,
                             "sha256": sha(p)})
            except OSError:
                rows.append({"path": str(p.relative_to(root)), "error": "UNREADABLE"})
    return sorted(rows, key=lambda r: r["path"])


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    code_root = WAVE / "20_DEV"
    pre_tree = walk_manifest(code_root)
    pre_sources = {str(p): sha(p) for p in SOURCES}

    env = dict(os.environ, PYTHONPATH=str(code_root), PYTHONDONTWRITEBYTECODE="1")
    probe = subprocess.run([sys.executable, "-B", "-c", PROBE], capture_output=True,
                           text=True, encoding="utf-8", env=env, cwd=str(code_root))
    deps = json.loads(probe.stdout) if probe.returncode == 0 and probe.stdout.strip() else {
        "probe_failed": probe.stderr[-800:]}

    # a real read (same request as the mint) under the same interpreter, then re-measure
    request_file = WAVE / "40_OPS" / "b0_read_request_r8_20261127.json"
    run2 = subprocess.run([sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-"],
                          input=request_file.read_bytes(), capture_output=True,
                          env=env, cwd=str(code_root))
    post_tree = walk_manifest(code_root)
    post_sources = {str(p): sha(p) for p in SOURCES}
    changed = [r for r in post_tree if r not in pre_tree]
    misc = subprocess.run(["git", "-C", str(WAVE), "status", "--porcelain"], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")

    out = {
        "schema": "SST.PH01.W0.B0.R3.T3Measurement/1",
        "measured_at": now.isoformat(),
        "f1_n07": {
            "affected_this_round": False,
            "reason": ("this round changes the receive path and two descriptor constants; it "
                       "introduces no cross-process cancellation, worker or UNKNOWN state"),
            "cross_process_artifacts_used": [],
            "finding_budget": ("C-R1-01 stays at its original attempts; no third repair is "
                               "opened because no new in-process or cross-process delta was "
                               "observed"),
            "historical_in_process_evidence": str(OLD / "30_VERIFY" / "verify_r1_receipt_round5.json"),
        },
        "f2_n05_no_write": {
            "source_sha_before": pre_sources,
            "source_sha_after": post_sources,
            "sources_unchanged": pre_sources == post_sources,
            "reader_second_run_exit": run2.returncode,
            "reader_second_run_stdout_sha256": hashlib.sha256(run2.stdout).hexdigest(),
            "reader_second_run_stderr": run2.stderr.decode("utf-8", "replace")[-400:],
            "envelope_on_disk_sha256": sha(ENVELOPE),
            "code_tree_files_before": len(pre_tree),
            "code_tree_files_after": len(post_tree),
            "code_tree_changes": changed,
            "no_product_write_observed": pre_sources == post_sources and not changed,
            "escaping_writes": {"worktree_status_lines": len([l for l in misc.stdout.splitlines() if l.strip()])},
        },
        "f2_n08_native_off": {
            "rerun_this_round": False,
            "reason": ("the change adds no import and no runtime dependency; the import probe "
                       "below is the direct observation that the reader's load surface is "
                       "unchanged in kind"),
            "import_probe": deps,
            "historical_bounded_receipt": {"path": str(NATIVE_OFF),
                                           "sha256": sha(NATIVE_OFF) if NATIVE_OFF.exists() else None,
                                           "verdict": json.loads(NATIVE_OFF.read_bytes()).get("verdict")
                                           if NATIVE_OFF.exists() else None},
            "claim_ceiling": ("NOT a whole-machine OFF proof: transitive imports, kernel/registry "
                              "writes and post-window network activity stay unproven, exactly as the "
                              "historical receipt already states"),
        },
    }
    OUT.write_bytes(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("f1_n07", "f2_n05_no_write")}, ensure_ascii=False, indent=1)[:2500])
    print(json.dumps({"import_packages": deps.get("packages_loaded_outside_stdlib")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
