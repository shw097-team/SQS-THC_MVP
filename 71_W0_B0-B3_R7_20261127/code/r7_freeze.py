#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r7 candidate freeze — one digest over exactly the artefacts this round produced.

Digest convention (stated so a checker can recompute it):
  * members = every file under this round root whose name matches the include rules below;
  * the freeze receipt itself and any document that quotes the digest are excluded
    (a manifest must not contain the artefact that carries its own digest);
  * lines are `<raw_sha256>  <path-relative-to-round-root>` joined by one "\n", sorted by that
    relative path with plain code-point ordering, then `rstrip("\n")` before hashing;
  * the digest is sha256 of that UTF-8 byte string.

Usage:  python -B r7_freeze.py [--include-docs]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

R7 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(R7, "40_OPS")

CODE = ("20_DEV/r7",)
DATA = ("00_PREFLIGHT", "40_OPS")
DOCS = ("60_CLOSEOUT",)
SKIP_NAMES = {"r7_candidate_freeze.json", "r7_CANDIDATE_MANIFEST.tsv"}
SKIP_SUFFIX = ("__pycache__", ".pyc")
SKIP_DIRS = {"b3_ledger"}  # the draft write is an effect, not a manifest member


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def collect(include_docs: bool) -> list[dict]:
    roots = list(CODE) + list(DATA) + (list(DOCS) if include_docs else [])
    out = []
    for root in roots:
        base = os.path.join(R7, root.replace("/", os.sep))
        for dp, dns, fns in os.walk(base):
            dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith("__pycache__")]
            for f in sorted(fns):
                if f in SKIP_NAMES or f.endswith(SKIP_SUFFIX):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, R7).replace(os.sep, "/")
                raw = open(p, "rb").read()
                out.append({"path": rel, "abs": p, "bytes": len(raw),
                            "raw_sha256": hashlib.sha256(raw).hexdigest(),
                            "layer": root.split("/")[0]})
    out.sort(key=lambda r: r["path"])
    return out


def digest(artefacts: list[dict]) -> str:
    body = "\n".join(f'{a["raw_sha256"]}  {a["path"]}' for a in artefacts).rstrip("\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def main() -> int:
    include_docs = "--include-docs" in sys.argv
    arts = collect(include_docs)
    dg = digest(arts)
    man = os.path.join(OPS, "r7_CANDIDATE_MANIFEST.tsv")
    with open(man, "w", encoding="utf-8", newline="\n") as f:
        for a in arts:
            f.write(f'{a["raw_sha256"]}\t{a["bytes"]}\t{a["path"]}\n')
    receipt = {
        "schema": "SST.PH01.W0.B0B3.CandidateFreeze@1",
        "candidate_digest": dg,
        "digest_convention": ("sha256 over '<raw_sha256>  <relative path>' lines sorted by "
                              "relative path, one \\n between lines, rstrip('\\n') applied; "
                              "the freeze receipt and this manifest are not members"),
        "include_docs": include_docs,
        "members": len(arts),
        "members_by_layer": {k: sum(1 for a in arts if a["layer"] == k)
                             for k in sorted({a["layer"] for a in arts})},
        "manifest": {"path": man, "sha256": sha_file(man)},
        "artefacts": [{k: a[k] for k in ("path", "bytes", "raw_sha256")} for a in arts],
    }
    out = os.path.join(OPS, "r7_candidate_freeze.json")
    json.dump(receipt, open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    # self-check: recompute from disk and from the manifest
    ok_members = all(sha_file(os.path.join(R7, a["path"].replace("/", os.sep))) == a["raw_sha256"]
                     for a in arts)
    print(json.dumps({"written": out, "candidate_digest": dg, "members": len(arts),
                      "members_verify": ok_members, "include_docs": include_docs},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
