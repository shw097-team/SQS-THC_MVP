# -*- coding: utf-8 -*-
"""B0 → B1/B2/B3 shared R3 receiver (one implementation, three independent consumers).

Check order is the adopted one (B1-B3 r7 §02.R3):
    strict JSON/type → version/tuple/namespace/pin → this consumer's own rights entry
    → bytes/span/value/R/P/M re-derived from the original source → per-source result.

Global wire/tuple defects reject the whole envelope.  A source-scoped typed error, or a
failing source, is accounted to that source only: legal siblings still return their own
result (B0 §02.E/§03.2, W0-ADR01 R8).
"""
from __future__ import annotations

import json
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import rights as rights_mod
from . import wire
from .wire import Reject

SCHEMA = "SST.PH01.W0.B0.R3.ConsumerReceipt/1"


def _global_checks(doc: dict[str, Any], dep: dict[str, Any], consumer_id: str) -> None:
    if set(doc) != wire.TOP_KEYS:
        raise Reject("WIRE_INVALID", f"top-level keys: {sorted(set(doc) ^ wire.TOP_KEYS)}")
    if doc["wire_version"] != wire.WIRE_VERSION:
        raise Reject("WIRE_VERSION_UNSUPPORTED", str(doc["wire_version"]))
    if doc["spec_version"] != dep["spec_version"]:
        raise Reject("TUPLE_MISMATCH", "spec_version is not the adopted B0 v2 literal")
    if doc["subject"] != dep["subject"] or doc["original_wave"] != dep["original_wave"]:
        raise Reject("TUPLE_MISMATCH", "subject/original_wave")
    if not wire.is_int(doc["bid"]) or doc["bid"] != dep["bid"]:
        raise Reject("TUPLE_MISMATCH", "bid is not an integer 0")
    cand = doc["candidate_digest"]
    if not wire.is_sha256(cand):
        raise Reject("PRODUCER_FREEZE_UNBOUND", "candidate_digest is not a sha256")
    if cand != dep["producer_candidate_digest"]:
        raise Reject("TUPLE_MISMATCH", "candidate_digest is not the pinned producer freeze")
    if doc["write_set"] != [] or doc["preimage"] != "N/A" or doc["fin_order"] != "DENY":
        raise Reject("EFFECT_DENIED", "read-only invariants write_set/preimage/fin_order")
    if not isinstance(doc["extensions"], dict):
        raise Reject("WIRE_INVALID", "extensions not an object")

    scope = doc["scope"]
    if not isinstance(scope, dict) or set(scope) != {"scope_id", "source_ids", "purpose", "consumer_ids"}:
        raise Reject("WIRE_INVALID", "scope shape")
    if scope["scope_id"] != dep["scope_id"]:
        raise Reject("SCOPE_MISMATCH", "scope_id")
    if not isinstance(scope["source_ids"], list) or not scope["source_ids"]:
        raise Reject("WIRE_INVALID", "scope.source_ids")
    if sorted(scope["source_ids"]) != sorted(dep["source_ids"]):
        raise Reject("SCOPE_MISMATCH", "scope source set differs from the authorised set")
    if len(set(scope["source_ids"])) != len(scope["source_ids"]):
        raise Reject("WIRE_INVALID", "scope.source_ids carries a duplicate")
    if not wire.nonempty(scope["purpose"]) or scope["purpose"] != dep["scope_purpose"]:
        raise Reject("SCOPE_MISMATCH", "scope purpose")
    if consumer_id not in (scope["consumer_ids"] or []):
        raise Reject("SCOPE_MISMATCH", "this consumer is not a declared consumer of the envelope")

    manifest = doc["source_manifest"]
    if not isinstance(manifest, dict) or set(manifest) != {"inherited_sha", "verification", "evidence_ref"}:
        raise Reject("WIRE_INVALID", "source_manifest shape")
    if not wire.is_sha256(manifest["inherited_sha"]):
        raise Reject("WIRE_INVALID", "source_manifest.inherited_sha")
    # the inherited manifest is a pin, not a claim: it must be the value the deployment holds
    pinned_manifest = (dep.get("source_manifest_expected") or {}).get("inherited_sha")
    if pinned_manifest and manifest["inherited_sha"] != pinned_manifest:
        raise Reject("TUPLE_MISMATCH", "source_manifest.inherited_sha is not the pinned inherited manifest")
    if manifest["verification"] not in ("VERIFIED", "UNVERIFIED"):
        raise Reject("WIRE_INVALID", "source_manifest.verification")
    if manifest["verification"] == "UNVERIFIED" and manifest["evidence_ref"] is not None:
        raise Reject("WIRE_INVALID", "UNVERIFIED manifest carries an evidence_ref")
    # the envelope can never upgrade the manifest the deployment holds as UNVERIFIED
    expected_ver = (dep.get("source_manifest_expected") or {}).get("verification")
    if expected_ver and manifest["verification"] == "VERIFIED" and expected_ver != "VERIFIED":
        raise Reject("MANIFEST_VERIFICATION_ESCALATED",
                     "envelope claims a VERIFIED manifest the deployment holds as UNVERIFIED")
    if not isinstance(doc["entries"], list) or not isinstance(doc["errors"], list):
        raise Reject("WIRE_INVALID", "entries/errors must be arrays")


