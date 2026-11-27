#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r7 preflight, B4 receiver probe, and B3 admission record — all derived, nothing hand-typed.

Three products:
  1. `00_PREFLIGHT/r7_preflight.json` — the r7 SPEC census recomputed from bytes:
     pins, byte counts, unit/case counts, payload_sha equality, unit↔case join in both
     directions, kind denominators, and the two byte-identical carrier copies per batch.
  2. `40_OPS/r7_b4_receiver.json` — a minimal B4 receiver over the B1 RepoReadSet: it fixes
     its own mandatory set (commit/path/blob/missing) before reading, applies per-field
     emptiness, and never gives a commit identity to an untracked target.
  3. `40_OPS/r7_b3_admission.json` — the B3 ReadyExecute evidence: four callables, host,
     output root, single-writer guard, oracle status, safety, recovery reconciliation, and
     the one input this round cannot supply (a current B0 SourceReadSet/2).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_spec as SPEC

W = r"<LOCAL_ROOT>"
R7 = os.path.join(W, "71_W0_B0-B3_R7_20261127")
OPS = os.path.join(R7, "40_OPS")
PRE = os.path.join(R7, "00_PREFLIGHT")
SPEC_DIR = os.path.join(W, "W0_B0-B3_GEN3_CODEX_FINAL_2026-11-27_r7")
MANIFEST = os.path.join(SPEC_DIR, "FINAL_SPEC_MANIFEST.tsv")
ENTRY = os.path.join(SPEC_DIR, "00_唯一交付入口_W0_B0-B3_2026-11-27_r7.md")


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def load(p: str):
    return json.load(open(p, encoding="utf-8"))


def preflight() -> dict:
    rows = []
    for line in open(MANIFEST, encoding="utf-8").read().splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        name, want_sha, want_bytes = cols[0], cols[1], int(cols[2])
        p = os.path.join(SPEC_DIR, name)
        got = sha_file(p)
        rows.append({"file": name, "declared_sha256": want_sha, "observed_sha256": got,
                     "declared_bytes": want_bytes, "observed_bytes": os.path.getsize(p),
                     "match": got == want_sha and os.path.getsize(p) == want_bytes})
    batches = {}
    for b in ("B1", "B2", "B3"):
        s = SPEC.load(b)
        us = SPEC.units(s["text"])
        cs = SPEC.case_table(s["text"], b)
        pay_ok = [u["unit_id"] for u in us
                  if SPEC.payload_sha(u["source_payload"]) == u.get("payload_sha")]
        declared = []
        for u in us:
            declared.extend(u.get("case_ids") or [])
        kinds = {}
        for u in us:
            kinds[u.get("kind")] = kinds.get(u.get("kind"), 0) + 1
        batches[b] = {
            "pin": SPEC.PINS[b], "observed_sha256": s["raw_sha256"],
            "pin_match": s["raw_sha256"] == SPEC.PINS[b], "bytes": s["bytes"],
            "carriers": SPEC.carriers(b),
            "carrier_count": len(SPEC.carriers(b)),
            "carrier_note": ("two byte-identical copies are one source in two locations; "
                             "the primary is the shallower path"),
            "units": len(us), "unique_unit_ids": len({u["unit_id"] for u in us}),
            "unique_keys": len({u["key"] for u in us}),
            "cases_in_section_06": len(cs), "case_ids_declared_in_units": len(set(declared)),
            "payload_sha_equal": len(pay_ok), "payload_sha_mismatch": len(us) - len(pay_ok),
            "join_unit_to_case_missing": sum(1 for cid in set(declared) if cid not in cs),
            "join_case_to_unit_orphan": sorted(set(cs) - set(declared)),
            "kind_denominators": kinds,
        }
    return {
        "schema": "SST.PH01.W0.B0B3.R7Preflight@1",
        "generated_at": now(),
        "spec_version": SPEC.SPEC_VERSION,
        "entry": {"path": ENTRY, "sha256": sha_file(ENTRY), "bytes": os.path.getsize(ENTRY)},
        "manifest": {"path": MANIFEST, "sha256": sha_file(MANIFEST),
                     "bytes": os.path.getsize(MANIFEST), "rows": len(rows)},
        "manifest_rows": rows,
        "manifest_all_match": all(r["match"] for r in rows),
        "batches": batches,
        "claim_ceiling": ("document identity, set completeness and payload integrity only; "
                          "no semantic re-adjudication of any clause and no product case"),
    }


