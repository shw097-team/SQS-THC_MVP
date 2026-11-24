"""Typed B0 source errors and SourceErrorEnvelope builders.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

ERROR_CODES = (
    "ROOT_NOT_FOUND",
    "ROOT_NOT_DIR",
    "PATH_ESCAPE",
    "REPARSE_POINT",
    "ADS_PATH",
    "RIGHTS_DENIED",
    "NAMESPACE_MISMATCH",
    "VERSION_DRIFT",
    "ENCODING_INVALID",
    "SHA_MISMATCH",
    "SPAN_OUT_OF_RANGE",
    "REQUIREDNESS_HOLD",
    "SCHEMA_INVALID",
)

_ERROR_CODE_SET = frozenset(ERROR_CODES)


def build_error(
    affected_locator: str,
    code: str,
    detail: str,
    *,
    first_fail: str | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    """Build one envelope error item with the fixed contract keys."""

    if code not in _ERROR_CODE_SET:
        raise ValueError(f"untyped B0 source error code: {code}")
    return {
        "affected_locator": str(affected_locator),
        "code": code,
        "detail": str(detail),
        "first_fail": code if first_fail is None else str(first_fail),
        "retryable": bool(retryable),
    }


def _normalise_error(error: Mapping[str, Any]) -> dict[str, Any]:
    return build_error(
        str(error.get("affected_locator", "")),
        str(error.get("code", "")),
        str(error.get("detail", "")),
        first_fail=str(error.get("first_fail") or error.get("code", "")),
        retryable=bool(error.get("retryable", False)),
    )


def build_envelope(
    errors: Iterable[Mapping[str, Any]],
    subject: str,
    scope: str | None,
) -> dict[str, Any]:
    """Build a SourceErrorEnvelope without adding contract-external keys."""

    return {
        "schema": "B0.SOURCE_ERROR_ENVELOPE/1",
        "subject": str(subject),
        "scope": None if scope is None else str(scope),
        "batch_id": "B0",
        "errors": [_normalise_error(error) for error in errors],
    }


def single_error_envelope(
    subject: str,
    scope: str | None,
    affected_locator: str,
    code: str,
    detail: str,
    *,
    first_fail: str | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    """Build an envelope containing one typed error."""

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