def _index_sources(doc: dict[str, Any], expected: set[str]) -> tuple[dict[str, dict], dict[str, dict]]:
    """One entry or one fatal error per requested source; duplicates and stray ids refuse."""
    entries: dict[str, dict] = {}
    errors: dict[str, dict] = {}
    for err in doc["errors"]:
        if not isinstance(err, dict) or set(err) != wire.ERROR_KEYS:
            raise Reject("WIRE_INVALID", "source error shape")
        sid = err.get("source_id")
        if not wire.nonempty(sid):
            raise Reject("WIRE_INVALID", "source error without a source_id")
        if sid not in expected:
            raise Reject("SCOPE_MISMATCH", f"error for an unrequested source {sid}")
        if sid in errors:
            raise Reject("WIRE_INVALID", f"duplicate error for {sid}")
        if err["op"] not in wire.OPS:
            raise Reject("WIRE_INVALID", "source error op")
        # integers reject bool: `attempt` must be an int, never True/False
        if type(err["retryable"]) is not bool or not wire.is_int(err["attempt"]) \
                or err["attempt"] not in (1, 2):
            raise Reject("WIRE_INVALID", "source error retryable/attempt")
        for key in ("code", "first_fail", "resume"):
            if not wire.nonempty(err[key]):
                raise Reject("WIRE_INVALID", f"source error {key}")
        errors[sid] = err
    for ent in doc["entries"]:
        if not isinstance(ent, dict) or set(ent) != wire.ENTRY_KEYS:
            raise Reject("WIRE_INVALID", "entry keys")
        ref = ent.get("source_ref")
        if not isinstance(ref, dict) or set(ref) != {"source_id", "namespace", "locator", "source_version"}:
            raise Reject("WIRE_INVALID", "source_ref shape")
        if not all(wire.nonempty(ref[k]) for k in ref):
            raise Reject("WIRE_INVALID", "source_ref values")
        sid = ref["source_id"]
        if sid not in expected:
            raise Reject("SCOPE_MISMATCH", f"entry for an unrequested source {sid}")
        if sid in entries:
            raise Reject("WIRE_INVALID", f"duplicate entry for {sid}")
        if sid in errors:
            raise Reject("WIRE_INVALID", f"{sid} carries both an entry and an error")
        entries[sid] = ent
    for sid in expected:
        if sid not in entries and sid not in errors:
            raise Reject("TUPLE_MISMATCH", f"requested source {sid} has neither entry nor error")
    return entries, errors


def _check_authority_block(authority: Any) -> dict[str, Any]:
    if not isinstance(authority, dict) or set(authority) != wire.AUTHORITY_KEYS:
        raise Reject("WIRE_INVALID", "authority shape")
    absent = sorted(k for k in wire.AUTHORITY_KEYS if authority[k] is None)
    # nullable by contract: epoch_provider_ref / epoch_evidence_ref
    absent = [k for k in absent if k not in ("epoch_provider_ref", "epoch_evidence_ref")]
    if absent:
        raise Reject("RIGHTS_UNVERIFIED", f"authority fields null: {absent}")
    if authority["epoch_strategy"] not in wire.EPOCH_STRATEGIES:
        raise Reject("WIRE_INVALID", "authority.epoch_strategy")
    if authority["disclosure"] not in wire.DISCLOSURES:
        raise Reject("WIRE_INVALID", "authority.disclosure")
    for key in ("source_owner", "usage_evidence_ref", "verification_method",
                "rights_check_ref", "checked_at", "revocation_check_ref"):
        if not wire.nonempty(authority[key]):
            raise Reject("RIGHTS_UNVERIFIED", f"authority.{key} empty")
    if not wire.is_sha256(authority["usage_evidence_sha"]):
        raise Reject("RIGHTS_UNVERIFIED", "authority.usage_evidence_sha")
    return authority


