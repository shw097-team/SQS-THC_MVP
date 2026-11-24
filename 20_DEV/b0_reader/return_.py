"""B0.RETURN read-set assembly with isolated per-reference failures.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from typing import Any

from .bytes_ import read_bytes
from .errors import build_envelope, build_error
from .fields import split_fields
from .root import check_root

_TRANSIENT_CODES = frozenset({"ROOT_NOT_FOUND", "RIGHTS_DENIED"})


def _error_for_result(
    result: Mapping[str, Any],
    locator: str,
    *,
    expires_transient: bool,
    default_code: str = "SCHEMA_INVALID",
) -> dict[str, Any]:
    code = str(result.get("code") or default_code)
    first_fail = str(result.get("first_fail") or code)
    retryable = code in _TRANSIENT_CODES and bool(expires_transient)
    return build_error(
        locator,
        code,
        f"{code}: {locator}",
        first_fail=first_fail,
        retryable=retryable,
    )


def _normalise_ref(ref: Any, index: int) -> dict[str, Any]:
    if isinstance(ref, Mapping):
        return dict(ref)
    return {
        "source_ref": os.fspath(ref),
        "locator": f"refs[{index}]",
    }


def _required_fields(ref: Mapping[str, Any]) -> list[str]:
    value = ref.get("required_fields", [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _locator(ref: Mapping[str, Any], source_ref: str) -> str:
    return str(ref.get("locator") or source_ref)


def _entry(
    ref: Mapping[str, Any],
    source_ref: str,
    root_verdict: Mapping[str, Any],
    byte_result: Mapping[str, Any],
    field_result: Mapping[str, Any],
) -> dict[str, Any]:
    polarity = ref.get("polarity")
    if polarity not in {"POS", "NEG"}:
        polarity = None
    requiredness = ref.get("requiredness")
    if requiredness != "required":
        requiredness = None
    return {
        "source_ref": source_ref,
        "source_sha": byte_result["source_sha"],
        "clause_span": byte_result["clause_span"],
        "clause_sha": byte_result["clause_sha"],
        "acl_epoch": ref.get("acl_epoch"),
        "rights_epoch": ref.get("rights_epoch"),
        "reader": "B0.ROOT+BYTES+FIELDS(engine)",
        "original_id": ref.get("original_id"),
        "child_id": ref.get("child_id"),
        "polarity": polarity,
        "requiredness": requiredness,
        "owner": ref.get("owner"),
        "required_fields": field_result["required_fields"],
        "missing_fields": field_result["missing_fields"],
        "observed": field_result["observed"],
        "locator": _locator(ref, source_ref),
    }


def build_read_set(
    subject: str,
    scope: str | None,
    version: str,
    refs: Iterable[Any],
    *,
    expires_transient: bool = True,
) -> dict[str, Any]:
    """Build one SourceReadSet by chaining ROOT, BYTES, and FIELDS per ref."""

    entries: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, raw_ref in enumerate(refs):
        ref = _normalise_ref(raw_ref, index)
        source_ref = os.fspath(ref.get("source_ref", ref.get("source", "")))
        source_ref = str(source_ref)
        allowed_root = ref.get("allowed_root", ref.get("root"))
        if allowed_root is None:
            allowed_root = os.path.dirname(source_ref)
        locator = _locator(ref, source_ref)

        root_verdict = check_root(
            allowed_root,
            source_ref,
            expected_namespace=ref.get(
                "expected_namespace", ref.get("namespace")
            ),
            expected_version=ref.get("expected_version", ref.get("version")),
        )
        if not root_verdict["ok"]:
            errors.append(
                _error_for_result(
                    root_verdict,
                    locator,
                    expires_transient=expires_transient,
                )
            )
            continue

        byte_result = read_bytes(
            root_verdict,
            expected_sha=ref.get("expected_sha"),
            clause_span=ref.get("clause_span"),
        )
        if not byte_result["ok"]:
            errors.append(
                _error_for_result(
                    byte_result,
                    locator,
                    expires_transient=expires_transient,
                )
            )
            continue

        required = _required_fields(ref)
        observed = ref.get("observed", {})
        verified = ref.get("verified_by_source", {})
        field_result = split_fields(
            required,
            observed if isinstance(observed, Mapping) else {},
            verified_by_source=verified if isinstance(verified, Mapping) else {},
        )
        if not field_result["ok"]:
            errors.append(
                _error_for_result(
                    field_result,
                    locator,
                    expires_transient=expires_transient,
                )
            )
            continue

        entries.append(
            _entry(ref, source_ref, root_verdict, byte_result, field_result)
        )

    read_set = {
        "schema": "B0.SOURCE_READ_SET/1",
        "subject": str(subject),
        "scope": None if scope is None else str(scope),
        "batch_id": "B0",
        "version": str(version),
        "entries": entries,
        "errors": errors,
        "write_set": [],
    }
    assert read_set["write_set"] == []
    return read_set


def to_envelope(
    errors: Iterable[Mapping[str, Any]],
    subject: str,
    scope: str | None,
) -> dict[str, Any]:
    """Convert B0 errors to the fixed SourceErrorEnvelope."""

    return build_envelope(errors, subject, scope)
