#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Freeze the B1/B2 r5 product candidate: deterministic manifest + run receipt.

Manifest lines are `relative/POSIX/path<TAB>raw_sha256<TAB>bytes<LF>` sorted by path,
excluding the manifest itself and the entry document that carries its digest.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time

R = r"<LOCAL_ROOT>\71_W0_B0-B3_R7_20261127"
DEV = os.path.join(R, "20_DEV", "b1_r5")
OPS = os.path.join(R, "40_OPS")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    artefacts = []
    for d in (DEV, OPS):
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                continue
            if name.startswith(("b1_r7_candidate_freeze", "b2_r7_candidate_freeze",
                               "b1b2_r7_candidate_freeze", "b1b2_r7_CANDIDATE_MANIFEST")):
                continue
            if not name.endswith((".py", ".json", ".md", ".log")):
                continue
            # r5 scope only: this freeze covers what this task produced, not prior sessions' files
            if os.path.normcase(d) == os.path.normcase(OPS) and "_r7" not in name and "r7_" not in name:
                continue
            artefacts.append((os.path.relpath(p, R).replace(os.sep, "/"), sha(p),
                              os.path.getsize(p)))
    # explicit extras: files that the scope filter above cannot see (sub-directory or no "r5" in the name)
    for rel in ("40_OPS/b3_draft/SourceChildLedger.draft.v2.json",
                "40_OPS/m01_boundary_grep_receipt.json",
                "40_OPS/local_only_register.json",
                "40_OPS/B0_READER_PIN_DELTA.md"):
        p = os.path.join(R, rel.replace("/", os.sep))
        if os.path.isfile(p):
            artefacts.append((rel, sha(p), os.path.getsize(p)))
    artefacts.sort()
    manifest = "".join(f"{p}\t{s}\t{b}\n" for p, s, b in artefacts).encode("utf-8")
    msha = hashlib.sha256(manifest).hexdigest()
    mp = os.path.join(OPS, "b1b2_r7_CANDIDATE_MANIFEST.tsv")
    open(mp, "wb").write(manifest)

    tqaep_b1 = json.load(open(os.path.join(OPS, "b1_r7_tqaep.json"), encoding="utf-8"))
    tqaep_b2 = json.load(open(os.path.join(OPS, "b2_r7_tqaep.json"), encoding="utf-8"))
    edge = json.load(open(os.path.join(OPS, "b1_r7_edge_sec.json"), encoding="utf-8"))
    run = json.load(open(os.path.join(OPS, "b1_r7_run_all.json"), encoding="utf-8"))

    receipt = {
        "schema": "SST.PH01.W0.B1B2.CANDIDATE_FREEZE@5",
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "spec_manifest_sha256": "2e4db2d2c2bd6d52316f7e634587888441b5425b7c68902c00b36ded47960d6c",
        "candidate_manifest": {"path": mp, "sha256": msha, "bytes": len(manifest),
                              "artefacts": len(artefacts)},
        "inputs": {
            "repo_root": "C:\\Projects\\Agent_Workspace\\SQS-THC",
            "repo_head": run["repo"]["local_head"],
            "repo_remote": run["repo"]["remote_url"],
            "carrier_sha256": "463dcf33a668a9daa8f0bbf447c7dacc4c3d602bc53fa7e4866844ffbbc4b3e1",
            "fda_carrier_root": run["trusted_context"]["external_root"],
            "allowlist_sha256": run["trusted_context"]["allowlist_ref"]["sha256"],
            "locators_sha256": run["trusted_context"]["locator_ref"]["sha256"],
        },
        "product_actual": {
            "B1": {"cases": tqaep_b1["case_count"], "verdicts": tqaep_b1["verdict_counts"],
                   "edge_sec": edge["counts"], "effect": run["effect"],
                   "write_set": run["write_set"], "preimage": run["preimage"],
                   "fin_order": run["fin_order"]},
            "B2": {"cases": tqaep_b2["case_count"], "verdicts": tqaep_b2["verdict_counts"],
                   "qrows_verified": tqaep_b2["qrows"]["summary"]["verified"],
                   "receivers": tqaep_b2["receivers"]},
        },
        "runtime": {"python": sys.version.split()[0],
                    "git": subprocess.run(["git", "--version"], capture_output=True)
                            .stdout.decode().strip(),
                    "os_principal": os.environ.get("USERNAME", "")},
    }
    out = os.path.join(OPS, "b1b2_r7_candidate_freeze.json")
    json.dump(receipt, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"manifest": mp, "manifest_sha256": msha, "artefacts": len(artefacts),
                      "receipt": out}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