def _check_manifest_evidence(doc: dict[str, Any], dep: dict[str, Any]) -> None:
    """A VERIFIED manifest is only as good as the bytes the deployment pinned for it."""
    manifest = doc["source_manifest"]
    if manifest["verification"] != "VERIFIED":
        return
    pin = dep.get("source_manifest_expected") or {}
    expected_sha = pin.get("evidence_sha256")
    if not expected_sha:
        raise Reject("MANIFEST_EVIDENCE_UNRESOLVED", "deployment holds no verified-manifest digest")
    ref = manifest.get("evidence_ref")
    if not wire.nonempty(ref):
        raise Reject("MANIFEST_EVIDENCE_UNRESOLVED", "VERIFIED manifest without an evidence_ref")
    path = Path(ref)
    if not path.is_file():
        raise Reject("MANIFEST_EVIDENCE_UNRESOLVED", "evidence_ref does not resolve to bytes")
    if wire.sha256(path.read_bytes()) != expected_sha:
        raise Reject("MANIFEST_EVIDENCE_UNRESOLVED", "evidence bytes are not the pinned manifest")


def _receive_source(sid: str, ent: dict[str, Any], exp: dict[str, Any],
                    dep: dict[str, Any], rights_state: dict[str, Any],
                    now: datetime) -> dict[str, Any]:
    """One source, checked against this consumer's own pinned expectation."""
    ref = ent["source_ref"]
    if ref["namespace"] != exp["namespace"]:
        raise Reject("TUPLE_MISMATCH", "namespace")
    if ref["source_version"] != exp["source_version"]:
        raise Reject("TUPLE_MISMATCH", "source_version")
    if ref["locator"] != exp["locator"]:
        # the envelope never chooses what this consumer opens
        raise Reject("TUPLE_MISMATCH", "locator is not the trusted mapping for this source")
    if ent["sha"] != exp["expected_raw_sha256"]:
        raise Reject("TUPLE_MISMATCH", "raw pin differs from the pinned source pin")
    if not wire.is_int(ent["byte_length"]) or ent["byte_length"] < 0:
        raise Reject("WIRE_INVALID", "byte_length")
    if ent["encoding"] != "UTF-8":
        raise Reject("WIRE_INVALID", "encoding")
    if ent["clause_span"] != exp["requirement_span"]:
        raise Reject("TUPLE_MISMATCH", "clause_span is not the RequiredSetSpec requirement span")
    if not wire.is_sha256(ent["clause_sha"]):
        raise Reject("WIRE_INVALID", "clause_sha")
    if not wire.is_sha256(ent["provenance"]["requirement_sha"]) or \
            not wire.is_sha256(ent["provenance"]["rule_sha"]):
        raise Reject("WIRE_INVALID", "provenance sha")
    prov = ent["provenance"]
    if set(prov) != {"requirement_ref", "requirement_sha", "requirement_span", "rule_ref", "rule_sha"}:
        raise Reject("WIRE_INVALID", "provenance shape")
    if prov["requirement_sha"] != exp["expected_raw_sha256"]:
        raise Reject("TUPLE_MISMATCH", "provenance names a different requirement source")

    # ---- rights BEFORE any source content is touched (contract order) ----
    authority = _check_authority_block(ent["authority"])
    interval = rights_mod.check_envelope_authority(authority, rights_state, dep, now)
    for key in ("acl_epoch", "rights_epoch"):
        if ent[key] is not None and not wire.nonempty(ent[key]):
            raise Reject("WIRE_INVALID", key)
    if authority["epoch_strategy"] == "PROVIDER_VERSIONED":
        provider = dep.get("epoch_provider") or {}
        declared = [ent.get("acl_epoch"), ent.get("rights_epoch")]
        if not provider.get("provider_ref") or not all(wire.nonempty(v) for v in declared):
            # a bare string in one epoch column is not a provider-versioned epoch
            raise Reject("EPOCH_UNBOUND",
                         "PROVIDER_VERSIONED needs a deployment-bound provider and real acl/rights epochs")
        if authority.get("epoch_provider_ref") != provider["provider_ref"]:
            raise Reject("EPOCH_UNBOUND", "epoch_provider_ref is not the provider this deployment binds")
        want = provider.get("expected_rights_epoch")
        if want and ent.get("rights_epoch") != want:
            raise Reject("EPOCH_STALE", "rights_epoch is not the provider's current epoch")

    # ---- original bytes, read once from the trusted mapping (no envelope locator) ----
    locator = Path(exp["locator"])
    roots = [str(Path(r)) for r in (dep.get("allowed_roots") or [])]
    if roots:
        resolved = str(locator.resolve())
        if not any(resolved.lower().startswith(r.rstrip("\\").lower() + "\\") for r in roots):
            raise Reject("TUPLE_MISMATCH", "pinned locator is outside the deployment's allowed roots")
    try:
        before = locator.stat(follow_symlinks=False)
        if getattr(before, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise Reject("PATH_REPARSE_DENIED", "pinned source is a reparse point")
        raw = locator.read_bytes()
        after = locator.stat(follow_symlinks=False)
    except Reject:
        raise
    except OSError as exc:
        raise Reject("SOURCE_UNAVAILABLE", f"trusted source unreadable: {exc}") from exc
    if (before.st_size, before.st_mtime_ns, getattr(before, "st_ino", 0)) != \
            (after.st_size, after.st_mtime_ns, getattr(after, "st_ino", 0)) or len(raw) != after.st_size:
        raise Reject("SOURCE_CHANGED_SINCE_READ", "source identity moved during the read")
    if wire.sha256(raw) != exp["expected_raw_sha256"]:
        raise Reject("SOURCE_CHANGED_SINCE_READ", "source bytes no longer match the pin")
    if len(raw) != ent["byte_length"]:
        raise Reject("TUPLE_MISMATCH", "byte_length differs from the source")

    clause_bytes = wire.slice_span(raw, exp["requirement_span"])
    clause_sha = wire.sha256(clause_bytes)
    if clause_sha != ent["clause_sha"]:
        raise Reject("CLAUSE_SHA_MISMATCH", "clause slice hash differs")
    if clause_sha != exp["expected_clause_sha256"]:
        raise Reject("CLAUSE_RULE_MISMATCH", "clause slice moved against the pinned requirement")

    # ---- R re-derived from the RequiredSetSpec, not from the envelope ----
    required = list(exp["required_fields"])
    if ent["required_fields"] != sorted(set(required)):
        raise Reject("REQUIRED_SET_CHANGED", "wire R is not the original required set")
    observed = ent["observed"]
    if not isinstance(observed, dict):
        raise Reject("WIRE_INVALID", "observed not an object")
    for field, item in observed.items():
        if field not in required:
            raise Reject("FIELD_NOT_REQUIRED", f"{field} is not in the original R")
        if not isinstance(item, dict) or set(item) != {"value", "source_sha", "span", "value_sha"}:
            raise Reject("WIRE_INVALID", f"observed[{field}] shape")
        if item["source_sha"] != ent["sha"]:
            raise Reject("TUPLE_MISMATCH", f"observed[{field}] not taken from this source")
        if not wire.is_sha256(item["value_sha"]) or not isinstance(item["value"], str):
            raise Reject("WIRE_INVALID", f"observed[{field}] value/value_sha")
        if wire.sha256(item["value"].encode("utf-8")) != item["value_sha"]:
            raise Reject("CLAUSE_RULE_MISMATCH", f"observed[{field}] value_sha mismatch")
        expected_value = wire.md_label_value(raw, exp["extraction_rule"])
        if item["value"] != expected_value:
            raise Reject("CLAUSE_RULE_MISMATCH", f"observed[{field}] is not the value the rule yields")
        if item["span"] != exp["extraction_rule"]["span"]:
            raise Reject("CLAUSE_RULE_MISMATCH", f"observed[{field}] span is not the rule span")
        if exp["extraction_rule"]["source_id"] != sid:
            raise Reject("TUPLE_MISMATCH", "extraction rule belongs to another source")

    # ---- M must be exactly R - P ----
    missing = ent["missing"]
    if not isinstance(missing, list):
        raise Reject("WIRE_INVALID", "missing not an array")
    m_fields = []
    for item in missing:
        if not isinstance(item, dict) or set(item) != {"field", "reason", "source_ref"}:
            raise Reject("WIRE_INVALID", "missing shape")
        if item["reason"] not in wire.MISSING_REASONS:
            raise Reject("WIRE_INVALID", "missing reason")
        if item["source_ref"] != sid:
            raise Reject("TUPLE_MISMATCH", "missing source_ref")
        m_fields.append(item["field"])
    if len(set(m_fields)) != len(m_fields):
        raise Reject("WIRE_INVALID", "duplicate missing field")
    if set(m_fields) & set(observed):
        raise Reject("TUPLE_MISMATCH", "a field is both observed and missing")
    if set(m_fields) | set(observed) != set(required):
        raise Reject("TUPLE_MISMATCH", "R/P/M is not a partition of R")

    decision, first_fail = "ACCEPT", None
    if m_fields:
        decision, first_fail = "DRAFT_MISSING", "MANDATORY_FIELD_MISSING"

    return {
        "R": sorted(required), "P": sorted(observed), "M": sorted(m_fields),
        "clause_sha": clause_sha, "clause_span": exp["requirement_span"],
        "authority_checked": authority, "authority_interval": interval,
        "provenance": prov, "decision": decision, "first_fail": first_fail,
    }


def receive(deployment: dict[str, Any], consumer_id: str, payload: bytes, *,
            now: datetime | None = None, deployment_ref: dict[str, Any] | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    consumer = deployment["consumers"][consumer_id]
    expected = set(consumer["source_ids"])
    rows: list[dict[str, Any]] = []

    def row(sid: str, decision: str, first_fail: str | None, *, sha: str | None = None,
            evidence: dict[str, Any] | None = None) -> None:
        rows.append({
            "consumer_id": consumer_id,
            "validator_name": consumer["validator_name"],
            "validator_version": consumer["validator_version"],
            "subject": deployment["subject"],
            "scope_id": deployment["scope_id"],
            "spec_version": deployment["spec_version"],
            "candidate_digest": deployment["producer_candidate_digest"],
            "source_id": sid,
            "sha": sha,
            # per-source: the window + receipt that authorised THIS source's decision
            "rights_check_ref": (f'{rights_state["live_window_id"]}:'
                                 f'{rights_state["receipt_sha256"][:16]}:{sid}' if rights_state else None),
            "decision": decision,
            "first_fail": first_fail,
            "checked_at": now.isoformat(),
            "evidence": evidence or {},
        })

    rights_state: dict[str, Any] | None = None
    global_fail: str | None = None
    detail = ""
    try:
        doc = wire.parse_envelope(payload)
    except Reject as exc:
        doc, global_fail, detail = None, exc.code, exc.detail

    if doc is not None and global_fail is None:
        try:
            _global_checks(doc, deployment, consumer_id)
        except Reject as exc:
            global_fail, detail = exc.code, exc.detail

    if global_fail is None:
        try:
            rights_state = rights_mod.check_rights(deployment, now)
        except Reject as exc:
            global_fail, detail = exc.code, exc.detail

    if global_fail is not None:
        for sid in sorted(expected):
            row(sid, "REJECT", global_fail, evidence={"detail": detail,
                                                      "scope": "ENVELOPE_OR_RIGHTS"})
        return _receipt(deployment, consumer_id, payload, rows, now, rights_state,
                        global_fail, deployment_ref)

    try:
        _check_manifest_evidence(doc, deployment)
    except Reject as exc:
        for sid in sorted(expected):
            row(sid, "REJECT", exc.code, evidence={"detail": exc.detail, "scope": "MANIFEST"})
        return _receipt(deployment, consumer_id, payload, rows, now, rights_state,
                        exc.code, deployment_ref)

    try:
        entries, errors = _index_sources(doc, expected)
    except Reject as exc:
        for sid in sorted(expected):
            row(sid, "REJECT", exc.code, evidence={"detail": exc.detail, "scope": "ENVELOPE"})
        return _receipt(deployment, consumer_id, payload, rows, now, rights_state,
                        exc.code, deployment_ref)

    for sid in sorted(expected):
        exp = consumer["sources"][sid]
        if sid in errors:
            err = errors[sid]
            # a source-scoped typed error accounts to this source only
            row(sid, "REJECT", err["first_fail"],
                evidence={"source_error": err, "scope": "SOURCE"})
            continue
        ent = entries[sid]
        try:
            result = _receive_source(sid, ent, exp, deployment, rights_state, now)
        except Reject as exc:
            row(sid, "REJECT", exc.code, sha=ent.get("sha"),
                evidence={"detail": exc.detail, "scope": "SOURCE",
                          "expected": {k: exp[k] for k in
                                       ("expected_raw_sha256", "requirement_span",
                                        "required_fields", "expected_value")}})
            continue
        row(sid, result["decision"], result["first_fail"], sha=ent["sha"], evidence={
            "R": result["R"], "P": result["P"], "M": result["M"],
            "clause_sha": result["clause_sha"], "clause_span": result["clause_span"],
            "authority_checked": result["authority_checked"],
            "authority_interval": result["authority_interval"],
            "provenance": result["provenance"],
            "expected": {k: exp[k] for k in ("expected_raw_sha256", "requirement_span",
                                             "required_fields", "expected_value",
                                             "required_set_sha256")},
        })

    # rights re-verified immediately before returning a result
    recheck_fail = None
    try:
        after = rights_mod.check_rights(deployment, datetime.now(timezone.utc))
        if after["receipt_sha256"] != rights_state["receipt_sha256"] or \
                after["live_window_id"] != rights_state["live_window_id"]:
            recheck_fail = "RIGHTS_CHANGED_BEFORE_RETURN"
    except Reject as exc:
        recheck_fail = exc.code
    if recheck_fail:
        for r in rows:
            r["decision"] = "REJECT"
            r["first_fail"] = recheck_fail

    return _receipt(deployment, consumer_id, payload, rows, now, rights_state,
                    None, deployment_ref)


def _receipt(deployment: dict[str, Any], consumer_id: str, payload: bytes,
             rows: list[dict[str, Any]], now: datetime, rights_state: dict[str, Any] | None,
             global_fail: str | None, deployment_ref: dict[str, Any] | None) -> dict[str, Any]:
    accepted = [r for r in rows if r["decision"] == "ACCEPT"]
    draft = [r for r in rows if r["decision"] == "DRAFT_MISSING"]
    rejected = [r for r in rows if r["decision"] == "REJECT"]
    if global_fail is not None:
        verdict = "REJECTED"
    elif rejected:
        verdict = "REJECTED"
    elif draft:
        verdict = "PARTIAL_DRAFT"
    else:
        verdict = "ACCEPTED"
    return {
        "schema": SCHEMA,
        "consumer_id": consumer_id,
        "validator_name": deployment["consumers"][consumer_id]["validator_name"],
        "validator_version": deployment["consumers"][consumer_id]["validator_version"],
        "deployment": deployment_ref or {"deployment_id": deployment["deployment_id"],
                                         "trust_root_kind": deployment["trust_root_kind"]},
        "envelope_sha256": wire.sha256(payload),
        "envelope_bytes": len(payload),
        "checked_at": now.isoformat(),
        "rights": rights_state,
        "rows": rows,
        "sources_expected": len(deployment["consumers"][consumer_id]["source_ids"]),
        "sources_accepted": len(accepted),
        "sources_draft_missing": len(draft),
        "sources_rejected": len(rejected),
        "global_first_fail": global_fail,
        "verdict": verdict,
        "claim_ceiling": ("This receipt evidences one consumer's inbound acceptance of one "
                          "B0 SourceReadSet/2 envelope. It does not accept B1/B2/B3 own "
                          "products, does not raise B0 to COMPLETE and grants no write."),
    }


def load_pinned_deployment(deployment_id: str, expected_sha256: str, path: str) -> dict[str, Any]:
    """Load the deployment descriptor by pinned digest and prove its trust root."""
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise Reject("TRUST_CONTEXT_UNBOUND", f"deployment descriptor unreadable: {exc}") from exc
    sha = wire.sha256(raw)
    if sha != expected_sha256:
        raise Reject("TRUST_CONTEXT_UNBOUND", "deployment descriptor hash is not the pin")
    rights_mod.assert_trust_root(p)
    dep = json.loads(raw.decode("utf-8"))
    if dep.get("deployment_id") != deployment_id:
        raise Reject("TRUST_CONTEXT_UNBOUND", "deployment id differs")
    dep["_deployment_ref"] = {"path": str(p), "sha256": sha,
                              "deployment_id": deployment_id,
                              "trust_root_kind": dep["trust_root_kind"]}
    return dep
