"""B0.BYTES strict UTF-8, raw hashes, and physical line spans.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
from typing import Any

from .winio import WinHandle, map_open_error


def _result(
    *,
    ok: bool,
    source_sha: str | None,
    clause_span: list[int] | None,
    clause_sha: str | None,
    text: str | None,
    line_count: int,
    byte_length: int,
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
        "byte_length": byte_length,
        "code": code,
        "first_fail": first_fail,
    }


def line_spans(payload: bytes) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    index = 0
    while index < len(payload):
        value = payload[index]
        if value == 0x0D:
            if index + 1 < len(payload) and payload[index + 1] == 0x0A:
                index += 1
            spans.append((start, index + 1))
            start = index + 1
        elif value == 0x0A:
            spans.append((start, index + 1))
            start = index + 1
        index += 1
    if start < len(payload):
        spans.append((start, len(payload)))
    return spans


def normalize_span(clause_span: Any) -> list[int] | None:
    if clause_span is None:
        return None
    if isinstance(clause_span, (str, bytes)):
        return None
    try:
        values = list(clause_span)
    except TypeError:
        return None
    if (
        len(values) != 2
        or any(type(value) is not int for value in values)
        or values[0] < 1
        or values[1] < values[0]
    ):
        return None
    return [values[0], values[1]]


def decode_payload(payload: bytes, encoding: str) -> str:
    if encoding not in {"UTF-8", "utf-8"}:
        raise UnicodeDecodeError(
            "b0", payload, 0, min(1, len(payload)), "unsupported encoding"
        )
    return payload.decode("utf-8", errors="strict")


def read_bytes(
    verdict: dict[str, Any],
    *,
    expected_sha: str | None = None,
    clause_span: list[int] | tuple[int, int] | None = None,
    encoding: str = "UTF-8",
) -> dict[str, Any]:
    """Read from the approved handle, not by reopening the approved path."""

    span_supplied = clause_span is not None
    requested_span = normalize_span(clause_span)
    if not bool(verdict.get("ok")):
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            byte_length=0,
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
            byte_length=0,
            code="SPAN_INVALID",
            first_fail="SPAN_INVALID",
        )

    handle = verdict.get("handle")
    if not isinstance(handle, WinHandle):
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            byte_length=0,
            code="PATH_IDENTITY_UNVERIFIED",
            first_fail="PATH_IDENTITY_UNVERIFIED",
        )

    try:
        before = handle.identity()
        payload = handle.read_all()
        after = handle.identity()
    except OSError as exc:
        code = map_open_error(exc)
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            byte_length=0,
            code=code,
            first_fail=code,
        )
    if before.tuple != after.tuple or len(payload) != after.size:
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            byte_length=len(payload),
            code="SOURCE_CHANGED",
            first_fail="SOURCE_CHANGED",
        )

    try:
        text = decode_payload(payload, encoding)
    except (LookupError, UnicodeDecodeError):
        return _result(
            ok=False,
            source_sha=None,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=0,
            byte_length=len(payload),
            code="ENCODING_INVALID",
            first_fail="ENCODING_INVALID",
        )
    source_sha = hashlib.sha256(payload).hexdigest()
    spans = line_spans(payload)
    line_count = len(spans)
    if expected_sha is not None and source_sha != expected_sha:
        return _result(
            ok=False,
            source_sha=source_sha,
            clause_span=requested_span,
            clause_sha=None,
            text=None,
            line_count=line_count,
            byte_length=len(payload),
            code="SOURCE_PIN_MISMATCH",
            first_fail="SOURCE_PIN_MISMATCH",
        )

    clause_sha: str | None = None
    if requested_span is not None:
        first_line, last_line = requested_span
        if last_line > line_count or line_count == 0:
            return _result(
                ok=False,
                source_sha=source_sha,
                clause_span=requested_span,
                clause_sha=None,
                text=None,
                line_count=line_count,
                byte_length=len(payload),
                code="SPAN_INVALID",
                first_fail="SPAN_INVALID",
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
        byte_length=len(payload),
        code=None,
        first_fail=None,
    )
