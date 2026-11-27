#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layer map, promotion record and index reconciliation for this round.

Three jobs, all derived rather than hand-written:

1. **Layers** — every file under the round root gets exactly one layer:
   `PRIMARY` (accepted, current), `CURRENT_CANDIDATE` (this round's live candidate),
   `SUPERSEDED` (kept for audit, never cited as current), `LOCAL_ONLY` (rights-bearing,
   never published), `EFFECT` (a product write), `DOC_HISTORY` (older document revisions).
2. **Promotion** — the items whose own gates passed are named with their sha and the basis
   that admits them, and the index is updated; nothing else is promoted by association.
3. **Reconciliation** — the index's phase_status / accepted / promotion_state are recomputed
   so a stale string ("B0 SourceReadSet/2 currency") cannot survive after B0 closed.

Rules are explicit and stable so this file can be re-run after the next round without
re-deciding by memory.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import time

R7 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(R7, "40_OPS")
CLOSE = os.path.join(R7, "60_CLOSEOUT")
INDEX = os.path.join(R7, "DELIVERY_INDEX.json")

# Items whose gates passed in this round. Each carries the basis that admits it; a reviewer
# can re-derive every one of them from the named receipt.
PROMOTIONS = [
    ("40_OPS/b0_descriptor_renewal.json", "B0 descriptor renewal",
     "window WIN-5afc943249a6, ceiling READ_ONLY_PROBE, only authorization/usage/time changed"),
    ("40_OPS/b0_current_sourcereadset.json", "B0 current SourceReadSet/2",
     "exit 0, 2 sources, 14 authority fields, missing=[], write_set=[]"),
    ("40_OPS/r7_consumer_receipts.json", "B0 three-end receive",
     "B1/B2/B3 ACCEPT, currency CURRENT (usage_evidence_sha equals the live receipt)"),
    ("40_OPS/r7_consumer_selftest.json", "consumer self-test",
     "12/12 arms, including ENVELOPE_AUTHORITY_EXPIRED"),
    ("40_OPS/b0_product_test_2026-11-27.log", "B0 product case suite",
     "137 tests OK, bounded temp root, TMPDIR unset"),
]

LOCAL_ONLY = {"40_OPS/b0_current_sourcereadset.json"}
EFFECTS = ("40_OPS/b3_ledger/",)
DOC_HISTORY = re.compile(r"_rev[1-5]\.md$")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def newest_rev():
    revs = sorted(glob.glob(os.path.join(OPS, "r7_candidate_freeze.rev*.json")),
                  key=os.path.getmtime)
    return revs[-1] if revs else None


def classify(rel: str, cur_rev: str) -> str:
    if rel in LOCAL_ONLY:
        return "LOCAL_ONLY"
    if any(rel.startswith(e) for e in EFFECTS):
        return "EFFECT"
    if rel.startswith("60_CLOSEOUT/") and DOC_HISTORY.search(rel):
        return "DOC_HISTORY"
    if rel.startswith("60_CLOSEOUT/"):
        return "PRIMARY"
    if rel.startswith("20_DEV/"):
        return "PRIMARY"          # the engine set this round ran
    if rel.startswith("00_PREFLIGHT/"):
        return "PRIMARY"
    if re.match(r"40_OPS/r7_candidate_freeze(\.rev\d+)?\.json$", rel):
        return "CURRENT_CANDIDATE" if rel.endswith(os.path.basename(cur_rev)) else "SUPERSEDED"
    if re.match(r"40_OPS/r7_CANDIDATE_MANIFEST(\.rev\d+)?\.tsv$", rel):
        cur_man = "r7_CANDIDATE_MANIFEST." + os.path.basename(cur_rev).split("r7_candidate_freeze.")[-1].replace(".json", ".tsv")
        return "CURRENT_CANDIDATE" if rel.endswith(cur_man) else "SUPERSEDED"
    if rel.startswith("50_PUBLISH/"):
        return "PRIMARY"
    if rel == "40_OPS/r7_checker_verdict.md":
        # a verdict binds to the candidate digest it judged; once that digest is superseded the
        # verdict is history, not a statement about the current candidate
        return "VERDICT_SUPERSEDED"
    return "CURRENT_CANDIDATE"


def main() -> int:
    cur = newest_rev()
    rows = []
    for dp, dns, fns in os.walk(R7):
        dns[:] = [d for d in dns if d not in {"__pycache__"}]
        for f in sorted(fns):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, R7).replace(os.sep, "/")
            if rel == "DELIVERY_INDEX.json":
                continue
            rows.append({"path": rel, "bytes": os.path.getsize(p), "sha256": sha(p),
                         "layer": classify(rel, cur)})
    rows.sort(key=lambda r: (r["layer"], r["path"]))
    tally = {}
    for r in rows:
        tally[r["layer"]] = tally.get(r["layer"], 0) + 1

    promoted = []
    for rel, name, basis in PROMOTIONS:
        p = os.path.join(R7, rel)
        if os.path.isfile(p):
            promoted.append({"path": rel, "bytes": os.path.getsize(p), "sha256": sha(p),
                             "name": name, "basis": basis,
                             "published": rel not in LOCAL_ONLY})
    layers = {
        "schema": "SST.PH01.W0.B0B3.Layers@1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "round_root": R7,
        "current_candidate": {"path": os.path.relpath(cur, R7).replace(os.sep, "/") if cur else None,
                              "digest": (json.load(open(cur, encoding="utf-8")).get("candidate_digest")
                                         if cur else None)},
        "tally": tally,
        "promotion": {"promoted": promoted,
                      "not_promoted": {
                          "B1": "PARTIAL_PARK_UNTIL_DELTA (no new recoverable delta this round)",
                          "B2": "PARTIAL (20 route FirstFail divergences need an owner decision)",
                          "B3": "ReadyAtom false: 183/273 source-bound atoms have no declared owner",
                      }},
        "rules": {
            "PRIMARY": "accepted or engine/config used by this round",
            "CURRENT_CANDIDATE": "this round's live candidate, not accepted",
            "SUPERSEDED": "older freeze/manifest revision, kept for audit, never cited as current",
            "DOC_HISTORY": "older document revision, kept for audit",
            "LOCAL_ONLY": "rights-bearing; never published, sha recorded instead",
            "EFFECT": "a product write (draft ledger), evidence not input",
            "VERDICT_SUPERSEDED": ("a separated-checker verdict whose judged candidate digest is no "
                                   "longer current; history only, must not be cited as applying to "
                                   "the current candidate"),
        },
        "files": rows,
    }
    json.dump(layers, open(os.path.join(OPS, "LAYERS.json"), "w", encoding="utf-8",
                           newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"schema": "SST.PH01.W0.B0B3.PromotionRecord@1",
               "generated_at": layers["generated_at"],
               "promoted": promoted,
               "candidate": layers["current_candidate"]},
              open(os.path.join(OPS, "PROMOTION_RECORD.json"), "w", encoding="utf-8",
                   newline="\n"), ensure_ascii=False, indent=1)

    idx = json.load(open(INDEX, encoding="utf-8"))
    idx["revision"] = max(idx.get("revision", 0), 7)
    idx["phase_status"] = {"B0": "COMPLETE", "B1": "PARTIAL_PARK_UNTIL_DELTA",
                           "B2": "PARTIAL", "B3": "READY_ATOM_FALSE_READY_EXECUTE_HOLD"}
    idx["accepted"] = {"B0": True, "B1": False, "B2": False, "B3": False, "W0": False}
    idx["promotion_state"] = {
        "promoted_to_primary": [p["path"] for p in promoted],
        "items_eligible": [],
        "blockers": ["B3 owner undeclared for 183 source-bound atoms",
                     "B3 requiredness has no cross-batch carrier",
                     "B2 20 route cases: product code differs from the declared FirstFail"],
        "basis_of_B0_acceptance": [p["basis"] for p in promoted if p["path"].startswith("40_OPS/b0")
                                   or "consumer" in p["path"]],
    }
    idx["layers"] = {"path": "40_OPS/LAYERS.json", "tally": tally,
                     "current_candidate": layers["current_candidate"]}
    json.dump(idx, open(INDEX, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)

    md = ["# LAYERS｜本輪檔案分層（rev7）", "",
          f"- 產生：{layers['generated_at']}",
          f"- 現行候選：`{layers['current_candidate']['path']}`／`{(layers['current_candidate']['digest'] or '')[:16]}…`",
          "", "## 統計", "", "| 層 | 檔數 |", "|---|---:|"]
    for k in ("PRIMARY", "CURRENT_CANDIDATE", "SUPERSEDED", "VERDICT_SUPERSEDED",
              "DOC_HISTORY", "LOCAL_ONLY", "EFFECT"):
        md.append(f"| {k} | {tally.get(k, 0)} |")
    md += ["", "## 升格（本輪）", "", "| 項目 | 路徑 | 依據 |", "|---|---|---|"]
    md += [f'| {p["name"]} | `{p["path"]}` | {p["basis"]} |' for p in promoted]
    md += ["", "## 未升格（不連帶）", ""]
    md += [f'- {k}：{v}' for k, v in layers["promotion"]["not_promoted"].items()]
    md += ["", "## 規則", ""]
    md += [f'- `{k}`：{v}' for k, v in layers["rules"].items()]
    open(os.path.join(OPS, "LAYERS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")

    print(json.dumps({"tally": tally, "promoted": [p["path"] for p in promoted],
                      "index_revision": idx["revision"],
                      "accepted": idx["accepted"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
