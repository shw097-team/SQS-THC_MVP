"""B0.BYTES strict UTF-8, digest, and CRLF-preserving clause reads.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
from typing import Any


def _result(
    *,
    ok: bool,
    source_sha: str | None,
    clause_span: list[int] | None,
    clause_sha: str | None,
    text: str | None,
    line_count: int,
    code: str | None,
    first_fail: str | None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "source_sha": source_sha,
        "clause_span": clause_span,
        "clause_sha": clause_sha,
        "text": text,
        "line_count": line_count,
        "code": code,
        "first_fail": first_fail,
    }


def _line_spans(payload: bytes) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for index, value in enumerate(payload):
        if value == 0x0A:
            spans.append((start, index + 1))
            start = index + 1
    if start < len(payload):
        spans.append((start, len(payload)))
    return spans


def _normalise_span(clause_span: Any) -> list[int] | None:
    if clause_span is None:
        return None
    if isinstance(clause_span, (str, bytes)):
        return None
    try:
        values = list(clause_span)
    except TypeError:
        return None
    if len(values) != 2 or any(
        isinstance(value, bool) or not isinstance(value, int) for value in values
    ):
        return None
    return [values[0], values[1]]


def read_bytes(
    verdict: dict[str, Any],
    *,
    expected_sha: str | None = None,
    clause_span: list[int] | tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Read an approved ROOT verdict and apply strict byte-level checks."""

    span_supplied = clause_span is not None
    requested_span = _normalise_span(clause_span)
    if not bool(verdict.get("ok")):
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            code=verdict.get("code"),
            first_fail=verdict.get("first_fail"),
        )
    if span_supplied and requested_span is None:
        return _result(
            ok=False,
            source_sha=None,
            clause_span=None,
            clause_sha=None,
            text=None,
            line_count=0,
            code="SPAN_OUT_OF_RANGE",
            first_fail="SPAN_OUT_OF_RANGE",
        )

    realpath = str(verdict.get("realpath", ""))
    try:
        with open(realpath, "rb") as stream:
            payload = stream.read()
    except PermissionError:
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            code="RIGHTS_DENIED",
            first_fail="RIGHTS_DENIED",
        )
    except OSError:
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            code="ROOT_NOT_FOUND",
            first_fail="ROOT_NOT_FOUND",
        )

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            code="ENCODING_INVALID",
            first_fail="ENCODING_INVALID",
        )

    source_sha = hashlib.sha256(payload).hexdigest()
    spans = _line_spans(payload)
    line_count = len(spans)
    if expected_sha is not None and source_sha != str(expected_sha).strip().lower():
        return _result(
            ok=False,
            source_sha=source_sha,
            clause_span=requested_span,
            clause_sha=None,
            text=text,
            line_count=line_count,
            code="SHA_MISMATCH",
            first_fail="SHA_MISMATCH",
        )

    clause_sha: str | None = None
    if requested_span is not None:
        first_line, last_line = requested_span
        if (
            first_line < 1
            or last_line < first_line
            or last_line > line_count
            or line_count == 0
        ):
            return _result(
                ok=False,
                source_sha=source_sha,
                clause_span=requested_span,
                clause_sha=None,
                text=text,
                line_count=line_count,
                code="SPAN_OUT_OF_RANGE",
                first_fail="SPAN_OUT_OF_RANGE",
            )
        clause_start = spans[first_line - 1][0]
        clause_end = spans[last_line - 1][1]
        clause_sha = hashlib.sha256(payload[clause_start:clause_end]).hexdigest()

    return _result(
        ok=True,
        source_sha=source_sha,
        clause_span=requested_span,
        clause_sha=clause_sha,
        text=text,
        line_count=line_count,
        code=None,
        first_fail=None,
    )
