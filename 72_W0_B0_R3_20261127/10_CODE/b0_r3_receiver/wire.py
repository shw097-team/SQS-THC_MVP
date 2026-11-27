# -*- coding: utf-8 -*-
"""Strict wire layer for SST.B0.SourceReadSet/2 (receiver side).

Re-implemented from the adopted v2 contract (B0 r4 §02.B0 / B1-B3 r7 §02.R3); the
producer's serializer is never imported.  Every rejection carries the contract code
the receiver must emit, so a negative arm can assert an exact first_fail.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

WIRE_VERSION = "SST.B0.SourceReadSet/2"
SUBJECT = "SST/SQS-THC/PH01/E00"
ORIGINAL_WAVE = "P1-W00M"
SPEC_VERSION = "2026-11-25_r4_Native-first"
SOURCE_MANIFEST_SHA = "2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e"

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
ERROR_KEYS = {"source_id", "op", "code", "first_fail", "retryable", "attempt", "resume"}
MISSING_REASONS = {"ABSENT", "UNVERIFIED", "FORMAT_UNSUPPORTED", "AMBIGUOUS"}
OPS = {"ROOT", "BYTES", "FIELDS", "RETURN"}
EPOCH_STRATEGIES = {"PROVIDER_VERSIONED", "LIVE_REVALIDATE"}
DISCLOSURES = {"LOCAL_ONLY", "APPROVED_CONSUMER"}

RFC3339 = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})$")


class Reject(Exception):
    """A typed refusal.  `code` is the contract first_fail, never a free sentence."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def is_sha256(v: Any) -> bool:
    return isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v)


def nonempty(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def is_int(v: Any) -> bool:
    """`type is int` — bool is an int subclass and the contract refuses bool-as-int."""
    return type(v) is int


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise Reject("WIRE_INVALID", f"duplicate key {key}")
        seen[key] = value
    return seen


def _reject_constant(token: str) -> None:
    raise Reject("WIRE_INVALID", f"non-finite number {token}")


def parse_envelope(payload: bytes) -> dict[str, Any]:
    """One UTF-8 JSON object, no BOM, no surrounding text, no duplicate keys, no NaN."""
    if payload[:3] == b"\xef\xbb\xbf":
        raise Reject("WIRE_INVALID", "BOM present")
    try:
        text = payload.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise Reject("WIRE_INVALID", "not strict utf-8") from exc
    if not text.strip():
        raise Reject("WIRE_INVALID", "empty payload")
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


def physical_lines(raw: bytes) -> list[bytes]:
    """Physical lines with their terminators kept (CRLF aware)."""
    lines: list[bytes] = []
    pos = 0
    while pos < len(raw):
        nl = raw.find(b"\n", pos)
        cr = raw.find(b"\r", pos)
        if nl == -1 and cr == -1:
            lines.append(raw[pos:])
            break
        if cr != -1 and (nl == -1 or cr < nl):
            end = cr + 2 if raw[cr:cr + 2] == b"\r\n" else cr + 1
            lines.append(raw[pos:end])
        else:
            lines.append(raw[pos:nl + 1])
        pos += len(lines[-1])
    return lines


def slice_span(raw: bytes, span: list[int]) -> bytes:
    lines = physical_lines(raw)
    a, b = span
    if a < 1 or b < a or b > len(lines):
        raise Reject("CLAUSE_RULE_MISMATCH", f"span {span} outside 1..{len(lines)}")
    return b"".join(lines[a - 1:b])


def parse_rfc3339(value: Any) -> datetime:
    """Strict RFC3339 with an explicit offset.  No local-timezone filling, no truncation."""
    if not isinstance(value, str):
        raise Reject("RIGHTS_UNVERIFIED", "timestamp not a string")
    m = RFC3339.match(value)
    if not m:
        raise Reject("RIGHTS_UNVERIFIED", f"not RFC3339: {value!r}")
    try:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise Reject("RIGHTS_UNVERIFIED", f"unparsable timestamp {value!r}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise Reject("RIGHTS_UNVERIFIED", "timestamp without offset")
    return dt.astimezone(timezone.utc)


def md_label_value(raw: bytes, rule: dict[str, Any]) -> str:
    """Re-derive the field value from the original bytes with the RequiredSetSpec rule."""
    if rule.get("method") != "MD_LABEL":
        raise Reject("CLAUSE_RULE_MISMATCH", f"unknown extraction method {rule.get('method')!r}")
    prefix = rule.get("prefix")
    span = rule.get("span")
    if not isinstance(prefix, str) or not prefix:
        raise Reject("CLAUSE_RULE_MISMATCH", "rule prefix absent")
    if not (isinstance(span, list) and len(span) == 2 and all(is_int(x) for x in span)):
        raise Reject("CLAUSE_RULE_MISMATCH", "rule span absent")
    lines = physical_lines(raw)
    for line in lines[span[0] - 1:span[1]]:
        text = line.decode("utf-8")
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    raise Reject("CLAUSE_RULE_MISMATCH", "label not found inside the rule span")
