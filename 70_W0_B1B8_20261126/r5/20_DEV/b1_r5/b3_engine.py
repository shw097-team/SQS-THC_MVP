#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 native engine — JOIN / CHILD / ROUTE / COMMIT (r4 spec, product layer).

B3's true requires per the frozen DAG are B0 SourceReadSet/2 and B2 ToolReadSet.
This engine consumes them as immutable inputs and never re-derives its own expectation
from the producer's observed values.

What is real here:
  * the B2 ToolReadSet is the object B2 actually emitted (1,465 union entries);
  * the B0 side is either a conforming SourceReadSet/2 value or, when the producer did not
    persist one (B0 does not write files by design), a real per-source consumer receipt is
    accepted as RECEIPT_ONLY evidence and the gap is named on every affected row;
  * namespace join is exact; duplicate atoms and missing requiredness are refused;
  * COMMIT is a guarded local draft write: single file, preimage ABSENT, read-back hash.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

W = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace"
OPS = os.path.join(W, "70_W0_B1B8_20261126", "40_OPS")
TOOL_READSET = os.path.join(OPS, "b2_r5_tool_readset.json")
B1_RECEIPT = os.path.join(W, "60_B1", "receipts", "b1_receipt_r6_2026-11-26.json")
SOURCE_READSET = os.path.join(OPS, "b0_r5_sourcereadset.json")
DRAFT_DIR = os.path.join(OPS, "b3_draft")


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_tool_readset(path: str = TOOL_READSET) -> dict:
    d = json.load(open(path, encoding="utf-8"))
    if d.get("schema") != "SST.B2.ToolReadSet@6":
        raise ValueError(f"TOOL_READSET_SCHEMA_MISMATCH {d.get('schema')}")
    entries = d.get("entries") or []
    if len(entries) != d.get("union_expected"):
        raise ValueError(f"TOOL_READSET_UNION_MISMATCH {len(entries)} != {d.get('union_expected')}")
    keys = [e["tool_key"] for e in entries]
    if len(set(keys)) != len(keys):
        raise ValueError("TOOL_READSET_DUPLICATE_KEY")
    d["_source"] = {"path": path, "sha256": sha256_file(path), "bytes": os.path.getsize(path)}
    return d


def load_source_side() -> dict:
    """Prefer a real SourceReadSet/2 value captured from the product run; fall back to the
    consumer receipt and mark every affected row RECEIPT_ONLY."""
    if os.path.exists(SOURCE_READSET):
        r = json.load(open(SOURCE_READSET, encoding="utf-8"))
        if r.get("wire_version") == "SST.B0.SourceReadSet/2":
            return {"kind": "READSET",
                    "evidence_ref": SOURCE_READSET, "evidence_sha256": sha256_file(SOURCE_READSET),
                    "wire_version": r.get("wire_version"),
                    "spec_version": r.get("spec_version"),
                    "candidate_digest": r.get("candidate_digest"),
                    "sources": {e["source_ref"]["source_id"]: e for e in r.get("entries") or []},
                    "note": "real SourceReadSet/2 captured from the B0 product run"}
    if os.path.exists(B1_RECEIPT):
        r = json.load(open(B1_RECEIPT, encoding="utf-8"))
        accepted = r.get("accepted") or []
        return {"kind": "RECEIPT_ONLY",
                "evidence_ref": B1_RECEIPT, "evidence_sha256": sha256_file(B1_RECEIPT),
                "wire_version": r.get("wire_version"),
                "spec_version": r.get("spec_version"),
                "candidate_digest": r.get("candidate_digest"),
                "sources": {a["source_id"]: a for a in accepted},
                "note": "a real consumer receipt, not the SourceReadSet/2 value itself; every "
                        "row joined through it is marked RECEIPT_ONLY"}
    return {"kind": "ABSENT", "sources": {}}


def join(tool_readset: dict, source_side: dict) -> dict:
    rows, errors = [], []
    seen_atoms = set()
    # the declared registry namespaces, taken from the producer's own declaration
    declared_ns = set((tool_readset.get("namespace") or {}).keys()) or {
        "R3-REGISTRY-Q1", "R3-REGISTRY-Q2", "R3-REGISTRY-Q3", "R3-REGISTRY-Q4"}
    for e in tool_readset["entries"]:
        key = e["tool_key"]
        # a tool key may omit its registry namespace; do not invent one
        ns = key.split("::")[0] if key.startswith("R3-REGISTRY-") else "UNRESOLVED_TOOL_KEY"
        row = {"atom": key, "namespace": ns, "kind": e.get("kind"),
               "source_row": e.get("source_row"),
               "requiredness": e.get("requiredness"),
               "payload_sha": e.get("payload_sha"),
               "b0_side": source_side["kind"], "missing": []}
        if key.startswith("R3-REGISTRY-") and ns not in declared_ns:
            errors.append({"code": "NAMESPACE_JOIN_DENY", "atom": key,
                           "declared": sorted(declared_ns), "retryable": False})
            row["missing"].append({"field": "namespace", "reason": "AMBIGUOUS",
                                   "detail": f"namespace {ns!r} is not one of the declared "
                                             f"registry namespaces"})
        if e.get("requiredness") in (None, "UNKNOWN"):
            row["missing"].append({"field": "requiredness", "reason": "UNVERIFIED",
                                   "detail": "producer emitted no classifiable requiredness"})
        if key in seen_atoms:
            errors.append({"code": "DUPLICATE_ATOM_DENY", "atom": key, "retryable": False})
            row["missing"].append({"field": "atom", "reason": "AMBIGUOUS",
                                   "detail": "duplicate atom in the tool read set"})
        seen_atoms.add(key)
        if source_side["kind"] == "RECEIPT_ONLY":
            row["missing"].append({"field": "b0_source_readset",
                                   "reason": "UNVERIFIED",
                                   "detail": "joined against a consumer receipt; the "
                                             "SourceReadSet/2 value itself was not supplied"})
        rows.append(row)
    return {"rows": rows, "errors": errors,
            "summary": {"rows": len(rows),
                        "with_mandatory": sum(1 for r in rows if not r["missing"]),
                        "with_missing": sum(1 for r in rows if r["missing"]),
                        "duplicate_atoms": len(errors)}}


