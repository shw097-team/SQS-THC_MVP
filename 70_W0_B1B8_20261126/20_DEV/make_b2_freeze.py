"""Freeze the B2 candidate (round 2): code + receipts, hashed and digest-bound.

Digest rule (identical to B1's, so a checker can recompute either):
    sha256 over the LF-joined "<sha>  <path>" lines of the artefact list SORTED by path,
    with NO trailing LF.

Usage:  python -B 20_DEV/make_b2_freeze.py <round> <receipt_trs> <receipt_tqaep>
"""
import datetime
import hashlib
import json
import os
import sys

WAVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(WAVE, "40_OPS")


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, "rb") as f:
        return sha_bytes(f.read())


def main():
    rnd = sys.argv[1] if len(sys.argv) > 1 else "2"
    trs = sys.argv[2]
    tq = sys.argv[3]
    arts = []
    for rel in ("20_DEV/b2_reader/b2_semantics.py",
                "20_DEV/b2_reader/b2_parse.py",
                "20_DEV/b2_reader/b2_ops_qrows2.py",
                "20_DEV/b2_reader/b2_ops_tqaep2.py",
                "20_DEV/b2_gate_probe.py",
                "20_DEV/b2_reader/b2_ops_qrows.py",   # the pinned old oracle for 72/54
                "40_OPS/b2_gate_probe.json",
                trs, tq):
        p = os.path.join(WAVE, rel)
        arts.append({"path": rel, "bytes": os.path.getsize(p), "raw_sha256": sha_file(p)})
    arts.sort(key=lambda a: a["path"])
    tq_doc = json.load(open(os.path.join(WAVE, tq), encoding="utf-8"))
    claim = tq_doc.get("claim_ceiling")
    not_claimed = (tq_doc.get("claim_scope") or {}).get("not_supported") or []
    digest = sha_bytes("".join(f"{a['raw_sha256']}  {a['path']}\n" for a in arts).rstrip("\n").encode())
    doc = {
        "schema": "SST.W0.B2.CANDIDATE_FREEZE/1",
        "batch": "B2", "subject": "SST/SQS-THC/PH01/E00", "original_wave": "P1-W00M",
        "frozen_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "round": int(rnd),
        "artefacts": arts,
        "candidate_digest": digest,
        "candidate_digest_rule": ("sha256 over the LF-joined '<sha>  <path>' lines of artefacts "
                                  "SORTED by path, no trailing LF (two spaces)"),
        "claim_ceiling": claim,
        "effect": "SOURCE_READ", "write_set": [], "preimage": "N/A", "fin_order": "DENY",
        "supersedes": "40_OPS/b2_candidate_freeze_round4.json",
        "not_claimed": ["B2 acceptance/completion"] + not_claimed,
        "claim_source": "copied from the TQAEP receipt at freeze time (single source, no drift)",
        "neg_holds": {k: v for k, v in (tq_doc.get("tally") or {}).items() if "HOLD" in k},
    }
    p = os.path.join(OUT, f"b2_candidate_freeze_round{rnd}.json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("freeze", os.path.basename(p), os.path.getsize(p), "B")
    print("candidate_digest", digest)
    for a in arts:
        print(f"  {a['raw_sha256'][:16]}  {a['bytes']:>9}  {a['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
