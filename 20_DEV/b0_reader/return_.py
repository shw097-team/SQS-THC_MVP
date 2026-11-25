"""B0.RETURN v2 read-set assembly and per-source accounting.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import time
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .bytes_ import normalize_span, read_bytes
from .errors import is_nonempty_str, is_sha256, make_error, sorted_errors
from .fields import extract_fields
from .native_entry import (
    TrustContextError,
    TrustedContext,
    TrustedSource,
    revalidate_trusted_context,
)
from .requiredset import RequiredSetError, RequiredSetSpec, load_required_set
from .root import (
    PathSecurityError,
    canonical_local_path,
    close_root_verdict,
    open_authorized_file,
)
from .winio import (
    WinHandle,
    WinIOError,
    current_principal,
    map_open_error,
    read_optional_file,
)

WIRE_VERSION = "SST.B0.SourceReadSet/2"
REQUEST_VERSION = "B0ReadRequest/2"
SPEC_VERSION = "2026-11-25_r4_Native-first"
SUBJECT = "SST/SQS-THC/PH01/E00"
ORIGINAL_WAVE = "P1-W00M"
INHERITED_SOURCE_MANIFEST_SHA = (
    "2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e"
)
_REQUEST_KEYS = {
    "request_version",
    "subject",
    "original_wave",
    "bid",
    "effect",
    "write_set",
    "scope_id",
    "sources",
}
_SOURCE_KEYS = {"source_id", "expected_sha", "clause_span"}
_CANDIDATE_RELATIVE_PATHS = (
    "00_PREFLIGHT/B0_READ_CONTEXT_2026-11-25_r4.json",
    "00_PREFLIGHT/required_set_req12_read_all_2026-11-25.json",
    "00_PREFLIGHT/required_set_req12_read_w0m_2026-11-25.json",
    "20_DEV/RUN_TESTS.cmd",
    "20_DEV/b0_reader/__init__.py",
    "20_DEV/b0_reader/bytes_.py",
    "20_DEV/b0_reader/cli.py",
    "20_DEV/b0_reader/controls.py",
    "20_DEV/b0_reader/errors.py",
    "20_DEV/b0_reader/fields.py",
    "20_DEV/b0_reader/native_entry.py",
    "20_DEV/b0_reader/requiredset.py",
    "20_DEV/b0_reader/return_.py",
    "20_DEV/b0_reader/root.py",
    "20_DEV/b0_reader/winio.py",
    "20_DEV/tests/test_b0_bytes.py",
    "20_DEV/tests/test_b0_cases.py",
    "20_DEV/tests/test_b0_fields.py",
    "20_DEV/tests/test_b0_return.py",
    "20_DEV/tests/test_b0_root.py",
    "20_DEV/tests/test_contract_probe.py",
    "20_DEV/tests/test_native_off.py",
    "20_DEV/tests/test_product_read.py",
    "20_DEV/tests/test_windows_security.py",
    "20_DEV/tests/trust_fixture.py",
)
_WORKSPACE_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


class InvocationError(ValueError):
    def __init__(self, code: str = "INVOCATION_INVALID") -> None:
        super().__init__(code)
        self.code = code


def candidate_digest() -> str:
    """Recompute the exact candidate manifest without globbing or symlinks."""

    lines: list[bytes] = []
    root = canonical_local_path(_WORKSPACE_ROOT)
    for relative in sorted(_CANDIDATE_RELATIVE_PATHS):
        path = canonical_local_path(
            os.path.join(root, relative.replace("/", "\\"))
        )
        if not path.startswith(root.rstrip("\\") + "\\"):
            raise InvocationError()
        try:
            metadata = os.lstat(path)
        except OSError as exc:
            raise InvocationError() from exc
        if (
            stat.S_ISLNK(metadata.st_mode)
            or metadata.st_file_attributes
            & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise InvocationError()
        try:
            with WinHandle.open(path) as handle:
                payload = handle.read_all()
        except WinIOError as exc:
            raise InvocationError() from exc
        raw_sha = hashlib.sha256(payload).hexdigest()
        lines.append(
            f"{relative}\t{raw_sha}\t{len(payload)}\n".encode("utf-8")
        )
    return hashlib.sha256(b"".join(lines)).hexdigest()


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvocationError()
        result[key] = value
    return result


def parse_request(payload: bytes) -> dict[str, Any]:
    try:
        document = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                InvocationError()
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise InvocationError() from exc
    if not isinstance(document, dict) or set(document) != _REQUEST_KEYS:
        raise InvocationError()
    if (
        document.get("subject") != SUBJECT
        or document.get("original_wave") != ORIGINAL_WAVE
        or type(document.get("bid")) is not int
        or document.get("bid") != 0
    ):
        raise InvocationError("SUBJECT_MISMATCH")
    if (
        document.get("request_version") != REQUEST_VERSION
        or document.get("effect") != "SOURCE_READ"
        or document.get("write_set") != []
    ):
        raise InvocationError("EFFECT_DENIED")
    if not is_nonempty_str(document.get("scope_id")):
        raise InvocationError()
    sources = document.get("sources")
    if not isinstance(sources, list) or not sources:
        raise InvocationError()
    parsed_sources: list[dict[str, Any]] = []
    source_ids: list[str] = []
    for source in sources:
        if not isinstance(source, dict) or set(source) != _SOURCE_KEYS:
            raise InvocationError()
        source_id = source.get("source_id")
        expected_sha = source.get("expected_sha")
        clause_span = normalize_span(source.get("clause_span"))
        if (
            not is_nonempty_str(source_id)
            or not is_sha256(expected_sha)
            or clause_span is None
        ):
            raise InvocationError()
        source_ids.append(source_id)
        parsed_sources.append(
            {
                "source_id": source_id,
                "expected_sha": expected_sha,
                "clause_span": clause_span,
            }
        )
    if len(source_ids) != len(set(source_ids)):
        raise InvocationError()
    parsed_sources.sort(key=lambda item: item["source_id"])
    return {
        "request_version": REQUEST_VERSION,
        "subject": SUBJECT,
        "original_wave": ORIGINAL_WAVE,
        "bid": 0,
        "effect": "SOURCE_READ",
        "write_set": [],
        "scope_id": document["scope_id"],
        "sources": parsed_sources,
    }


def _same_span(left: Any, right: Any) -> bool:
    return (
        isinstance(left, (list, tuple))
        and isinstance(right, (list, tuple))
        and len(left) == 2
        and len(right) == 2
        and tuple(left) == tuple(right)
    )


def _request_context(
    request: Mapping[str, Any], context: TrustedContext
) -> None:
    sources = request["sources"]
    request_ids = [source["source_id"] for source in sources]
    if request.get("scope_id") != context.scope_id:
        raise InvocationError("SCOPE_MISMATCH")
    allowed_ids = set(context.scope_source_ids)
    if (
        request_ids != sorted(request_ids)
        or len(request_ids) != len(set(request_ids))
        or any(source_id not in allowed_ids for source_id in request_ids)
    ):
        raise InvocationError("SCOPE_MISMATCH")


def _rfc3339_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _error(
    source_id: str,
    op: str,
    code: str,
    *,
    attempt: int = 1,
    expected_sha: str | None = None,
    observed_sha: str | None = None,
) -> dict[str, Any]:
    return make_error(
        source_id,
        op,
        code,
        affected_locator=None,
        retryable=code == "SOURCE_UNAVAILABLE" and attempt == 1,
        attempt=attempt,
        expected_sha=expected_sha if is_sha256(expected_sha) else None,
        observed_sha=observed_sha if is_sha256(observed_sha) else None,
    ).to_wire()


def _validate_request_context(
    request: Any, trusted_context: Any
) -> tuple[dict[str, Any], TrustedContext]:
    try:
        context = revalidate_trusted_context(trusted_context)
    except (TrustContextError, AttributeError) as exc:
        raise InvocationError("TRUST_CONTEXT_UNBOUND") from exc
    if not isinstance(request, Mapping) or set(request) != _REQUEST_KEYS:
        raise InvocationError()
    exact = copy.deepcopy(dict(request))
    if (
        exact.get("request_version") != REQUEST_VERSION
        or exact.get("effect") != "SOURCE_READ"
        or exact.get("write_set") != []
    ):
        raise InvocationError("EFFECT_DENIED")
    if (
        exact.get("subject") != SUBJECT
        or exact.get("original_wave") != ORIGINAL_WAVE
        or type(exact.get("bid")) is not int
        or exact.get("bid") != 0
    ):
        raise InvocationError("SUBJECT_MISMATCH")
    sources = exact.get("sources")
    if not isinstance(sources, list) or not sources:
        raise InvocationError()
    normalized: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, Mapping) or set(source) != _SOURCE_KEYS:
            raise InvocationError()
        source_id = source.get("source_id")
        expected_sha = source.get("expected_sha")
        span = normalize_span(source.get("clause_span"))
        if (
            not is_nonempty_str(source_id)
            or not is_sha256(expected_sha)
            or span is None
        ):
            raise InvocationError()
        normalized.append(
            {
                "source_id": source_id,
                "expected_sha": expected_sha,
                "clause_span": span,
            }
        )
    normalized.sort(key=lambda item: item["source_id"])
    source_ids = [source["source_id"] for source in normalized]
    if len(source_ids) != len(set(source_ids)):
        raise InvocationError()
    exact["sources"] = normalized
    _request_context(exact, context)
    return exact, context


def _load_required_set_for_source(
    trusted: TrustedSource,
) -> RequiredSetSpec:
    return load_required_set(
        trusted.required_set_ref,
        expected_sha=trusted.required_set_sha,
        expected_span=trusted.required_set_span,
        requirement_ref=trusted.locator,
        requirement_sha=trusted.expected_sha,
        expected_source_id=trusted.source_id,
    )


def _verify_evidence(ref: str, expected_sha: str) -> bool:
    try:
        payload = read_optional_file(ref)
    except WinIOError:
        return False
    return (
        payload is not None
        and hashlib.sha256(payload).hexdigest() == expected_sha
    )


def _revalidate_source(
    context: TrustedContext,
    trusted: TrustedSource,
    *,
    handle: WinHandle,
    expected_identity: tuple[int, int, int],
    expected_sha: str,
    expected_size: int,
) -> str | None:
    try:
        revalidate_trusted_context(context)
    except TrustContextError as exc:
        return exc.code
    if not _verify_evidence(
        trusted.usage_evidence_ref, trusted.usage_evidence_sha
    ):
        return "RIGHTS_UNVERIFIED"
    try:
        principal = current_principal()
        identity = handle.identity()
        payload = handle.read_all()
    except WinIOError:
        return "SOURCE_CHANGED"
    if principal != context.principal:
        return "RIGHTS_UNVERIFIED"
    if (
        identity.tuple != expected_identity
        or identity.size != expected_size
        or len(payload) != expected_size
        or hashlib.sha256(payload).hexdigest() != expected_sha
    ):
        return "SOURCE_CHANGED"
    return None


def _entry(
    request_source: Mapping[str, Any],
    trusted: TrustedSource,
    required_set: RequiredSetSpec,
    byte_result: Mapping[str, Any],
    field_result: Mapping[str, Any],
    context: TrustedContext,
) -> dict[str, Any]:
    return {
        "source_ref": {
            "source_id": trusted.source_id,
            "namespace": trusted.namespace,
            "locator": trusted.locator,
            "source_version": trusted.source_version,
        },
        "sha": byte_result["source_sha"],
        "byte_length": byte_result["byte_length"],
        "encoding": "UTF-8",
        "clause_span": list(request_source["clause_span"]),
        "clause_sha": byte_result["clause_sha"],
        "original_id": required_set.original_id,
        "child_id": required_set.child_id,
        "polarity": required_set.polarity,
        "requiredness": required_set.requiredness,
        "owner": required_set.owner,
        "provenance": required_set.provenance(),
        "required_fields": list(required_set.required_fields),
        "observed": field_result["observed"],
        "missing": [
            {
                "field": item["field"],
                "reason": item["reason"],
                "source_ref": trusted.source_id,
            }
            for item in field_result["missing"]
        ],
        "authority": {
            "source_owner": trusted.source_owner,
            "usage_evidence_ref": trusted.usage_evidence_ref,
            "usage_evidence_sha": trusted.usage_evidence_sha,
            "os_principal": context.principal,
            "verification_method": "LIVE_REVALIDATE_OWNER_WINDOW_OS_TOKEN",
            "rights_check_ref": context.authorization_ref,
            "checked_at": _rfc3339_now(),
            "valid_from": context.valid_from,
            "expires_at": context.expires_at,
            "revocation_check_ref": trusted.revocation_check_ref,
            "epoch_strategy": context.epoch_strategy,
            "epoch_provider_ref": None,
            "epoch_evidence_ref": None,
            "disclosure": "LOCAL_ONLY",
        },
        "acl_epoch": None,
        "rights_epoch": None,
    }


def _read_one(
    request_source: Mapping[str, Any],
    trusted: TrustedSource,
    context: TrustedContext,
    *,
    attempt: int = 1,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    source_id = trusted.source_id
    if not _verify_evidence(
        trusted.usage_evidence_ref, trusted.usage_evidence_sha
    ):
        return None, _error(source_id, "ROOT", "RIGHTS_UNVERIFIED")
    if request_source["expected_sha"] != trusted.expected_sha:
        return None, _error(
            source_id,
            "BYTES",
            "SOURCE_PIN_MISMATCH",
            expected_sha=trusted.expected_sha,
        )
    if not _same_span(
        request_source["clause_span"], trusted.required_set_span
    ):
        return None, _error(source_id, "BYTES", "SPAN_INVALID")

    handle: WinHandle | None = None
    verdict: Mapping[str, Any] | None = None
    try:
        handle, verdict = open_authorized_file(
            trusted.locator,
            allowed_root=trusted.allowed_root,
        )
    except PathSecurityError as exc:
        return None, _error(source_id, "ROOT", exc.code)
    except (WinIOError, OSError) as exc:
        code = map_open_error(exc)
        if code == "SOURCE_UNAVAILABLE" and attempt == 1:
            time.sleep(0.05)
            return _read_one(
                request_source,
                trusted,
                context,
                attempt=2,
            )
        return None, _error(
            source_id,
            "ROOT",
            code,
            attempt=attempt,
        )

    try:
        opened = handle.identity()
        byte_result = read_bytes(
            {**dict(verdict), "handle": handle},
            expected_sha=trusted.expected_sha,
            clause_span=request_source["clause_span"],
        )
        if not byte_result["ok"]:
            byte_code = str(byte_result["code"])
            if byte_code == "SOURCE_UNAVAILABLE" and attempt == 1:
                handle.close()
                if verdict is not None:
                    close_root_verdict(verdict)
                time.sleep(0.05)
                return _read_one(
                    request_source,
                    trusted,
                    context,
                    attempt=2,
                )
            return None, _error(
                source_id,
                "BYTES",
                byte_code,
                attempt=attempt,
                expected_sha=trusted.expected_sha,
                observed_sha=byte_result.get("source_sha"),
            )

        payload = handle.read_all()
        if hashlib.sha256(payload).hexdigest() != byte_result["source_sha"]:
            return None, _error(
                source_id,
                "BYTES",
                "SOURCE_CHANGED",
                expected_sha=trusted.expected_sha,
                observed_sha=byte_result["source_sha"],
            )

        try:
            required_set = _load_required_set_for_source(trusted)
        except RequiredSetError as exc:
            return None, _error(source_id, "FIELDS", exc.code)
        field_result = extract_fields(
            required_set,
            payload,
            source_id=source_id,
            source_sha=byte_result["source_sha"],
        )
        if not field_result["ok"]:
            return None, _error(
                source_id, "FIELDS", str(field_result["code"])
            )

        return_error = _revalidate_source(
            context,
            trusted,
            handle=handle,
            expected_identity=opened.tuple,
            expected_sha=byte_result["source_sha"],
            expected_size=byte_result["byte_length"],
        )
        if return_error is not None:
            return None, _error(source_id, "RETURN", return_error)
        return (
            _entry(
                request_source,
                trusted,
                required_set,
                byte_result,
                field_result,
                context,
            ),
            None,
        )
    finally:
        handle.close()
        if verdict is not None:
            close_root_verdict(verdict)


def _envelope_base(
    subject: str, scope: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "wire_version": WIRE_VERSION,
        "subject": subject,
        "original_wave": ORIGINAL_WAVE,
        "bid": 0,
        "spec_version": SPEC_VERSION,
        "candidate_digest": candidate_digest(),
        "scope": dict(scope),
        "source_manifest": {
            "inherited_sha": INHERITED_SOURCE_MANIFEST_SHA,
            "verification": "UNVERIFIED",
            "evidence_ref": None,
        },
        "write_set": [],
        "preimage": "N/A",
        "fin_order": "DENY",
        "extensions": {},
    }


def _scope_for_request(
    request: Mapping[str, Any], context: TrustedContext
) -> dict[str, Any]:
    return {
        "scope_id": context.scope_id,
        "source_ids": [
            source["source_id"] for source in request["sources"]
        ],
        "purpose": context.purpose,
        "consumer_ids": list(context.consumer_ids),
    }


class _FatalResult(dict[str, Any]):
    """Empty result carrier that retains the typed invocation error code."""

    __slots__ = ("code",)

    def __init__(self, code: str) -> None:
        super().__init__()
        self.code = code


def read_sources(
    request: Mapping[str, Any],
    *,
    trusted_context: TrustedContext,
) -> tuple[dict[str, Any], int]:
    """Read requested sources with one entry or fatal error per source."""

    try:
        exact, context = _validate_request_context(request, trusted_context)
    except InvocationError as exc:
        return _FatalResult(exc.code), 64
    except Exception:
        return _FatalResult("UNKNOWN_RECONCILE_REQUIRED"), 70
    scope = _scope_for_request(exact, context)
    entries: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for request_source in exact["sources"]:
        trusted = context.source(request_source["source_id"])
        if trusted is None:
            return {}, 64
        entry, error = _read_one(request_source, trusted, context)
        if error is not None:
            errors.append(error)
        elif entry is not None:
            entries.append(entry)
        else:
            return {}, 70

    entries.sort(key=lambda item: item["source_ref"]["source_id"])
    errors = sorted_errors(errors)
    if len(entries) + len(errors) != len(exact["sources"]):
        return {}, 70
    error_ids = {error["source_id"] for error in errors}
    if any(
        entry["source_ref"]["source_id"] in error_ids for entry in entries
    ):
        return {}, 70
    envelope = {
        **_envelope_base(SUBJECT, scope),
        "entries": entries,
        "errors": errors,
    }
    exit_code = (
        0
        if len(entries) == len(exact["sources"])
        and not errors
        and all(not entry["missing"] for entry in entries)
        else 2
    )
    return envelope, exit_code
