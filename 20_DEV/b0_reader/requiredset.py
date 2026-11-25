"""Validated pure-data RequiredSetSpec loading.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .errors import is_nonempty_str, is_sha256
from .root import (
    canonical_local_path,
    close_root_verdict,
    open_authorized_file,
)

SPEC_VERSION = "B0RequiredSetSpec/1"
SUPPORTED_METHODS = frozenset({"RAW_SPAN_UTF8", "MD_LABEL"})
NORMATIVE_KEYS = {
    "required_set_spec_version",
    "requirement_ref",
    "requirement_sha",
    "requirement_span",
    "original_id",
    "child_id",
    "polarity",
    "requiredness",
    "owner",
    "required_fields",
    "rules",
}
RULE_KEYS = {
    "field",
    "method",
    "source_id",
    "span",
    "prefix",
    "expected_literal",
}


class RequiredSetError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RequiredSetError("REQUIRED_SET_UNBOUND", "duplicate key")
        result[key] = value
    return result


def _load_json_bytes(payload: bytes) -> Any:
    try:
        text = payload.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                RequiredSetError("REQUIRED_SET_UNBOUND", value)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "invalid JSON") from exc


def normalize_span(value: Any) -> tuple[int, int]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or any(type(item) is not int for item in value)
        or value[0] < 1
        or value[1] < value[0]
    ):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "invalid span")
    return value[0], value[1]


@dataclass(frozen=True, slots=True)
class RuleSpec:
    field: str
    method: str
    source_id: str
    span: tuple[int, int]
    prefix: str | None
    expected_literal: str | None


@dataclass(frozen=True, slots=True)
class RequiredSetSpec:
    requirement_ref: str
    requirement_sha: str
    requirement_span: tuple[int, int]
    original_id: str
    child_id: str | None
    polarity: str
    requiredness: str
    owner: str
    required_fields: tuple[str, ...]
    rules: tuple[RuleSpec, ...]
    rule_ref: str
    rule_sha: str
    raw_bytes: int

    def provenance(self) -> dict[str, Any]:
        return {
            "requirement_ref": self.requirement_ref,
            "requirement_sha": self.requirement_sha,
            "requirement_span": list(self.requirement_span),
            "rule_ref": self.rule_ref,
            "rule_sha": self.rule_sha,
        }


def validate_required_set(
    document: Any,
    *,
    rule_ref: str,
    rule_sha: str,
    raw_bytes: int,
    requirement_ref: str | None = None,
    expected_source_id: str | None = None,
) -> RequiredSetSpec:
    if not isinstance(document, Mapping) or set(document) != NORMATIVE_KEYS:
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "spec keys")
    if document.get("required_set_spec_version") != SPEC_VERSION:
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "spec version")
    for key in (
        "requirement_ref",
        "original_id",
        "polarity",
        "requiredness",
        "owner",
    ):
        if not is_nonempty_str(document.get(key)):
            raise RequiredSetError("REQUIRED_SET_UNBOUND", key)
    child_id = document.get("child_id")
    if child_id is not None and not is_nonempty_str(child_id):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "child_id")
    if not is_sha256(document.get("requirement_sha")):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "requirement_sha")
    compliance_ref = canonical_local_path(document.get("requirement_ref"))
    if (
        requirement_ref is not None
        and canonical_local_path(compliance_ref)
        != canonical_local_path(requirement_ref)
    ):
        raise RequiredSetError("REQUIRED_SET_CHANGED", "requirement ref changed")
    if not os.path.isabs(rule_ref) or not is_sha256(rule_sha):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "rule pin")
    span = normalize_span(document.get("requirement_span"))
    fields = document.get("required_fields")
    if (
        not isinstance(fields, list)
        or not fields
        or any(not is_nonempty_str(field) for field in fields)
        or fields != sorted(fields)
        or len(fields) != len(set(fields))
    ):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "required_fields")
    rules_raw = document.get("rules")
    if not isinstance(rules_raw, list) or len(rules_raw) != len(fields):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "rules")
    rules_by_field: dict[str, RuleSpec] = {}
    for raw_rule in rules_raw:
        if not isinstance(raw_rule, Mapping) or set(raw_rule) != RULE_KEYS:
            raise RequiredSetError("REQUIRED_SET_UNBOUND", "rule keys")
        field = raw_rule.get("field")
        method = raw_rule.get("method")
        source_id = raw_rule.get("source_id")
        prefix = raw_rule.get("prefix")
        expected_literal = raw_rule.get("expected_literal")
        if (
            field not in fields
            or field in rules_by_field
            or not is_nonempty_str(method)
            or not is_nonempty_str(source_id)
        ):
            raise RequiredSetError("REQUIRED_SET_UNBOUND", "rule identity")
        if method in SUPPORTED_METHODS and method == "RAW_SPAN_UTF8":
            if prefix is not None:
                raise RequiredSetError("REQUIRED_SET_UNBOUND", "raw prefix")
        elif method in SUPPORTED_METHODS and not is_nonempty_str(prefix):
            raise RequiredSetError("REQUIRED_SET_UNBOUND", "label prefix")
        if (
            method in SUPPORTED_METHODS
            and expected_literal is not None
            and not isinstance(expected_literal, str)
        ):
            raise RequiredSetError("REQUIRED_SET_UNBOUND", "expected literal")
        rules_by_field[field] = RuleSpec(
            field=field,
            method=method,
            source_id=source_id,
            span=normalize_span(raw_rule.get("span")),
            prefix=prefix,
            expected_literal=expected_literal,
        )
    if set(rules_by_field) != set(fields):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "rules coverage")
    return RequiredSetSpec(
        requirement_ref=compliance_ref,
        requirement_sha=document["requirement_sha"],
        requirement_span=span,
        original_id=document["original_id"],
        child_id=child_id,
        polarity=document["polarity"],
        requiredness=document["requiredness"],
        owner=document["owner"],
        required_fields=tuple(fields),
        rules=tuple(rules_by_field[field] for field in fields),
        rule_ref=canonical_local_path(rule_ref),
        rule_sha=rule_sha,
        raw_bytes=raw_bytes,
    )


def load_required_set(
    ref: str,
    *,
    expected_sha: str,
    expected_span: tuple[int, int] | list[int],
    requirement_ref: str | None = None,
    requirement_sha: str | None = None,
    expected_source_id: str | None = None,
) -> RequiredSetSpec:
    canonical = canonical_local_path(ref)
    try:
        handle, verdict = open_authorized_file(
            canonical, allowed_root=os.path.dirname(canonical)
        )
        try:
            identity = handle.identity()
            payload = handle.read_all()
            after = handle.identity()
        finally:
            handle.close()
            close_root_verdict(verdict)
    except OSError as exc:
        raise RequiredSetError("REQUIRED_SET_UNBOUND", str(exc)) from exc
    if identity.tuple != after.tuple or len(payload) != after.size:
        raise RequiredSetError("REQUIRED_SET_CHANGED", "rule file changed")
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != expected_sha:
        raise RequiredSetError("REQUIRED_SET_CHANGED", "rule SHA changed")
    document = _load_json_bytes(payload)
    if not isinstance(document, Mapping):
        raise RequiredSetError("REQUIRED_SET_UNBOUND", "spec root")
    if (
        requirement_sha is not None
        and document.get("requirement_sha") != requirement_sha
    ):
        raise RequiredSetError("REQUIRED_SET_CHANGED", "requirement SHA changed")
    span_value = document.get("requirement_span")
    if list(expected_span) != list(span_value or []):
        raise RequiredSetError("REQUIRED_SET_CHANGED", "requirement span changed")
    return validate_required_set(
        document,
        rule_ref=canonical,
        rule_sha=actual_sha,
        raw_bytes=len(payload),
        requirement_ref=requirement_ref,
        expected_source_id=expected_source_id,
    )