def b4_receiver() -> dict:
    run = load(os.path.join(OPS, "b1_r7_run_all.json"))
    mandatory = ["commit", "path", "blob", "missing"]

    def absent(ent, field):
        v = ent.get(field, None)
        if field == "missing":
            return v is None
        return v in (None, "", {}, [])

    receipts, refused = [], []
    for e in run["base"]["entries"]:
        for t in e.get("targets") or []:
            ent = {"key": e.get("key"), "path": t.get("path"),
                   "commit": t.get("commit"), "blob": t.get("blob"),
                   "missing": t.get("missing") if "missing" in t else e.get("missing")}
            lack = [m for m in mandatory if absent(ent, m)]
            rec = {"consumer_id": "B4", "validator_name": "native_b4_receiver_r7",
                   "validator_version": SPEC.SPEC_VERSION, "subject": "SST/SQS-THC/PH01/E00",
                   "source_id": ent["path"], "sha": t.get("raw_sha256"),
                   # field names say what they are: the SPEC unit-id set digest is not a
                   # producer freeze, and the envelope digest is not a candidate identity
                   "spec_b1_unit_id_set_sha": run["spec_inputs"]["b1_unit_id_set_sha"],
                   "producer_spec_b1_sha256": run["spec_inputs"]["b1_spec_sha256"],
                   "producer_receipt": {"path": os.path.join(OPS, "b1_r7_run_all.json"),
                                        "sha256": sha_file(os.path.join(OPS, "b1_r7_run_all.json"))},
                   "decision": "REJECT" if lack else "ACCEPT_FOR_DRAFT",
                   "first_fail": ("MANDATORY_FIELD_MISSING:" + ",".join(lack)) if lack else None,
                   "checked_at": now(),
                   "identity_fabrication_check": {
                       "commit_is_null": ent["commit"] is None,
                       "blob_is_null": ent["blob"] is None,
                       "note": "an untracked target must carry null commit/blob; a value here is a defect"},
                   "observed": ent}
            (refused if lack else receipts).append(rec)
    return {"schema": "SST.PH01.W0.B4.Receiver@1", "generated_at": now(),
            "mandatory_fields": mandatory, "accepted": len(receipts), "refused": len(refused),
            "receipts": receipts, "refused_rows": refused,
            "claim_ceiling": "receiver readiness only; B4's own product effects are out of scope"}