def child_ledger(joined: dict) -> dict:
    ready = [r for r in joined["rows"] if not r["missing"]]
    held = [r for r in joined["rows"] if r["missing"]]
    by_scope = {}
    for r in joined["rows"]:
        by_scope[r["namespace"]] = by_scope.get(r["namespace"], 0) + 1
    return {
        "schema": "SST.B3.SourceChildLedger.DRAFT@1",
        "atoms_ready": len(ready),
        "atoms_held": len(held),
        "by_namespace": by_scope,
        "children": [{"atom": r["atom"], "requiredness": r["requiredness"],
                      "source_row": r["source_row"], "payload_sha": r["payload_sha"]}
                     for r in ready],
        "holds": [{"atom": r["atom"], "missing": r["missing"]} for r in held],
        "claim_ceiling": "DRAFT_ONLY: a ledger draft is neither a product outcome nor an ACK",
    }


def neg_arms(tool_readset: dict) -> list:
    """The original B3 refusals, executed for real."""
    arms = []
    # (a) same tail, different namespace
    sample = tool_readset["entries"][0]["tool_key"]
    tail = sample.split("::", 1)[1]
    forged = f"R3-REGISTRY-Q9::{tail}"
    # the mutation must travel through the real JOIN callable, not a string-set test
    forged_entry = json.loads(json.dumps(tool_readset["entries"][0]))
    forged_entry["tool_key"] = forged
    jn = join({"entries": [forged_entry], "union_expected": 1},
              {"kind": "ABSENT", "sources": {}})
    arm_errors = [e["code"] for e in jn["errors"]]
    row_holds = jn["rows"][0]["missing"] if jn["rows"] else []
    arms.append({"arm": "NAMESPACE_JOIN_DENY", "mutation": f"{sample} -> {forged}",
                 "observed_errors": arm_errors,
                 "observed_row_missing": [m.get("field") for m in row_holds],
                 "pass": ("NAMESPACE_JOIN_DENY" in arm_errors
                          or any(m.get("field") == "namespace" for m in row_holds))})
    # (b) duplicate atom
    dup = {"entries": [tool_readset["entries"][0], dict(tool_readset["entries"][0])],
           "union_expected": 2}
    j = join(dup, {"kind": "ABSENT", "sources": {}})
    arms.append({"arm": "DUPLICATE_ATOM_DENY", "mutation": "same tool_key twice",
                 "observed": [e["code"] for e in j["errors"]],
                 "pass": any(e["code"] == "DUPLICATE_ATOM_DENY" for e in j["errors"])})
    # (c) missing requiredness
    bad = json.loads(json.dumps(tool_readset["entries"][0]))
    bad["requiredness"] = "UNKNOWN"
    j2 = join({"entries": [bad], "union_expected": 1}, {"kind": "ABSENT", "sources": {}})
    arms.append({"arm": "TOOL_REQUIREDNESS_HOLD", "mutation": "requiredness -> UNKNOWN",
                 "pass": any(m["field"] == "requiredness" for m in j2["rows"][0]["missing"])})
    return arms


def commit(draft: dict, name: str) -> dict:
    """Guarded LOCAL_DRAFT_WRITE: one file under W, preimage must be ABSENT."""
    os.makedirs(DRAFT_DIR, exist_ok=True)
    path = os.path.join(DRAFT_DIR, name)
    if os.path.exists(path):
        raise FileExistsError(f"PREIMAGE_NOT_ABSENT {path}")
    body = json.dumps(draft, ensure_ascii=False, indent=1, sort_keys=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    readback = open(path, "rb").read()
    return {"path": path, "bytes": len(readback),
            "sha256": hashlib.sha256(readback).hexdigest(),
            "preimage": "ABSENT", "postimage_verified": readback.decode("utf-8") == body,
            "write_set": [path], "product_write": "LOCAL_DRAFT_WRITE",
            "single_file": True}


def run() -> dict:
    trs = load_tool_readset()
    src = load_source_side()
    j = join(trs, src)
    ledger = child_ledger(j)
    arms = neg_arms(trs)
    return {"schema": "SST.PH01.W0.B3.JoinResult@1",
            "inputs": {"tool_readset": trs["_source"],
                       "source_side": {k: src[k] for k in
                                       ("kind", "evidence_ref", "evidence_sha256",
                                        "wire_version", "spec_version") if k in src}},
            "join": j["summary"], "ledger": {k: ledger[k] for k in
                                             ("atoms_ready", "atoms_held", "by_namespace")},
            "neg_arms": arms, "errors": j["errors"],
            "effect": "SOURCE_READ+IN_MEMORY_TRANSFORM",
            "fin_order": "DENY"}
