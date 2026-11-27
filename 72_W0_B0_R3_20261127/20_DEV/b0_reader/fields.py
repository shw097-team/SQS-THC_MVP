"""B0.FIELDS requiredness-preserving source extraction.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .bytes_ import line_spans, normalize_span
from .requiredset import RequiredSetSpec, RuleSpec

MISSING_REASONS = frozenset(
    {"ABSENT", "UNVERIFIED", "FORMAT_UNSUPPORTED", "AMBIGUOUS"}
)


def value_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _failure(
    required_fields: list[str],
    observed: dict[str, Any],
    missing_fields: list[dict[str, str]],
    invariants: dict[str, bool],
    code: str,
    first_fail: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "required_fields": required_fields,
        "observed": observed,
        "missing": missing_fields,
        "missing_fields": missing_fields,
        "invariants": invariants,
        "code": code,
        "first_fail": first_fail,
    }


def _extract_rule(
    rule: RuleSpec,
    payload: bytes,
    lines: list[tuple[int, int]],
) -> tuple[str | None, str]:
    if rule.method not in {"RAW_SPAN_UTF8", "MD_LABEL"}:
        return None, "FORMAT_UNSUPPORTED"
    first, last = rule.span
    if last > len(lines) or first < 1:
        return None, "UNVERIFIED"
    segment_start = lines[first - 1][0]
    segment_end = lines[last - 1][1]
    try:
        segment = payload[segment_start:segment_end].decode(
            "utf-8", errors="strict"
        )
    except UnicodeDecodeError:
        return None, "UNVERIFIED"
    if segment_start == 0 and segment.startswith("\ufeff"):
        segment = segment[1:]
    if rule.method == "RAW_SPAN_UTF8":
        candidate = segment
    else:
        prefix = rule.prefix or ""
        occurrences = segment.count(prefix)
        if occurrences == 0:
            return None, "ABSENT"
        if occurrences > 1:
            return None, "AMBIGUOUS"
        start = segment.index(prefix) + len(prefix)
        end = segment.find("\r", start)
        if end < 0:
            end = segment.find("\n", start)
        if end < 0:
            end = len(segment)
        candidate = segment[start:end].strip(" \t")
        if candidate.endswith("\r"):
            candidate = candidate[:-1]
    if (
        rule.expected_literal is not None
        and candidate != rule.expected_literal
    ):
        return None, "CLAUSE_RULE_MISMATCH"
    return candidate, ""


def extract_fields(
    required_set: RequiredSetSpec,
    payload: bytes,
    *,
    source_id: str,
    source_sha: str,
) -> dict[str, Any]:
    """Extract only P from pure-data rules; caller-supplied values are absent."""

    required = list(required_set.required_fields)
    if not required:
        return _failure(
            required,
            {},
            [],
            {"subset": True, "disjoint": True, "r_unchanged": True},
            "REQUIRED_SET_UNBOUND",
            "REQUIRED_SET_UNBOUND",
        )
    lines = line_spans(payload)
    if (
        required_set.requirement_span[0] < 1
        or required_set.requirement_span[1] > len(lines)
    ):
        return _failure(
            required,
            {},
            [],
            {"subset": True, "disjoint": True, "r_unchanged": True},
            "SPAN_INVALID",
            "SPAN_INVALID",
        )
    observed: dict[str, Any] = {}
    missing: list[dict[str, str]] = []
    for rule in required_set.rules:
        if rule.source_id != source_id:
            return _failure(
                required,
                observed,
                missing,
                {"subset": False, "disjoint": True, "r_unchanged": True},
                "CLAUSE_RULE_MISMATCH",
                "CLAUSE_RULE_MISMATCH",
            )
        first, last = rule.span
        if first < 1 or last > len(lines):
            return _failure(
                required,
                observed,
                missing,
                {"subset": False, "disjoint": True, "r_unchanged": True},
                "SPAN_INVALID",
                "SPAN_INVALID",
            )
        value, reason = _extract_rule(rule, payload, lines)
        if value is None:
            if reason == "CLAUSE_RULE_MISMATCH":
                return _failure(
                    required,
                    observed,
                    missing,
                    {"subset": False, "disjoint": True, "r_unchanged": True},
                    "CLAUSE_RULE_MISMATCH",
                    "CLAUSE_RULE_MISMATCH",
                )
            missing.append(
                {
                    "field": rule.field,
                    "reason": reason,
                    "source_ref": source_id,
                }
            )
            continue
        observed[rule.field] = {
            "value": value,
            "source_sha": source_sha,
            "span": [first, last],
            "value_sha": value_sha(value),
        }
    observed = {key: observed[key] for key in sorted(observed)}
    missing.sort(key=lambda item: item["field"])
    required_sorted = sorted(required)
    p = set(observed)
    m = {item["field"] for item in missing}
    invariants = {
        "subset": m.issubset(required_sorted),
        "disjoint": p.isdisjoint(m),
        "r_unchanged": required == required_sorted,
        "partition": p | m == set(required_sorted),
    }
    if not all(invariants.values()):
        return _failure(
            required,
            observed,
            missing,
            invariants,
            "REQUIRED_SET_CHANGED",
            "REQUIRED_SET_CHANGED",
        )
    return {
        "ok": True,
        "required_fields": required,
        "observed": observed,
        "missing": missing,
        "missing_fields": missing,
        "invariants": invariants,
        "code": None,
        "first_fail": None,
    }


def split_fields(
    required_fields: list[str],
    observed: Mapping[str, Any],
    *,
    verified_by_source: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Author compatibility helper.

    The production path rejects caller-reported ``verified_by_source``; this
    helper accepts already verified values only for the original author tests.
    """

    del verified_by_source
    try:
        required = list(required_fields)
    except TypeError:
        required = []
    if (
        any(not isinstance(field, str) or not field for field in required)
        or required != sorted(required)
        or len(required) != len(set(required))
    ):
        return _failure(
            [str(field) for field in required],
            {},
            [],
            {"subset": False, "disjoint": True, "r_unchanged": False},
            "REQUIRED_SET_CHANGED",
            "REQUIRED_SET_CHANGED",
        )
    if any(field not in required for field in observed):
        return _failure(
            required,
            dict(observed),
            [],
            {"subset": True, "disjoint": True, "r_unchanged": True},
            "FIELD_NOT_REQUIRED",
            "FIELD_NOT_REQUIRED",
        )
    p = {field for field in required if field in observed}
    m = set(required) - p
    missing = [
        {"field": field, "reason": "ABSENT", "source_ref": "AUTHOR_ONLY"}
        for field in sorted(m)
    ]
    return {
        "ok": True,
        "required_fields": required,
        "observed": dict(observed),
        "missing": missing,
        "missing_fields": missing,
        "invariants": {
            "subset": True,
            "disjoint": True,
            "r_unchanged": True,
            "partition": True,
        },
        "code": None,
        "first_fail": None,
    }