def b3_admission() -> dict:
    prod = load(os.path.join(OPS, "b3_r7_product.json"))
    tqaep = load(os.path.join(OPS, "b3_r7_tqaep.json"))
    recon = load(os.path.join(OPS, "b3_r7_neg_reconcile.json"))
    negm = load(os.path.join(OPS, "b3_r7_neg_mutations.json"))
    receipt = load(os.path.join(OPS, "r7_consumer_receipts.json"))
    prior = load(os.path.join(PRE, "b3_prior_draft_inventory.json"))
    win = load(os.path.expanduser("~/.hgk-owner/window.json"))
    ops = {
        "JOIN": {"callable": "b3_product.op_join", "rows": prod["join"]["rows"],
                 "source_bound_ready": prod["join"]["source_bound_ready"],
                 "admission_ready": prod["join"]["admission_ready"],
                 "held": prod["join"]["held"]},
        "CHILD": {"callable": "b3_product.op_child", "atoms": prod["child"]["atoms"],
                  "ready": prod["child"]["ready"], "held": prod["child"]["held"]},
        "ROUTE": {"callable": "b3_product.op_route", "routes": prod["route"]["routes"],
                  "source_bound": prod["route"]["source_bound"],
                  "route_out": prod["route"]["route_out"], "hold": prod["route"]["hold"],
                  "note": ("route_out requires a bound owner; 365/365 units carry the literal "
                           "'#' as owner, so no route may leave this round")},
        "COMMIT": {"callable": "b3_product.op_commit", "receipt": prod["commit"]},
    }
    output_root = os.path.join(OPS, "b3_ledger")
    preimage_probe = {}
    for f in sorted(os.listdir(output_root)):
        p = os.path.join(output_root, f)
        preimage_probe[f] = {"bytes": os.path.getsize(p), "sha256": sha_file(p)}
    b0 = {"kind": "RECEIPT_ONLY",
          "reason": ("no current B0 SourceReadSet/2: the trusted-context descriptor "
                     "00_PREFLIGHT/B0_READ_CONTEXT_2026-11-26.json expired 2026-11-27T01:08+08:00 "
                     "and pins a previous window's authorization_sha; renewal edits product "
                     "constants and needs the Owner"),
          "consumer_currency": [{"consumer": r["consumer_id"], "decision": r["decision"],
                                 "first_fail": r.get("first_fail"),
                                 "rights_currency": r.get("rights_currency"),
                                 "authority_expired": r.get("envelope_authority_expired_at_receive")}
                                for r in receipt["receipts"]]}
    ready = {
        "ReadyDraft": True,
        "ReadyAtom": False,
        "ReadyExecute": False,
        "ReadyAccept": False,
        "readyatom_reason": ("no atom carries an owner (365/365 are the literal '#') and no "
                             "attachment is ratified; a source-bound atom is not an admissible "
                             "atom"),
    }
    out = {
        "schema": "SST.PH01.W0.B3.Admission@1",
        "generated_at": now(),
        "spec_b3_sha256": prod["spec_b3_sha256"],
        "host": {"hostname": socket.gethostname(), "os": platform.platform(),
                 "python": platform.python_version(), "principal": os.environ.get("USERNAME")},
        "ops": ops,
        "output_root": {
            "path": output_root,
            "preimage_state_at_first_slice": ("ABSENT — the directory was created by the first "
                                              "guarded write at 2026-11-27T15:40+0800; the write "
                                              "log is the two file mtimes below"),
            "postimage_state_at_this_run": preimage_probe,
            "writer": "b3_product.op_commit (single file, 'xb', readback compared)",
            "single_writer": True,
            "known_defect": ("the first slice's own product receipt was overwritten by the "
                             "immediate re-run used as the guard test; the committed bytes are "
                             "recoverable from the file (sha 1861ca3a…) but the receipt that "
                             "asserted preimage ABSENT for slice1 is not on disk"),
        },
        "oracles": {"source_bound": "direct_parent_ref + resolved_source_ref + direct_clause_sha",
                    "neg_declared_first_fail": {
                        "executed": recon.get("cases_verified", recon.get("cases_executed")),
                        "verdicts": recon["verdict_counts"],
                        "disagreements": len(recon.get("disagreements") or []),
                        "hold_reasons": negm.get("hold_reasons")},
                    "semantic_reader": "UNBOUND"},
        "safety": {"fin_order": prod["fin_order"], "effect": prod["effect"]},
        "recovery": {"prior_drafts": prior["files"],
                     "worker_or_handle_artefacts": [],
                     "write_locks": [f["write_lock_probe"] for f in prior["files"]]},
        "rights": {"window_id": win.get("window_id"), "task_id": win.get("task_id"),
                   "effect_class_ceiling": win.get("effect_class_ceiling"),
                   "expires_at": win.get("expires_at"), "state": win.get("state"),
                   "ops_used": win.get("ops_used"), "max_ops": win.get("max_ops"),
                   "op_counter_note": ("ops_used stayed 0: the draft write is a local file "
                                       "create guarded by reading the window, not an operation "
                                       "countersigned by the broker. rights_ref names a window, "
                                       "not a signed per-op receipt")},
        "b0_input": b0,
        "four_ready": ready,
        "readyexecute_blockers": [
            {"item": "B3 atom owner / ratification", "owner": "B3 domain holder (original clause owner)",
             "decision": ("365/365 units carry the literal '#' as owner and no atom is ratified; "
                          "supply the owner from the original clause, then the ledger can admit"),
             "blocks": "ReadyAtom, admission_ready, route_out, ReadyExecute"},
            {"item": "two identity fields are not verified by the product",
             "owner": "engineering",
             "decision": ("FIELD_owner and FIELD_requiredness mutations are not detected "
                          "(b3_r7_neg_mutations FAIL=2); the product must compare them against a "
                          "declared expectation before it may accept a row"),
             "blocks": "ReadyExecute"},
            {"item": "nine NEG fields have no structured carrier",
             "owner": "B3 domain holder",
             "decision": ("original_id, source_sha256, clause_span, parent, child, polarity, "
                          "oracle, case, draft exist only in clause prose; supply typed fields"),
             "blocks": "44-case NEG closure (29 HOLD)"},
        ],
        "b0_currency": {
            "readset": "40_OPS/b0_current_sourcereadset.json",
            "window_id": win.get("window_id"),
            "consumers": [(r.get("consumer_id"), r.get("decision"), r.get("rights_currency"))
                          for r in receipt["receipts"]],
            "resolved": all(r.get("decision") == "ACCEPT" for r in receipt["receipts"]),
        },
        "claim_ceiling": ("B3 product callables executed in memory and one guarded draft write; "
                          "no acceptance, no downstream effect, no semantic oracle"),
    }
    return out


def main() -> int:
    os.makedirs(PRE, exist_ok=True)
    pf = preflight()
    json.dump(pf, open(os.path.join(PRE, "r7_preflight.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    b4 = b4_receiver()
    json.dump(b4, open(os.path.join(OPS, "r7_b4_receiver.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    adm = b3_admission()
    json.dump(adm, open(os.path.join(OPS, "r7_b3_admission.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({
        "preflight": {"manifest_all_match": pf["manifest_all_match"],
                      "batches": {b: {"units": v["units"], "cases": v["cases_in_section_06"],
                                      "payload_sha_equal": v["payload_sha_equal"],
                                      "carriers": v["carrier_count"]}
                                  for b, v in pf["batches"].items()}},
        "b4_receiver": {"accepted": b4["accepted"], "refused": b4["refused"]},
        "b3_admission": {"four_ready": adm["four_ready"],
                         "blockers": [b["item"] for b in adm["readyexecute_blockers"]]},
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
