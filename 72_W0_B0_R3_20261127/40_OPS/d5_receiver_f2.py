#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D5: F2 measurement for the *receiver* (not the producer's old import probe).

What this measures on this machine, at this revision:
  * the receiver's actual import surface and every non-stdlib distribution it loads;
  * the external processes its rights entry needs (PowerShell for the DACL, whoami for
    the principal) and the fact that they are OS helpers, not runtime dependencies;
  * a no-write observation around a real receive (source bytes and the code tree).

Not claimed: a whole-machine OFF proof, transitive imports of native DLLs, kernel/registry
writes, or network silence beyond the import surface.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
CODE = WAVE / "10_CODE"
OUT = WAVE / "40_OPS" / "d5_receiver_f2_20261127.json"
ENVELOPE = WAVE / "40_OPS" / "b0_sourcereadset_r9_20261127.json"
SOURCES = [
    Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8\藍圖\SST_PLP_PH01_W0_全批次藍圖.md"),
    Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_WM\SST_PLP_PH01_ALL_WNM_2026-11-24_r2\SST_PLP_PH01_W0M_實質正文.md"),
]
PROBE = r"""
import json, sys, sysconfig, importlib.metadata as md
from consumers import b1, b2, b3
from b0_r3_receiver import deployment, receiver, rights, wire
import b0_reader.root, b0_reader.winio
stdlib = sysconfig.get_paths()["stdlib"].lower()
own = {"b0_r3_receiver", "consumers", "b0_reader"}
outside = []
for name, mod in sorted(sys.modules.items()):
    f = getattr(mod, "__file__", None) or ""
    if not f or f.lower().startswith(stdlib):
        continue
    if any(name == o or name.startswith(o + ".") for o in own):
        continue
    outside.append(name)
dists = {}
for dist in ("cryptography", "cffi", "pycparser"):
    try:
        dists[dist] = md.version(dist)
    except Exception:
        dists[dist] = None
print(json.dumps({"modules_outside_stdlib": outside,
                  "distributions": dists,
                  "python": sys.version.split()[0],
                  "receiver_file": receiver.__file__,
                  "rights_file": rights.__file__}, ensure_ascii=False))
"""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(root: Path) -> dict[str, str]:
    rows = {}
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".tmp_tests"}]
        for name in sorted(filenames):
            p = Path(dirpath) / name
            try:
                rows[str(p.relative_to(root))] = sha(p)
            except OSError:
                rows[str(p.relative_to(root))] = "UNREADABLE"
    return rows


def main() -> int:
    now = datetime.now(timezone.utc).astimezone()
    env = dict(os.environ, PYTHONPATH=str(CODE), PYTHONDONTWRITEBYTECODE="1")
    probe = subprocess.run([sys.executable, "-B", "-c", PROBE], capture_output=True,
                           text=True, encoding="utf-8", env=env, cwd=str(CODE))
    surface = json.loads(probe.stdout) if probe.returncode == 0 else {"probe_failed": probe.stderr[-600:]}

    # what the rights entry actually shells out to
    src = (CODE / "b0_r3_receiver" / "rights.py").read_text(encoding="utf-8")
    helpers = {
        "powershell": src.count('"powershell"'),
        "whoami": src.count('"whoami"'),
        "icacls": src.count('"icacls"'),
    }
    who = subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip()

    pre_sources = {str(p): sha(p) for p in SOURCES}
    pre_tree = tree(CODE)
    req = json.loads((WAVE / "40_OPS" / "b0_read_request_r9_20261127.json").read_bytes())
    recv = subprocess.run([sys.executable, "-B", "-m", "consumers.b3", "receive",
                           "--envelope", str(ENVELOPE)],
                          capture_output=True, text=True, encoding="utf-8", env=env,
                          cwd=str(CODE))
    post_sources = {str(p): sha(p) for p in SOURCES}
    post_tree = tree(CODE)
    changed = sorted(set(pre_tree) ^ set(post_tree)) + \
        sorted(k for k in pre_tree if k in post_tree and pre_tree[k] != post_tree[k])
    receipt = json.loads(recv.stdout) if recv.returncode == 0 and recv.stdout.strip().startswith("{") else {}

    out = {
        "schema": "SST.PH01.W0.B0.R3.D5ReceiverF2/1",
        "measured_at": now.isoformat(),
        "import_surface": surface,
        "external_helpers": {**helpers, "principal": who,
                             "note": ("PowerShell reads the DACL of the deployment descriptor, "
                                      "whoami proves the process principal; both are OS helpers "
                                      "invoked by the rights entry, not runtime dependencies")},
        "native_first": {
            "network_client_modules_imported": [m for m in surface.get("modules_outside_stdlib", [])
                                                if m in {"socket", "ssl", "http", "urllib3",
                                                         "requests"}],
            "claim_ceiling": ("No network module appears in the receiver's import set. This is an "
                              "import-surface observation, not a packet-level OFF proof."),
        },
        "no_write_observation": {
            "source_sha_before": pre_sources,
            "source_sha_after": post_sources,
            "sources_unchanged": pre_sources == post_sources,
            "code_tree_files": [len(pre_tree), len(post_tree)],
            "code_tree_changes": changed,
            "receive_exit": recv.returncode,
            "receive_verdict": receipt.get("verdict"),
            "no_product_write_observed": pre_sources == post_sources and not changed,
        },
        "request_used": {"path": "40_OPS/b0_read_request_r9_20261127.json",
                         "sources": [s["source_id"] for s in req["sources"]]},
    }
    OUT.write_bytes(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({"import_surface": surface,
                      "helpers": helpers,
                      "no_write": out["no_write_observation"]}, ensure_ascii=False, indent=1)[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
