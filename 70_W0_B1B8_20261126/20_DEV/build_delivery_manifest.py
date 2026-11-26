#!/usr/bin/env python3
"""Build DELIVERY_MANIFEST.json — classify every wave artefact into a real layer.

Layers:
  CODE_AUTHORITATIVE        shipped code (mtime must precede its receipt)
  AUTHORITATIVE_INPUT       preflight receipts that are genuine inputs
  CANDIDATE_NOT_RATIFIED    inputs that close a gap but await owner ratification
  CHECKER_RECORD_IMMUTABLE  separated-checker verdicts (never rewritten)
  CURRENT_RECEIPT           newest receipt of each series
  SUPERSEDED_RECEIPT        older rounds, kept as history
  CURRENT_CLOSEOUT / LASTGOOD_HISTORY / SUPERSEDED_CLOSEOUT
No artefact is promoted here: promotion requires acceptance, which does not exist yet.
"""
from __future__ import annotations
import hashlib, json, os, re, datetime

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # <wave>/20_DEV/this.py -> <wave>


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
            p = os.path.join(root, f)
            files.append(os.path.relpath(p, W).replace(os.sep, "/"))

    pats = {"b1_run": r"^40_OPS/b1_run_", "b1_tqaep": r"^40_OPS/b1_tqaep_",
            "b2_parse": r"^40_OPS/b2_parse_", "b2_trs": r"^40_OPS/b2_toolreadset_",
            "b2_tqaep": r"^40_OPS/b2_tqaep_",
            "b1_closeout": r"^60_CLOSEOUT/.*B1_CLOSEOUT_rev\d+\.md$",
            "b1_handoff": r"^60_CLOSEOUT/.*B1_HANDOFF",
            "b2_closeout": r"^60_CLOSEOUT/.*B2_CLOSEOUT"}
    cur = {}
    for k, pat in pats.items():
        m = sorted(f for f in files if re.search(pat, f))
        cur[k] = m[-1] if m else None

    def classify(f: str) -> str:
        if f.startswith("20_DEV/"):
            return "CODE_AUTHORITATIVE"
        if f.startswith("00_PREFLIGHT/"):
            if "locator_bindings" in f or "source_allowlist" in f:
                return "CANDIDATE_NOT_RATIFIED"
            return "AUTHORITATIVE_INPUT"
        if re.search(r"^40_OPS/b1_checker_round\d+_verdict", f):
            return "CHECKER_RECORD_IMMUTABLE"
        if re.search(r"^60_CLOSEOUT/.*CLOSEOUT_rev1\.md$", f) or re.search(
                r"^60_CLOSEOUT/.*HANDOFF(\.md|_rev1)", f):
            return "LASTGOOD_HISTORY"
        if f in (cur["b1_closeout"], cur["b1_handoff"], cur["b2_closeout"]):
            return "CURRENT_CLOSEOUT"
        if f in (cur["b1_run"], cur["b1_tqaep"], cur["b2_parse"], cur["b2_trs"], cur["b2_tqaep"]):
            return "CURRENT_RECEIPT"
        if re.search(r"^40_OPS/(b1_run|b1_tqaep|b2_parse|b2_toolreadset|b2_tqaep)_", f):
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
        "schema": "SST.PH01.W0.B1B8.DELIVERY_MANIFEST@1",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": W,
        "promotion_state": {
            "promoted_to_primary": [],
            "reason": ("no batch has completed acceptance: B1_ACCEPTED is false through checker "
                       "rounds 1-3; B2 TQAEP has executed but holds no separated-checker verdict. "
                       "Promotion without acceptance is not permitted."),
            "candidate_layer_holders": ["00_PREFLIGHT/b1_locator_bindings.json",
                                        "00_PREFLIGHT/b1_source_allowlist.json"],
            "not_pushed": True,
            "why_not_pushed": ("SQS-THC_MVP_Workspace is not a git repository (no .git, no remote); "
                               "the only named remote in the master prompt (SQS-THC_MVP) does not "
                               "exist locally. No credential was exercised."),
            "to_promote_a_batch_requires": [
                "separated checker PASS on a frozen candidate",
                "owner ratification of locator bindings (D-1) and mirror carrier (D-2)",
                "spec-owner resolution or recorded waiver for slot mapping (D-3) and kernel oracle (D-4)",
                "consumer receipt (ReadyAccept)",
                "this manifest entry flipped to PRIMARY with the acceptance receipt sha"],
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
