"""Typed B0 source errors and fixed v2 error serialization.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

OP_ORDER = ("ROOT", "BYTES", "FIELDS", "RETURN")
OP_SET = frozenset(OP_ORDER)

ERROR_CODES = (
    "INVOCATION_INVALID",
    "TRUST_CONTEXT_UNBOUND",
    "SUBJECT_MISMATCH",
    "SCOPE_MISMATCH",
    "EFFECT_DENIED",
    "ROOT_UNBOUND",
    "PATH_INVALID",
    "PATH_ESCAPE",
    "PATH_REPARSE_DENIED",
    "PATH_IDENTITY_UNVERIFIED",
    "RIGHTS_UNVERIFIED",
    "RIGHTS_DENIED",
    "RIGHTS_EXPIRED",
    "RIGHTS_REVOKED",
    "EPOCH_STALE",
    "SOURCE_UNAVAILABLE",
    "SOURCE_PIN_MISMATCH",
    "SOURCE_CHANGED",
    "ENCODING_INVALID",
    "NAMESPACE_MISMATCH",
    "VERSION_MISMATCH",
    "SPAN_INVALID",
    "REQUIRED_SET_UNBOUND",
    "REQUIRED_SET_CHANGED",
    "FIELD_NOT_REQUIRED",
    "FIELD_METADATA_UNVERIFIED",
    "CLAUSE_RULE_MISMATCH",
    "WIRE_VERSION_UNSUPPORTED",
    "WIRE_INVALID",
    "TUPLE_MISMATCH",
    "CONSUMER_NOT_YET_EXECUTED",
    "UNKNOWN_RECONCILE_REQUIRED",
    "NATIVE_DEPENDENCY_FAILED",
    "EVIDENCE_TUPLE_MISMATCH",
    "INDEPENDENCE_NOT_PROVEN",
    "PRODUCT_NOT_PROVEN",
)
ERROR_CODE_SET = frozenset(ERROR_CODES)

# Historical v1 names remain recognizable only to support author-level controls.
LEGACY_ERROR_CODES = (
    "ROOT_NOT_FOUND",
    "ROOT_NOT_DIR",
    "REPARSE_POINT",
    "ADS_PATH",
    "VERSION_DRIFT",
    "SHA_MISMATCH",
    "SPAN_OUT_OF_RANGE",
    "REQUIREDNESS_HOLD",
    "SCHEMA_INVALID",
)
LEGACY_ERROR_CODE_SET = frozenset(LEGACY_ERROR_CODES)
TERMINAL_INVOCATION_CODES = frozenset(
    {
        "INVOCATION_INVALID",
        "TRUST_CONTEXT_UNBOUND",
        "SUBJECT_MISMATCH",
        "SCOPE_MISMATCH",
        "EFFECT_DENIED",
    }
)
RETRYABLE_CODES = frozenset({"SOURCE_UNAVAILABLE"})

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SourceError:
    """One fixed v2 source error; this is a value, never an authority token."""

    source_id: str
    op: str
    code: str
    first_fail: str
    affected_locator: str | None
    retryable: bool
    attempt: int
    resume: str
    expected_sha: str | None = None
    observed_sha: str | None = None

    def to_wire(self) -> dict[str, Any]:
        if self.op not in OP_SET:
            raise ValueError("INVOCATION_INVALID")
        if self.code not in ERROR_CODE_SET:
            raise ValueError("INVOCATION_INVALID")
        if not is_nonempty_str(self.source_id):
            raise ValueError("INVOCATION_INVALID")
        if not is_nonempty_str(self.first_fail) or not is_nonempty_str(self.resume):
            raise ValueError("INVOCATION_INVALID")
        if self.affected_locator is not None and not isinstance(
            self.affected_locator, str
        ):
            raise ValueError("INVOCATION_INVALID")
        if type(self.retryable) is not bool or type(self.attempt) is not int:
            raise ValueError("INVOCATION_INVALID")
        if self.attempt not in (1, 2):
            raise ValueError("INVOCATION_INVALID")
        if self.retryable != (self.code in RETRYABLE_CODES and self.attempt == 1):
            raise ValueError("INVOCATION_INVALID")

        result: dict[str, Any] = {
            "source_id": self.source_id,
            "op": self.op,
            "code": self.code,
            "first_fail": self.first_fail,
            "affected_locator": self.affected_locator,
            "retryable": self.retryable,
            "attempt": self.attempt,
            "resume": self.resume,
        }
        if self.expected_sha is not None:
            if not _SHA_RE.fullmatch(self.expected_sha):
                raise ValueError("INVOCATION_INVALID")
            result["expected_sha"] = self.expected_sha
        if self.observed_sha is not None:
            if not _SHA_RE.fullmatch(self.observed_sha):
                raise ValueError("INVOCATION_INVALID")
            result["observed_sha"] = self.observed_sha
        return result


def is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA_RE.fullmatch(value) is not None


def make_error(
    source_id: str,
    op: str,
    code: str,
    *,
    first_fail: str | None = None,
    affected_locator: str | None = None,
    retryable: bool = False,
    attempt: int = 1,
    resume: str | None = None,
    expected_sha: str | None = None,
    observed_sha: str | None = None,
) -> SourceError:
    """Construct a typed error without stringly accepting legacy product codes."""

    if code not in ERROR_CODE_SET:
        raise ValueError(f"untyped B0 source error code: {code}")
    if op not in OP_SET:
        raise ValueError(f"invalid B0 source operation: {op}")
    if resume is None:
        resume = (
            "UNKNOWN 先 reconcile；不得未確認狀態前重入"
            if code == "UNKNOWN_RECONCILE_REQUIRED"
            else "修正可信來源或權利後建立新 attempt"
        )
    return SourceError(
        source_id=source_id,
        op=op,
        code=code,
        first_fail=first_fail or code,
        affected_locator=affected_locator,
        retryable=retryable,
        attempt=attempt,
        resume=resume,
        expected_sha=expected_sha,
        observed_sha=observed_sha,
    )


def build_error(
    affected_locator: str,
    code: str,
    detail: str,
    *,
    first_fail: str | None = None,
    retryable: bool = False,
    source_id: str | None = None,
    op: str = "RETURN",
    attempt: int = 1,
    resume: str | None = None,
    expected_sha: str | None = None,
    observed_sha: str | None = None,
) -> dict[str, Any]:
    """Build one v2 error while retaining the author compatibility signature.

    ``detail`` is accepted for source compatibility but never serialized, so
    path/ACL/content leakage cannot enter the wire through a free-form field.
    """

    del detail
    if source_id is None:
        source_id = affected_locator or "UNAVAILABLE"
    if code in LEGACY_ERROR_CODE_SET:
        raise ValueError("legacy author error cannot be promoted to v2 wire")
    error = make_error(
        source_id,
        op,
        code,
        first_fail=first_fail,
        affected_locator=None if affected_locator == "" else affected_locator,
        retryable=retryable,
        attempt=attempt,
        resume=resume,
        expected_sha=expected_sha,
        observed_sha=observed_sha,
    )
    return error.to_wire()


def normalize_error(error: SourceError | Mapping[str, Any]) -> dict[str, Any]:
    """Validate an error object and return only its normative fields."""

    if isinstance(error, SourceError):
        return error.to_wire()
    if not isinstance(error, Mapping):
        raise ValueError("INVOCATION_INVALID")
    allowed = {
        "source_id",
        "op",
        "code",
        "first_fail",
        "affected_locator",
        "retryable",
        "attempt",
        "resume",
        "expected_sha",
        "observed_sha",
    }
    if set(error) - allowed:
        raise ValueError("INVOCATION_INVALID")
    retryable = error.get("retryable", False)
    attempt = error.get("attempt", 1)
    if type(retryable) is not bool or type(attempt) is not int:
        raise ValueError("INVOCATION_INVALID")
    return SourceError(
        source_id=error.get("source_id", ""),
        op=error.get("op", ""),
        code=error.get("code", ""),
        first_fail=error.get("first_fail", error.get("code", "")),
        affected_locator=error.get("affected_locator"),
        retryable=retryable,
        attempt=attempt,
        resume=error.get("resume", ""),
        expected_sha=error.get("expected_sha"),
        observed_sha=error.get("observed_sha"),
    ).to_wire()


def sorted_errors(
    errors: Iterable[SourceError | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    values = [normalize_error(error) for error in errors]
    values.sort(key=lambda item: item["source_id"])
    source_ids = [item["source_id"] for item in values]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("INVOCATION_INVALID")
    return values


def build_envelope(
    errors: Iterable[SourceError | Mapping[str, Any]],
    subject: str,
    scope: Any,
) -> dict[str, Any]:
    """Build the fixed v2 error-envelope projection.

    The synthetic context admits only an error envelope. It deliberately
    cannot serialize a successful source entry without a full live context.
    """

    if scope is None:
        normal_errors = sorted_errors(errors)
        projected_scope = {
            "scope_id": "UNAVAILABLE",
            "source_ids": sorted({item["source_id"] for item in normal_errors}),
            "purpose": "UNAVAILABLE",
            "consumer_ids": ["UNAVAILABLE"],
        }
        errors_value = normal_errors
    else:
        projected_scope = scope
        errors_value = sorted_errors(errors)
    return {
        "wire_version": "SST.B0.SourceReadSet/2",
        "subject": str(subject),
        "original_wave": "P1-W00M",
        "bid": 0,
        "spec_version": "2026-11-25_r4_Native-first",
        "candidate_digest": "SYNTHETIC_CANDIDATE_NOT_PRODUCT",
        "scope": projected_scope,
        "source_manifest": {
            "inherited_sha": "2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e",
            "verification": "UNVERIFIED",
            "evidence_ref": None,
        },
        "entries": [],
        "errors": errors_value,
        "write_set": [],
        "preimage": "N/A",
        "fin_order": "DENY",
        "extensions": {},
    }


def single_error_envelope(
    subject: str,
    scope: Any,
    affected_locator: str,
    code: str,
    detail: str,
    *,
    first_fail: str | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    """Author-compatible single-error wrapper; v1 fields are not emitted."""

    return build_envelope(
        [
            build_error(
                affected_locator,
                code,
                detail,
                first_fail=first_fail,
                retryable=retryable,
            )
        ],
        subject,
        scope,
    )
