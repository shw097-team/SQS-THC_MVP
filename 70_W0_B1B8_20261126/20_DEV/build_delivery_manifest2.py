#!/usr/bin/env python3
"""Build DELIVERY_MANIFEST.json (@2) — classify every wave artefact into a real layer.

@2 changes: freeze records, checker prompts/logs, the B2 v2 receipts and the round-4/5 verdicts are
classified explicitly (the @1 builder left them UNCLASSIFIED or stale), and promotion_state no longer
carries the false "not pushed / workspace is not a git repository" paragraph: this wave root is not a
git repository, but publication runs through W/dist/SQS-THC_MVP against the real remote.

No artefact is promoted here. Promotion requires acceptance, which does not exist.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(p: str):
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)


def main() -> int:
    files = []
    for root, ds, fs in os.walk(W):
        ds[:] = [d for d in ds if d not in ("__pycache__", ".pytest_cache")]
        for f in fs:
            if f.endswith((".pyc", ".pyo")):
                continue
            files.append(os.path.relpath(os.path.join(root, f), W).replace(os.sep, "/"))

    pats = {"b1_run": r"^40_OPS/b1_run_", "b1_tqaep": r"^40_OPS/b1_tqaep_",
            "b1_freeze": r"^40_OPS/b1_candidate_freeze_",
            "b2_parse": r"^40_OPS/b2_parse_", "b2_trs": r"^40_OPS/b2_toolreadset_",
            "b2_tqaep": r"^40_OPS/b2_tqaep_", "b2_freeze": r"^40_OPS/b2_candidate_freeze_",
            "b3_parse": r"^40_OPS/b3_parse_",
            "b1_closeout": r"^60_CLOSEOUT/.*B1_CLOSEOUT_rev\d+\.md$",
            "b1_handoff": r"^60_CLOSEOUT/.*B1_HANDOFF",
            "b2_closeout": r"^60_CLOSEOUT/.*B2_CLOSEOUT",
            "session": r"^60_CLOSEOUT/.*SESSION_CLOSEOUT_HANDOFF.*\.md$"}
    cur = {}
    for k, pat in pats.items():
        m = sorted(f for f in files if re.search(pat, f))
        cur[k] = m[-1] if m else None

    def classify(f: str) -> str:
        if f in ("60_CLOSEOUT/SST_PLP_PH01_W0_CLOSEOUT.md",
                 "60_CLOSEOUT/SST_PLP_PH01_W0_HANDOFF.md",
                 "NEW_SESSION_BOOTSTRAP.md"):
            return "CURRENT_CLOSEOUT"
        if f.startswith("90_EXTERNAL_INPUTS/"):
            return ("MAKER_RECORD" if f.endswith("STATUS.md")
                    else "CANDIDATE_EXTERNAL_UNRATIFIED")
        if f.startswith("20_DEV/"):
            return "CODE_AUTHORITATIVE"
        if f.startswith("00_PREFLIGHT/"):
            if "locator_bindings" in f or "source_allowlist" in f:
                return "CANDIDATE_NOT_RATIFIED"
            return "AUTHORITATIVE_INPUT"
        if re.search(r"^40_OPS/.*checker.*_verdict\.md$", f):
            return "CHECKER_RECORD_IMMUTABLE"
        if re.search(r"^40_OPS/.*(checker.*_prompt\.md|checker.*_run\.log)$", f):
            return "MAKER_RECORD"
        if re.search(r"^40_OPS/.*_gate_probe\.json$", f):
            return "MAKER_RECORD"
        if re.search(r"^40_OPS/.*_candidate_freeze_", f):
            return "FREEZE_RECORD"
        if f == "DELIVERY_MANIFEST.json":
            return "MANIFEST_SELF"
        if re.search(r"^40_OPS/b\d_summary\.json$", f):
            return "DERIVED_SUMMARY"
        if re.search(r"^60_CLOSEOUT/.*_rev1\.md$", f):
            return "LASTGOOD_HISTORY"
        if f in (cur["b1_closeout"], cur["b1_handoff"], cur["b2_closeout"], cur["session"]):
            return "CURRENT_CLOSEOUT"
        if f in (cur["b1_run"], cur["b1_tqaep"], cur["b2_parse"], cur["b2_trs"],
                 cur["b2_tqaep"], cur["b1_freeze"], cur["b2_freeze"], cur["b3_parse"]):
            return "CURRENT_RECEIPT"
        if re.search(r"^40_OPS/(b1_run|b1_tqaep|b2_parse|b2_toolreadset|b2_tqaep|b3_parse|"
                     r"b1_candidate_freeze|b2_candidate_freeze)_", f):
            return "SUPERSEDED_RECEIPT"
        if f.startswith("60_CLOSEOUT/"):
            return "SUPERSEDED_CLOSEOUT"
        return "UNCLASSIFIED"

    ent, layers = [], {}
    for f in sorted(files):
        s, b = sha(os.path.join(W, f))
        lay = classify(f)
        layers[lay] = layers.get(lay, 0) + 1
        ent.append({"path": f, "bytes": b, "raw_sha256": s, "layer": lay,
                    "mtime": datetime.datetime.fromtimestamp(
                        os.path.getmtime(os.path.join(W, f))).astimezone().isoformat(
                        timespec="seconds")})

    man = {
        "schema": "SST.PH01.W0.B1B8.DELIVERY_MANIFEST@2",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": W,
        "promotion_state": {
            "promoted_to_primary": [],
            "reason": ("no batch has completed acceptance. B1: separated checker returns "
                       "B1_ACCEPTED = NO across rounds 4 and 5 (Owner decisions D-1…D-4 outstanding, "
                       "5 kernel NEGs oracle-blocked, 1 scope-gap HOLD). B2: five separated rounds, "
                       "final B2_ACCEPTED = NO — no product execution, 15 HOLDs (9 spec-mutation "
                       "unimplemented, 6 oracle-unbound), parent/carrier not ratified. B3: parse "
                       "only. Promotion without original-domain acceptance is not permitted, and a "
                       "fresh Maker verdict is not acceptance."),
            "promotion_audit_this_session": {
                "items_eligible": [], "items_promoted": [],
                "explanation": ("nothing reached acceptance, so nothing was eligible; no accepted "
                                "object was filed into a discard or candidate layer. The two "
                                "CANDIDATE_NOT_RATIFIED files under 00_PREFLIGHT are locator "
                                "bindings awaiting Owner decision D-1, not accepted artefacts.")},
            "candidate_layer_holders": ["00_PREFLIGHT/b1_locator_bindings.json",
                                        "00_PREFLIGHT/b1_source_allowlist.json"],
            "publish_channel": ("W/dist/SQS-THC_MVP (clone of shw097-team/SQS-THC_MVP); the wave "
                                "root itself is not a git repository"),
            "to_promote_a_batch_requires": [
                "separated checker PASS on a frozen candidate",
                "owner ratification of the three locator bindings (D-1) and the carrier/mirror scope (D-2)",
                "spec-owner resolution or recorded waiver for slot mapping (D-3) and the kernel oracle (D-4)",
                "consumer receipt (ReadyAccept)",
                "this manifest entry flipped to PRIMARY with the acceptance receipt sha"],
        },
        "layer_legend": {
            "CODE_AUTHORITATIVE": "source under 20_DEV (the Maker's executable definition)",
            "CURRENT_RECEIPT": "the receipt the wave currently stands on, per batch",
            "FREEZE_RECORD": "candidate freeze (artefact bytes+sha+candidate_digest)",
            "CHECKER_RECORD_IMMUTABLE": "separated verifier verdict; never rewritten",
            "MAKER_RECORD": "prompt, run log, maker diagnostic",
            "SUPERSEDED_RECEIPT": "earlier receipt, retained on purpose (audit trail)",
            "CURRENT_CLOSEOUT": "the closeout/handoff in force",
            "SUPERSEDED_CLOSEOUT": "earlier closeout revision, retained",
            "CANDIDATE_NOT_RATIFIED": "input the Owner has not ratified (locator bindings)",
            "CANDIDATE_EXTERNAL_UNRATIFIED": "external SPEC candidate from another worker, not adopted",
            "LASTGOOD_HISTORY": "last known-good copy of a batch closeout",
            "AUTHORITATIVE_INPUT": "preflight input that is authoritative as read",
            "DERIVED_SUMMARY": "derived summary, not evidence",
            "MANIFEST_SELF": "this file",
        },
        "current_pointers": cur,
        "layer_counts": layers,
        "artefacts": ent,
    }
    p = os.path.join(W, "DELIVERY_MANIFEST.json")
    json.dump(man, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    s, b = sha(p)
    print("MANIFEST", b, "B", s)
    print("layers", layers)
    print("current", json.dumps(cur, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
