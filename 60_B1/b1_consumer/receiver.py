"""B1 minimal real v2 consumer (receiver side of SST.B0.SourceReadSet/2).

This is B1's own inbound acceptance path: it re-validates the B0 envelope against
its *own* trusted configuration and rights evidence, and writes B1's own receipt.
It does not import the B0 maker serializer; parsing/typing rules are re-implemented
from the r4 spec §02.F / §03.2.

B1_CANDIDATE_TECHNICALLY_READY (engineering), NOT B1_READY_EXECUTE.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WIRE_VERSION = "SST.B0.SourceReadSet/2"
SUBJECT = "SST/SQS-THC/PH01/E00"
ORIGINAL_WAVE = "P1-W00M"
VERIFIER_VERSION = "b1-consumer/1.0.0"

TOP_KEYS = {
    "wire_version", "subject", "original_wave", "bid", "spec_version",
    "candidate_digest", "scope", "source_manifest", "entries", "errors",
    "write_set", "preimage", "fin_order", "extensions",
}
ENTRY_KEYS = {
    "source_ref", "sha", "byte_length", "encoding", "clause_span", "clause_sha",
    "original_id", "child_id", "polarity", "requiredness", "owner", "provenance",
    "required_fields", "observed", "missing", "authority", "acl_epoch", "rights_epoch",
}
AUTHORITY_KEYS = {
    "source_owner", "usage_evidence_ref", "usage_evidence_sha", "os_principal",
    "verification_method", "rights_check_ref", "checked_at", "valid_from",
    "expires_at", "revocation_check_ref", "epoch_strategy", "epoch_provider_ref",
    "epoch_evidence_ref", "disclosure",
}
MISSING_REASONS = {"ABSENT", "UNVERIFIED", "FORMAT_UNSUPPORTED", "AMBIGUOUS"}


class Reject(Exception):
    def __init__(self, first_fail: str, detail: str = "") -> None:
        super().__init__(first_fail)
        self.first_fail = first_fail
        self.detail = detail


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise Reject("WIRE_INVALID", f"duplicate key {key}")
        seen[key] = value
    return seen


def _reject_constant(token: str) -> None:
    raise Reject("WIRE_INVALID", f"non-finite number {token}")


def load_context(path: str | os.PathLike[str]) -> dict[str, Any]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"context_version", "consumer_id", "candidate_digest", "scope_id",
                "source_ids", "rights_receipt_ref", "rights_receipt_sha",
                "rights_state_ref", "rights_task_id", "rights_scope",
                "verifier_version"}
    if set(doc) != required:
        raise Reject("CONSUMER_CONTEXT_INVALID", "context keys mismatch")
    if doc["context_version"] != "B1ReceiveContext/1":
        raise Reject("CONSUMER_CONTEXT_INVALID", "context version")
    return doc


def parse_envelope(payload: bytes) -> dict[str, Any]:
    if payload[:3] == b"\xef\xbb\xbf":
        raise Reject("WIRE_INVALID", "BOM present")
    try:
        text = payload.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise Reject("WIRE_INVALID", "not strict utf-8") from exc
    try:
        doc = json.loads(text, object_pairs_hook=_no_duplicate_keys,
                         parse_constant=_reject_constant)
    except Reject:
        raise
    except Exception as exc:
        raise Reject("WIRE_INVALID", "not one JSON object") from exc
    if not isinstance(doc, dict):
        raise Reject("WIRE_INVALID", "top level not an object")
    return doc


def check_rights(context: dict[str, Any], now: datetime) -> dict[str, str]:
    """B1's own rights entry.

    Two distinct evidences are required: the owner-signed receipt this consumer was
    configured against (identity, hash-pinned) and the live owner window (current
    state/expiry). A swapped receipt or an extended window is refused.
    """

    try:
        receipt_bytes = Path(context["rights_receipt_ref"]).read_bytes()
    except OSError as exc:
        raise Reject("RIGHTS_UNVERIFIED", "receipt unreadable") from exc
    receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
    if receipt_sha != context["rights_receipt_sha"]:
        raise Reject("RIGHTS_UNVERIFIED", "receipt hash changed")
    try:
        receipt = json.loads(receipt_bytes.decode("utf-8"))
    except Exception as exc:
        raise Reject("RIGHTS_UNVERIFIED", "receipt unparsable") from exc
    if receipt.get("task_id") != context["rights_task_id"]:
        raise Reject("RIGHTS_UNVERIFIED", "task mismatch")
    if list(receipt.get("scope") or []) != list(context["rights_scope"]):
        raise Reject("RIGHTS_UNVERIFIED", "scope mismatch")

    try:
        window_bytes = Path(context["rights_state_ref"]).read_bytes()
    except OSError as exc:
        raise Reject("RIGHTS_UNVERIFIED", "live window unreadable") from exc
    try:
        window = json.loads(window_bytes.decode("utf-8"))
    except Exception as exc:
        raise Reject("RIGHTS_UNVERIFIED", "live window unparsable") from exc
    if window.get("window_id") != receipt.get("window_id"):
        raise Reject("RIGHTS_UNVERIFIED", "live window is not the pinned window")
    state = window.get("state")
    if state in ("CLOSED", "REVOKED"):
        raise Reject("RIGHTS_REVOKED", f"state={state}")
    if state != "OPEN":
        raise Reject("RIGHTS_UNVERIFIED", f"state={state}")
    expires_at = window.get("expires_at")
    receipt_expiry = receipt.get("expires_at")
    if type(expires_at) is not int or type(receipt_expiry) is not int:
        raise Reject("RIGHTS_UNVERIFIED", "expiry not integer")
    if expires_at > receipt_expiry:
        raise Reject("RIGHTS_UNVERIFIED", "window expiry exceeds the pinned receipt")
    if int(now.timestamp()) >= expires_at:
        raise Reject("RIGHTS_EXPIRED", "owner window expired")
    return {"receipt_sha": receipt_sha,
            "state_sha": hashlib.sha256(window_bytes).hexdigest(),
            "window_id": window["window_id"]}


def validate_envelope(doc: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if set(doc) != TOP_KEYS:
        raise Reject("WIRE_INVALID", f"top-level keys: {sorted(set(doc) ^ TOP_KEYS)}")
    if doc["wire_version"] != WIRE_VERSION:
        raise Reject("WIRE_VERSION_UNSUPPORTED", str(doc["wire_version"]))
    if doc["subject"] != SUBJECT or doc["original_wave"] != ORIGINAL_WAVE:
        raise Reject("TUPLE_MISMATCH", "subject/wave")
    if type(doc["bid"]) is not int or doc["bid"] != 0:
        raise Reject("TUPLE_MISMATCH", "bid")
    if doc["candidate_digest"] != context["candidate_digest"]:
        raise Reject("TUPLE_MISMATCH", "candidate_digest")
    if doc["write_set"] != [] or doc["preimage"] != "N/A" or doc["fin_order"] != "DENY":
        raise Reject("WIRE_INVALID", "read-only invariants")
    scope = doc["scope"]
    if not isinstance(scope, dict) or set(scope) != {"scope_id", "source_ids", "purpose", "consumer_ids"}:
        raise Reject("WIRE_INVALID", "scope shape")
    if scope["scope_id"] != context["scope_id"]:
        raise Reject("SCOPE_MISMATCH", "scope_id")
    if list(scope["source_ids"]) != sorted(context["source_ids"]):
        raise Reject("SCOPE_MISMATCH", "source_ids")
    if not _nonempty(scope["purpose"]) or not scope["consumer_ids"]:
        raise Reject("WIRE_INVALID", "scope purpose/consumer")
    if context["consumer_id"] not in scope["consumer_ids"]:
        raise Reject("SCOPE_MISMATCH", "this consumer is not a declared consumer of the envelope")
    manifest = doc["source_manifest"]
    if not isinstance(manifest, dict) or set(manifest) != {"inherited_sha", "verification", "evidence_ref"}:
        raise Reject("WIRE_INVALID", "source_manifest shape")
    if not _sha(manifest["inherited_sha"]):
        raise Reject("WIRE_INVALID", "manifest sha")
    if manifest["verification"] not in ("VERIFIED", "UNVERIFIED"):
        raise Reject("WIRE_INVALID", "manifest verification")
    if manifest["verification"] == "UNVERIFIED" and manifest["evidence_ref"] is not None:
        raise Reject("WIRE_INVALID", "unverified manifest with evidence_ref")

    entries = doc["entries"]
    errors = doc["errors"]
    if not isinstance(entries, list) or not isinstance(errors, list):
        raise Reject("WIRE_INVALID", "entries/errors not lists")
    seen: dict[str, str] = {}
    for error in errors:
        if not isinstance(error, dict) or not isinstance(error.get("source_id"), str):
            raise Reject("WIRE_INVALID", "error entry shape")
        if error["source_id"] in seen:
            raise Reject("WIRE_INVALID", "source_id duplicated across entry/error")
        seen[error["source_id"]] = "error"
        if error.get("op") not in ("ROOT", "BYTES", "FIELDS", "RETURN"):
            raise Reject("WIRE_INVALID", "error op")
        if type(error.get("retryable")) is not bool or error.get("attempt") not in (1, 2):
            raise Reject("WIRE_INVALID", "error retryable/attempt")
        if not _nonempty(error.get("code")) or not _nonempty(error.get("first_fail")) or not _nonempty(error.get("resume")):
            raise Reject("WIRE_INVALID", "error code/first_fail/resume")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise Reject("WIRE_INVALID", "entry keys")
        ref = entry["source_ref"]
        if not isinstance(ref, dict) or set(ref) != {"source_id", "namespace", "locator", "source_version"}:
            raise Reject("WIRE_INVALID", "source_ref shape")
        if not all(_nonempty(ref[k]) for k in ref):
            raise Reject("WIRE_INVALID", "source_ref values")
        sid = ref["source_id"]
        if sid in seen:
            raise Reject("WIRE_INVALID", "source_id duplicated")
        seen[sid] = "entry"
        if sid not in context["source_ids"]:
            raise Reject("SCOPE_MISMATCH", f"unexpected source {sid}")
        if not _sha(entry["sha"]) or type(entry["byte_length"]) is not int or entry["byte_length"] < 0:
            raise Reject("WIRE_INVALID", "sha/byte_length")
        if entry["encoding"] != "UTF-8":
            raise Reject("WIRE_INVALID", "encoding")
        span = entry["clause_span"]
        if (not isinstance(span, list) or len(span) != 2
                or any(type(x) is not int for x in span) or span[0] < 1 or span[1] < span[0]):
            raise Reject("WIRE_INVALID", "clause_span")
        if not _sha(entry["clause_sha"]):
            raise Reject("WIRE_INVALID", "clause_sha")
        for key in ("original_id", "polarity", "requiredness", "owner"):
            if not _nonempty(entry[key]):
                raise Reject("WIRE_INVALID", f"{key}")
        if entry["child_id"] is not None and not _nonempty(entry["child_id"]):
            raise Reject("WIRE_INVALID", "child_id")
        prov = entry["provenance"]
        if not isinstance(prov, dict) or set(prov) != {
                "requirement_ref", "requirement_sha", "requirement_span", "rule_ref", "rule_sha"}:
            raise Reject("WIRE_INVALID", "provenance shape")
        if not _sha(prov["requirement_sha"]) or not _sha(prov["rule_sha"]):
            raise Reject("WIRE_INVALID", "provenance sha")
        required_fields = entry["required_fields"]
        if not isinstance(required_fields, list) or not required_fields or any(not _nonempty(f) for f in required_fields):
            raise Reject("WIRE_INVALID", "required_fields")
        if required_fields != sorted(set(required_fields)):
            raise Reject("WIRE_INVALID", "required_fields order/dupes")
        observed = entry["observed"]
        if not isinstance(observed, dict):
            raise Reject("WIRE_INVALID", "observed")
        for field, value in observed.items():
            if not isinstance(value, dict) or set(value) != {"value", "source_sha", "span", "value_sha"}:
                raise Reject("WIRE_INVALID", f"observed[{field}] shape")
            if not _sha(value["source_sha"]) or not _sha(value["value_sha"]):
                raise Reject("WIRE_INVALID", f"observed[{field}] sha")
            if value["source_sha"] != entry["sha"]:
                raise Reject("TUPLE_MISMATCH", f"observed[{field}] not from this source")
            if hashlib.sha256(value["value"].encode()).hexdigest() != value["value_sha"]:
                raise Reject("WIRE_INVALID", f"observed[{field}] value_sha")
        missing = entry["missing"]
        if not isinstance(missing, list):
            raise Reject("WIRE_INVALID", "missing")
        reason_fields = [m.get("field") for m in missing if isinstance(m, dict)]
        if len(reason_fields) != len(missing):
            raise Reject("WIRE_INVALID", "missing entries")
        for item in missing:
            if set(item) != {"field", "reason", "source_ref"}:
                raise Reject("WIRE_INVALID", "missing shape")
            if item["reason"] not in MISSING_REASONS:
                raise Reject("WIRE_INVALID", "missing reason")
            if item["source_ref"] != sid:
                raise Reject("WIRE_INVALID", "missing source_ref")
        p_set = set(observed)
        m_set = set(missing_field for missing_field in reason_fields)
        r_set = set(required_fields)
        if p_set | m_set != r_set or p_set & m_set:
            raise Reject("TUPLE_MISMATCH", "R/P/M not a partition")
        if len(missing) != len(m_set):
            raise Reject("WIRE_INVALID", "missing duplicated")
        authority = entry["authority"]
        if not isinstance(authority, dict) or set(authority) != AUTHORITY_KEYS:
            raise Reject("WIRE_INVALID", "authority shape")
        if authority["epoch_strategy"] not in ("PROVIDER_VERSIONED", "LIVE_REVALIDATE"):
            raise Reject("WIRE_INVALID", "epoch_strategy")
        if authority["disclosure"] not in ("LOCAL_ONLY", "APPROVED_CONSUMER"):
            raise Reject("WIRE_INVALID", "disclosure")
        for key in ("acl_epoch", "rights_epoch"):
            if entry[key] is not None and not _nonempty(entry[key]):
                raise Reject("WIRE_INVALID", key)
        item = {
            "source_id": sid,
            "sha": entry["sha"],
            "clause_sha": entry["clause_sha"],
            "R": required_fields,
            "P": sorted(observed),
            "M": sorted(m_set),
            "authority_epoch_strategy": authority["epoch_strategy"],
        }
        (accepted if not m_set else rejected).append(item)
    if set(seen) != set(context["source_ids"]):
        raise Reject("TUPLE_MISMATCH", "missing requested source")
    return {"accepted": accepted, "rejected": rejected, "errors": errors}


def receive(payload: bytes, context: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc).astimezone()
    rights = check_rights(context, now)
    doc = parse_envelope(payload)
    result = validate_envelope(doc, context)
    receipt = {
        "schema": "SST.B1.RECEIPT/1",
        "consumer_id": context["consumer_id"],
        "verifier_version": context["verifier_version"],
        "received_at": now.isoformat(),
        "subject": doc["subject"],
        "scope_id": doc["scope"]["scope_id"],
        "spec_version": doc["spec_version"],
        "candidate_digest": doc["candidate_digest"],
        "wire_version": doc["wire_version"],
        "rights": {"receipt_ref": context["rights_receipt_ref"],
                   "receipt_sha": rights["receipt_sha"],
                   "state_ref": context["rights_state_ref"],
                   "state_sha": rights["state_sha"],
                   "window_id": rights["window_id"],
                   "task_id": context["rights_task_id"]},
        "accepted": result["accepted"],
        "rejected": result["rejected"],
        "errors": result["errors"],
        "snapshot_sha": hashlib.sha256(payload).hexdigest(),
        "first_fail": None,
        "verdict": "ACCEPTED" if not result["rejected"] and not result["errors"] else "PARTIAL",
    }
    return receipt
