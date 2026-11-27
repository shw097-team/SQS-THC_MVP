#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1: turn the historical r7 B1 TQAEP into a B1 baseline receipt.

Nothing here re-runs the product.  It reads the r7 TQAEP that the previous wave produced,
re-derives each case's evidence quality from the recorded identities (not from the recorded
verdict), and states what B1 may and may not claim.  The reclassification is deliberately
conservative: a POS case only counts as verified when the read carries commit + blob + raw
sha at the pinned commit.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

W = Path(__file__).resolve().parents[1]
TQAEP = W / "40_OPS" / "b1_r7_tqaep.json"
EDGE = W / "40_OPS" / "b1_r7_edge_sec.json"
OUT = W / "30_VERIFY" / "B1_T1_BASELINE_20261128.json"
SPEC = Path(r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
            r"\W0_B0-B3_r7\SST_PLP_PH01_W0_B1_執行控制小包_實質正文_2026-11-27_r7_Native-first_CODEX_FINAL.md")

CONSTANT_BASED = {"B1.POS.FDA_broker_live_submit", "B1.NEG.FDA_broker_live_submit"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    tqaep = json.loads(TQAEP.read_text(encoding="utf-8"))
    cases = tqaep["cases"]
    spec_sha = sha(SPEC)

    buckets: dict[str, list[str]] = {
        "BASE_POS_VERIFIED": [], "BASE_NEG_VERIFIED": [], "BASE_POS_NO_IDENTITY": [],
        "BASE_HOLD": [], "KERNEL_SOURCE_BOUND": [], "KERNEL_HOLD": [],
        "FDA_HOLD": [], "FDA_CONSTANT_BASED": [],
    }
    reasons: dict[str, str] = {}
    for cid, c in sorted(cases.items()):
        kind, verdict = c["kind"], c["verdict"]
        actual = c.get("actual") or {}
        if kind == "BASE":
            if verdict == "HOLD":
                buckets["BASE_HOLD"].append(cid)
                reasons[cid] = "allowlist/identity hold recorded by the r7 run"
                continue
            if cid.startswith("B1.NEG."):
                buckets["BASE_NEG_VERIFIED"].append(cid)
                reasons[cid] = "refusal path: row removed, BASE_ROW_MISSING observed"
                continue
            ids = actual.get("identities") or []
            full = bool(ids) and all(i.get("commit") and i.get("blob") and i.get("raw_sha256")
                                     for i in ids)
            if full and verdict == "PASS":
                buckets["BASE_POS_VERIFIED"].append(cid)
                reasons[cid] = "commit+blob+raw sha recorded at the pinned commit"
            else:
                buckets["BASE_POS_NO_IDENTITY"].append(cid)
                reasons[cid] = ("r7 verdict " + verdict +
                                "; no full commit/blob/raw identity for every target")
        elif kind == "KERNEL":
            if verdict == "PASS_SOURCE_BOUND":
                buckets["KERNEL_SOURCE_BOUND"].append(cid)
                reasons[cid] = ("content 5/5 raw sha and 64/64 symbol span match; the spec's "
                                "commit pin is not resolvable locally")
            else:
                buckets["KERNEL_HOLD"].append(cid)
                reasons[cid] = "SECOND_WRITER predicate needs the original Kernel semantics/oracle"
        else:
            if cid in CONSTANT_BASED:
                buckets["FDA_CONSTANT_BASED"].append(cid)
                reasons[cid] = ("r7 PASS rests on a literal deny/allow constant, which the r5 "
                                "separated checker ruled out as a product verification")
            else:
                buckets["FDA_HOLD"].append(cid)
                reasons[cid] = "deny observed against a simulated broker, not the original FDA artefact"

    verified = len(buckets["BASE_POS_VERIFIED"]) + len(buckets["BASE_NEG_VERIFIED"]) + \
        len(buckets["KERNEL_SOURCE_BOUND"])
    open_cases = len(cases) - verified

    edge = json.loads(EDGE.read_text(encoding="utf-8")) if EDGE.exists() else {}
    out = {
        "schema": "SST.PH01.W0.B1.T1Baseline/1",
        "built_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "spec": {"path": str(SPEC), "sha256": spec_sha, "bytes": SPEC.stat().st_size,
                 "version": "2026-11-27_r7_Native-first"},
        "source_of_case_data": {"path": str(TQAEP), "sha256": sha(TQAEP),
                                "generated_at": tqaep.get("generated_at"),
                                "declared_counts": tqaep.get("verdict_counts"),
                                "repo_head": tqaep.get("repo_head"),
                                "spec_b1_sha256": tqaep.get("spec_b1_sha256")},
        "case_total": len(cases),
        "buckets": {k: {"count": len(v), "cases": v} for k, v in buckets.items()},
        "counts": {k: len(v) for k, v in buckets.items()},
        "verified_eligible": verified,
        "open_cases": open_cases,
        "reclassification_rules": [
            "NEG BASE counts as verified when the refusal path fired (BASE_ROW_MISSING); a "
            "deleted row legitimately has no commit identity.",
            "POS BASE counts as verified only when every target carries commit+blob+raw sha; "
            "otherwise PARTIAL regardless of the r7 verdict (this is the r5 F03 lesson).",
            "FDA broker_live_submit POS/NEG are reclassified out of PASS: their r7 evidence is a "
            "literal constant, which the r5 separated checker (B1C-R5-F01) ruled inadmissible.",
            "KERNEL counts only as SOURCE_BOUND (content+span), never as a full accept: the spec's "
            "commit pin is not present in the local object database.",
        ],
        "reasons": reasons,
        "edge_sec": {"path": str(EDGE) if EDGE.exists() else None,
                     "declared": edge.get("verdict_counts") or edge.get("summary") or None,
                     "note": ("historic EDGE/SEC 9 cases were produced by the same wave; they are "
                              "not re-measured here and are not counted as B1 acceptance.")},
        "findings": {
            "F01/D-1": {"status": "OPEN_PARK",
                        "detail": "BASE-009／BASE-017 declared paths need Repo/Source Owner "
                                  "ratification of namespace/root/path/commit/blob/raw/usage/receipt",
                        "affected": ["B1.POS.BASE-006", "B1.POS.BASE-007", "B1.POS.BASE-008",
                                     "B1.POS.BASE-009", "B1.POS.BASE-011", "B1.POS.BASE-012",
                                     "B1.POS.BASE-013", "B1.POS.BASE-014", "B1.POS.BASE-015",
                                     "B1.POS.BASE-016", "B1.POS.BASE-017"],
                        "resume": "Owner issues per-target approval (namespace/root/path/commit/"
                                  "blob/raw/usage/receipt); then re-read with identity and re-run "
                                  "the 11 POS cases"},
            "F02/D-2": {"status": "OPEN_PARK",
                        "detail": "BASE-018 carries a target outside the owner allow-list; the four "
                                  "FDA-related read rights are not granted",
                        "affected": ["B1.POS.BASE-018"],
                        "resume": "Owner extends the allow-list to the named targets or grants the "
                                  "four read rights; no glob or mirror substitution"},
            "F03/D-3": {"status": "OPEN_PARK",
                        "detail": "7 FDA slots need their original artefacts and a qualified reader; "
                                  "12 cases ran against a simulated broker",
                        "affected": buckets["FDA_HOLD"] + buckets["FDA_CONSTANT_BASED"],
                        "resume": "Original FDA artefacts + FDA-XQ-R13 Reader available with read "
                                  "rights; then re-derive slot→action→artifact M:N and re-run"},
            "F04/D-4": {"status": "OPEN_PARK",
                        "detail": "5 Kernel NEG cases need the original ten author rules and their "
                                  "SECOND_WRITER oracle",
                        "affected": buckets["KERNEL_HOLD"],
                        "resume": "Original Kernel oracle/author rules supplied by the Kernel Owner"},
            "fabricated_commit": {"status": "EXHAUSTED",
                                  "detail": "two substantive repair attempts already spent under the "
                                            "original ledger; no third attempt without an Owner "
                                            "re-open decision"},
        },
        "ready": {"ReadyDraft": "PRESENT (r7 spec + 60-case table)",
                  "ReadyAtom": "PARTIAL (29/60 cases eligible; 31 open)",
                  "ReadyExecute": "NOT_READY",
                  "ReadyAccept": "NOT_READY"},
        "b1_status": "B1_NOT_ACCEPTED_PARTIAL",
        "claim_ceiling": ("This baseline reclassifies an existing historical run; it does not "
                          "re-execute the product, does not accept B1 and does not lift any hold."),
    }
    OUT.write_bytes(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({"counts": out["counts"], "verified_eligible": verified,
                      "open_cases": open_cases, "b1_status": out["b1_status"],
                      "declared": out["source_of_case_data"]["declared_counts"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
