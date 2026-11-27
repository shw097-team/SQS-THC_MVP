# -*- coding: utf-8 -*-
"""Shared machinery for the three genuine inbound entries (D4).

Each consumer batch keeps its *own* declared expectation and its own entry function: the
shared receiver is one implementation, but the expectation, the identity and the readback
belong to the batch that consumes the envelope.  A consumer whose declaration drifts from
the pinned deployment refuses instead of silently inheriting the other batch's view.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from b0_r3_receiver import deployment as deployment_mod
from b0_r3_receiver.receiver import receive

ENTRY_SCHEMA = "SST.PH01.W0.B0.R3.InboundReadback/1"


def run_entry(consumer_id: str, own_expected: dict[str, Any], payload: bytes, *,
              entry: str, deployment_id: str = "prod", now=None) -> dict[str, Any]:
    dep = deployment_mod.load(deployment_id)
    consumer = dep["consumers"][consumer_id]

    # this batch's own declaration must agree with the deployment it is bound to
    pinned_sources = consumer["sources"]
    if sorted(own_expected["sources"]) != sorted(pinned_sources):
        raise SystemExit(json.dumps({
            "refused": "CONSUMER_EXPECTATION_DRIFT",
            "consumer_id": consumer_id,
            "declared": sorted(own_expected["sources"]),
            "pinned": sorted(pinned_sources)}, ensure_ascii=False))
    if own_expected.get("consumer_use") and own_expected["consumer_use"] != consumer["consumer_use"]:
        raise SystemExit(json.dumps({
            "refused": "CONSUMER_EXPECTATION_DRIFT", "consumer_id": consumer_id,
            "field": "consumer_use", "declared": own_expected["consumer_use"],
            "pinned": consumer["consumer_use"]}, ensure_ascii=False))
    fields = ("required_fields", "expected_raw_sha256", "requirement_span",
              "namespace", "source_version", "locator", "expected_clause_sha256")
    for sid, decl in own_expected["sources"].items():
        pin = pinned_sources[sid]
        drift = [f for f in fields if f in decl and decl[f] != pin[f]]
        rule = decl.get("extraction_rule")
        if rule and (rule.get("span") != pin["extraction_rule"].get("span")
                     or rule.get("prefix") != pin["extraction_rule"].get("prefix")):
            drift.append("extraction_rule")
        if drift:
            raise SystemExit(json.dumps({
                "refused": "CONSUMER_EXPECTATION_DRIFT",
                "consumer_id": consumer_id, "source_id": sid, "fields": drift,
                "declared": {k: decl.get(k) for k in fields},
                "pinned": {k: pin.get(k) for k in fields}}, ensure_ascii=False))

    receipt = receive(dep, consumer_id, payload, now=now,
                      deployment_ref=dep.get("_deployment_ref"))
    accepted = [r["source_id"] for r in receipt["rows"] if r["decision"] == "ACCEPT"]
    readback = {
        "schema": ENTRY_SCHEMA,
        "consumer_id": consumer_id,
        "entry": entry,
        "consumer_use": consumer["consumer_use"],
        "deployment": receipt["deployment"],
        "envelope_sha256": receipt["envelope_sha256"],
        "expected_sources": sorted(own_expected["sources"]),
        "accepted_sources": accepted,
        "mandatory_satisfied": receipt["verdict"] == "ACCEPTED",
        "per_source": [{"source_id": r["source_id"], "decision": r["decision"],
                        "first_fail": r["first_fail"],
                        "rights_check_ref": r["rights_check_ref"]} for r in receipt["rows"]],
        "claim_ceiling": ("This is the batch's inbound acceptance of one B0 envelope. It is not "
                          "the batch's own product acceptance and raises no ReadyExecute."),
    }
    receipt["inbound"] = readback
    return receipt


def cli(consumer_id: str, own_expected: dict[str, Any], entry: str,
        argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "receive":
        print(json.dumps({"refused": "USAGE", "usage": "receive --envelope <file|-> [--out <path>]"}))
        return 64
    envelope, out = None, None
    rest = argv[1:]
    for i, a in enumerate(rest):
        if a == "--envelope" and i + 1 < len(rest):
            envelope = rest[i + 1]
        if a == "--out" and i + 1 < len(rest):
            out = rest[i + 1]
    if envelope is None:
        print(json.dumps({"refused": "USAGE", "detail": "--envelope is required"}))
        return 64
    payload = sys.stdin.buffer.read() if envelope == "-" else Path(envelope).read_bytes()
    receipt = run_entry(consumer_id, own_expected, payload, entry=entry)
    text = json.dumps(receipt, ensure_ascii=False, indent=1)
    if out:
        p = Path(out)
        if p.exists():
            print(json.dumps({"refused": "PREIMAGE_NOT_ABSENT", "path": str(p)}))
            return 64
        with open(p, "xb") as fh:
            fh.write(text.encode("utf-8") + b"\n")
        print(json.dumps({"written": str(p), "consumer_id": consumer_id,
                          "verdict": receipt["verdict"],
                          "mandatory_satisfied": receipt["inbound"]["mandatory_satisfied"]},
                         ensure_ascii=False))
    else:
        print(text)
    return 0 if receipt["verdict"] == "ACCEPTED" else 2
