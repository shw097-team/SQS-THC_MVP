"""Trusted Native entry and context construction.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from .errors import is_nonempty_str, is_sha256
from .root import (
    PathSecurityError,
    canonical_local_path,
    validate_path_security,
)
from .winio import (
    WinHandle,
    WinIOError,
    current_principal,
    map_open_error,
    read_optional_file,
)

EXPECTED_DESCRIPTOR_PATH = (
    r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace"
    r"\00_PREFLIGHT\B0_READ_CONTEXT_2026-11-25_r4.json"
)
EXPECTED_DESCRIPTOR_SHA = (
    "b8759ca7f5c213024c4046db07494cabb355d39d051b0082ff043845e9fb45e0"
)
EXPECTED_DESCRIPTOR_BYTES = 3612
CONTEXT_VERSION = "B0TrustedContext/1"

_TRUST_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_CONTEXT_SEAL_KEY = secrets.token_bytes(32)
_OWNER_WINDOW_SCHEMA = "OwnerSigningWindow@1"
_OWNER_WINDOW_TASK_ID = "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH"
_OWNER_WINDOW_SCOPE = (
    "b0_source_read_authority",
    "sqs_thc_ph01_e00",
)
_OWNER_WINDOW_CEILING = "READ_ONLY_PROBE"
_OWNER_WINDOW_KEYS = {
    "schema",
    "task_id",
    "scope",
    "expires_at",
    "max_ops",
    "ops_used",
    "effect_class_ceiling",
    "state",
}


class TrustContextError(Exception):
    def __init__(self, code: str = "TRUST_CONTEXT_UNBOUND") -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class TrustedSource:
    source_id: str
    locator: str
    allowed_root: str
    namespace: str
    source_version: str
    expected_sha: str
    required_set_ref: str
    required_set_sha: str
    required_set_span: tuple[int, int]
    source_owner: str
    usage_evidence_ref: str
    usage_evidence_sha: str
    revocation_check_ref: str


@dataclass(frozen=True, slots=True)
class TrustedContext:
    context_version: str
    context_ref: str
    context_sha: str
    context_bytes: int
    principal: str
    authorization_ref: str
    authorization_sha: str
    scope_id: str
    purpose: str
    consumer_ids: tuple[str, ...]
    valid_from: str
    expires_at: str
    revocation_ref: str
    epoch_strategy: str
    sources: tuple[TrustedSource, ...]
    _seal: str = field(repr=False)

    @property
    def scope_source_ids(self) -> tuple[str, ...]:
        return tuple(source.source_id for source in self.sources)

    def source(self, source_id: str) -> TrustedSource | None:
        for source in self.sources:
            if source.source_id == source_id:
                return source
        return None

def _verify_context(context: Any) -> TrustedContext:
    try:
        if not isinstance(context, TrustedContext):
            raise TrustContextError()
        if (
            context.context_version != CONTEXT_VERSION
            or not isinstance(context._seal, str)
            or not hmac.compare_digest(
                context._seal.encode("ascii"),
                _context_seal(context).encode("ascii"),
            )
        ):
            raise TrustContextError()
    except (TypeError, UnicodeEncodeError, ValueError, AttributeError) as exc:
        raise TrustContextError() from exc
    return context


def _seal_material(context: TrustedContext) -> bytes:
    """Encode exactly the four sealed identity fields without ambiguity."""

    fields = (
        context.context_sha,
        context.principal,
        context.valid_from,
        context.expires_at,
    )
    if any(not isinstance(value, str) for value in fields):
        raise TrustContextError()
    return b"".join(
        len(value.encode("utf-8")).to_bytes(8, "big") + value.encode("utf-8")
        for value in fields
    )


def _context_seal(context: TrustedContext) -> str:
    return hmac.new(
        _CONTEXT_SEAL_KEY,
        _seal_material(context),
        hashlib.sha256,
    ).hexdigest()


def _parse_rfc3339(value: Any) -> datetime:
    if not is_nonempty_str(value):
        raise TrustContextError()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TrustContextError() from exc
    if parsed.tzinfo is None:
        raise TrustContextError()
    return parsed


def _descriptor_json(payload: bytes) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=no_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(value)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise TrustContextError() from exc
    if not isinstance(value, dict):
        raise TrustContextError()
    return value


def _descriptor_source(raw: Any) -> TrustedSource:
    if not isinstance(raw, Mapping):
        raise TrustContextError()
    required = {
        "source_id",
        "locator",
        "allowed_root",
        "namespace",
        "source_version",
        "expected_sha",
        "required_set",
        "source_owner",
        "usage_evidence_ref",
        "usage_evidence_sha",
        "revocation_check_ref",
    }
    if set(raw) != required:
        raise TrustContextError()
    required_set = raw.get("required_set")
    if not isinstance(required_set, Mapping) or set(required_set) != {
        "ref",
        "sha",
        "span",
    }:
        raise TrustContextError()
    for key in (
        "source_id",
        "namespace",
        "source_version",
        "source_owner",
        "usage_evidence_ref",
        "revocation_check_ref",
    ):
        if not is_nonempty_str(raw.get(key)):
            raise TrustContextError()
    if not is_sha256(raw.get("expected_sha")):
        raise TrustContextError()
    if not is_sha256(raw.get("usage_evidence_sha")):
        raise TrustContextError()
    if not is_sha256(required_set.get("sha")):
        raise TrustContextError()
    span = required_set.get("span")
    if (
        not isinstance(span, list)
        or len(span) != 2
        or any(type(item) is not int for item in span)
        or span[0] < 1
        or span[1] < span[0]
    ):
        raise TrustContextError()
    try:
        locator = canonical_local_path(raw.get("locator"))
        allowed_root = canonical_local_path(raw.get("allowed_root"))
        required_ref = canonical_local_path(required_set.get("ref"))
    except (PathSecurityError, OSError) as exc:
        raise TrustContextError() from exc
    return TrustedSource(
        source_id=raw["source_id"],
        locator=locator,
        allowed_root=allowed_root,
        namespace=raw["namespace"],
        source_version=raw["source_version"],
        expected_sha=raw["expected_sha"],
        required_set_ref=required_ref,
        required_set_sha=required_set["sha"],
        required_set_span=(span[0], span[1]),
        source_owner=raw["source_owner"],
        usage_evidence_ref=raw["usage_evidence_ref"],
        usage_evidence_sha=raw["usage_evidence_sha"],
        revocation_check_ref=raw["revocation_check_ref"],
    )


def _parse_descriptor(
    payload: bytes,
    *,
    principal: str,
    now: datetime,
    allow_expired: bool = False,
) -> TrustedContext:
    document = _descriptor_json(payload)
    required = {
        "allowed_principal",
        "authorization_note",
        "authorization_ref",
        "authorization_sha",
        "context_version",
        "epoch_note",
        "epoch_strategy",
        "expires_at",
        "revocation_ref",
        "scope",
        "sources",
        "valid_from",
    }
    if set(document) != required:
        raise TrustContextError()
    if document.get("context_version") != CONTEXT_VERSION:
        raise TrustContextError()
    if document.get("allowed_principal") != principal:
        raise TrustContextError()
    for key in (
        "authorization_ref",
        "authorization_note",
        "epoch_note",
        "revocation_ref",
    ):
        if not is_nonempty_str(document.get(key)):
            raise TrustContextError()
    if not is_sha256(document.get("authorization_sha")):
        raise TrustContextError()
    if document.get("epoch_strategy") != "LIVE_REVALIDATE":
        raise TrustContextError()
    scope = document.get("scope")
    if not isinstance(scope, Mapping) or set(scope) != {
        "consumer_ids",
        "purpose",
        "scope_id",
        "source_ids",
    }:
        raise TrustContextError()
    if not is_nonempty_str(scope.get("scope_id")) or not is_nonempty_str(
        scope.get("purpose")
    ):
        raise TrustContextError()
    for key in ("consumer_ids", "source_ids"):
        value = scope.get(key)
        if (
            not isinstance(value, list)
            or not value
            or any(not is_nonempty_str(item) for item in value)
            or value != sorted(value)
            or len(value) != len(set(value))
            or any(item == "*" for item in value)
        ):
            raise TrustContextError()
    raw_sources = document.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise TrustContextError()
    sources = tuple(_descriptor_source(raw) for raw in raw_sources)
    source_ids = [source.source_id for source in sources]
    if (
        source_ids != sorted(source_ids)
        or len(source_ids) != len(set(source_ids))
        or source_ids != scope["source_ids"]
    ):
        raise TrustContextError()
    valid_from = _parse_rfc3339(document.get("valid_from"))
    expires_at = _parse_rfc3339(document.get("expires_at"))
    if valid_from > expires_at or now < valid_from:
        raise TrustContextError()
    if not allow_expired and now >= expires_at:
        raise TrustContextError("RIGHTS_EXPIRED")
    context_sha = hashlib.sha256(payload).hexdigest()
    return TrustedContext(
        context_version=CONTEXT_VERSION,
        context_ref=EXPECTED_DESCRIPTOR_PATH,
        context_sha=context_sha,
        context_bytes=len(payload),
        principal=principal,
        authorization_ref=document["authorization_ref"],
        authorization_sha=document["authorization_sha"],
        scope_id=scope["scope_id"],
        purpose=scope["purpose"],
        consumer_ids=tuple(scope["consumer_ids"]),
        valid_from=document["valid_from"],
        expires_at=document["expires_at"],
        revocation_ref=document["revocation_ref"],
        epoch_strategy=document["epoch_strategy"],
        sources=sources,
        _seal="",
    )


def _validated_handle_payload(
    handle: WinHandle,
    *,
    allowed_root: str,
    final_component_is_file: bool,
) -> tuple[bytes, Any]:
    identity = handle.identity()
    if not identity.is_regular_file or not identity.final_path:
        raise TrustContextError()
    try:
        canonical, _ = validate_path_security(
            identity.final_path,
            allowed_root=allowed_root,
            final_component_is_file=final_component_is_file,
        )
    except PathSecurityError as exc:
        raise TrustContextError() from exc
    if os.path.normcase(canonical) != os.path.normcase(identity.final_path):
        raise TrustContextError()
    payload = handle.read_all()
    after = handle.identity()
    if identity.tuple != after.tuple or len(payload) != after.size:
        raise TrustContextError()
    return payload, after


def _open_fixed_descriptor() -> WinHandle:
    root = canonical_local_path(_TRUST_ROOT)
    try:
        validate_path_security(
            EXPECTED_DESCRIPTOR_PATH,
            allowed_root=root,
            require_sealed=True,
        )
    except PathSecurityError as exc:
        raise TrustContextError() from exc
    try:
        return WinHandle.open(EXPECTED_DESCRIPTOR_PATH)
    except WinIOError as exc:
        raise TrustContextError(map_open_error(exc)) from exc


def _read_pinned_descriptor() -> bytes:
    """Read and pin-check the fixed descriptor before trusting its fields."""

    root = canonical_local_path(_TRUST_ROOT)
    try:
        validate_path_security(
            EXPECTED_DESCRIPTOR_PATH,
            allowed_root=root,
            require_sealed=True,
        )
        with _open_fixed_descriptor() as handle:
            payload, _ = _validated_handle_payload(
                handle,
                allowed_root=root,
                final_component_is_file=True,
            )
    except (TrustContextError, PathSecurityError, WinIOError, OSError) as exc:
        raise TrustContextError() from exc
    if len(payload) != EXPECTED_DESCRIPTOR_BYTES:
        raise TrustContextError()
    if hashlib.sha256(payload).hexdigest() != EXPECTED_DESCRIPTOR_SHA:
        raise TrustContextError()
    return payload


def _validated_evidence(path: str) -> bytes:
    """Read one external evidence file through its checked, held handle."""

    canonical = canonical_local_path(path)
    try:
        validate_path_security(
            canonical,
            allowed_root=os.path.dirname(canonical),
        )
        with WinHandle.open(canonical) as handle:
            payload, _ = _validated_handle_payload(
                handle,
                allowed_root=os.path.dirname(canonical),
                final_component_is_file=True,
            )
    except TrustContextError:
        raise
    except (PathSecurityError, WinIOError, OSError) as exc:
        raise TrustContextError("RIGHTS_UNVERIFIED") from exc
    return payload


def _revocation_json(payload: bytes) -> dict[str, Any]:
    try:
        document = _descriptor_json(payload)
    except TrustContextError as exc:
        raise TrustContextError("RIGHTS_UNVERIFIED") from exc
    return document


def _owner_window_is_valid(
    payload: bytes,
    *,
    now: datetime,
    max_expiry: int | None = None,
) -> bool:
    """Return true only for a complete, current, exact-scope OPEN window.

    When ``max_expiry`` is supplied (the descriptor's own expiry), a live window
    that claims a later expiry is refused: a swapped window cannot extend rights
    beyond what the deployment descriptor pinned.
    """

    try:
        document = _revocation_json(payload)
        # The Owner window document carries additional bookkeeping keys
        # (workspace, prompt source, fingerprints); only the required set matters.
        if not _OWNER_WINDOW_KEYS <= set(document):
            return False
        if document.get("schema") != _OWNER_WINDOW_SCHEMA:
            return False
        if document.get("task_id") != _OWNER_WINDOW_TASK_ID:
            return False
        if document.get("state") != "OPEN":
            return False
        if document.get("effect_class_ceiling") != _OWNER_WINDOW_CEILING:
            return False
        scope = document.get("scope")
        if (
            not isinstance(scope, list)
            or any(not is_nonempty_str(item) for item in scope)
            or tuple(scope) != _OWNER_WINDOW_SCOPE
        ):
            return False
        expires_at = document.get("expires_at")
        max_ops = document.get("max_ops")
        ops_used = document.get("ops_used")
        if (
            type(expires_at) is not int
            or type(max_ops) is not int
            or type(ops_used) is not int
            or max_ops <= 0
            or ops_used < 0
            or ops_used >= max_ops
        ):
            return False
        if max_expiry is not None and expires_at > int(max_expiry):
            return False
        return int(now.timestamp()) < expires_at
    except (TrustContextError, OverflowError, OSError, ValueError):
        return False


def _pinned_receipt(context: TrustedContext) -> dict[str, Any] | None:
    """Load the owner-signed receipt this descriptor was built against (hash-pinned)."""

    try:
        payload = read_optional_file(context.authorization_ref)
    except (WinIOError, OSError):
        return None
    if payload is None or hashlib.sha256(payload).hexdigest() != context.authorization_sha:
        return None
    try:
        document = _descriptor_json(payload)
    except TrustContextError:
        return None
    return document


def _window_matches_receipt(window: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
    """The live window must be the very window the receipt was issued for.

    Both identifiers are required: a receipt without them cannot bind a live window,
    so it is treated as unverifiable rather than assumed valid.
    """

    window_id = receipt.get("window_id")
    fingerprint = receipt.get("owner_fingerprint")
    if not is_nonempty_str(window_id) or not is_nonempty_str(fingerprint):
        return False
    return window.get("window_id") == window_id and window.get("owner_fingerprint") == fingerprint


def _revocation_error(
    context: TrustedContext,
    payload: bytes,
    *,
    now: datetime,
) -> str | None:
    """Classify revocation evidence; every non-definitive result is unknown."""

    evidence_sha = hashlib.sha256(payload).hexdigest()
    if evidence_sha in {
        context.authorization_sha,
        context.context_sha,
    }:
        return None
    try:
        document = _revocation_json(payload)
    except TrustContextError:
        return "RIGHTS_UNVERIFIED"
    marker = document.get("state")
    if not isinstance(marker, str):
        return "RIGHTS_UNVERIFIED"
    normalized = marker.strip().upper()
    if normalized in {"CLOSED", "REVOKED"}:
        return "RIGHTS_REVOKED"
    if normalized == "EXPIRED":
        return "RIGHTS_EXPIRED"
    if normalized != "OPEN":
        return "RIGHTS_UNVERIFIED"
    try:
        max_expiry = int(_parse_rfc3339(context.expires_at).timestamp())
    except (TrustContextError, ValueError, OverflowError):
        max_expiry = None
    if document.get("schema") == _OWNER_WINDOW_SCHEMA:
        receipt = _pinned_receipt(context)
        if receipt is None or not _window_matches_receipt(document, receipt):
            return "RIGHTS_UNVERIFIED"
    if _owner_window_is_valid(payload, now=now, max_expiry=max_expiry):
        return None
    expires_at = document.get("expires_at")
    if type(expires_at) is int and int(now.timestamp()) >= expires_at:
        return "RIGHTS_EXPIRED"
    return "RIGHTS_UNVERIFIED"


def _verify_referenced_paths(context: TrustedContext) -> None:
    """Recheck every reference before a context can be used."""

    _validated_evidence(context.authorization_ref)
    for source in context.sources:
        validate_path_security(
            source.locator,
            allowed_root=source.allowed_root,
        )
        _validated_evidence(source.usage_evidence_ref)
        _validated_evidence(source.required_set_ref)
        revocation = source.revocation_check_ref.split("#", 1)[0]
        _validated_evidence(revocation)


def _seal_resolved_context(context: TrustedContext) -> TrustedContext:
    """The sole sealing operation; called only after full resolver validation."""

    if not isinstance(context, TrustedContext) or context._seal != "":
        raise TrustContextError()
    return replace(context, _seal=_context_seal(context))


def _verify_descriptor_binding(
    context: TrustedContext,
    *,
    now: datetime,
) -> None:
    """Bind every context field, including source mappings, to the fixed pin."""

    payload = _read_pinned_descriptor()
    parsed = _parse_descriptor(
        payload,
        principal=context.principal,
        now=now,
        allow_expired=True,
    )
    if replace(context, _seal="") != parsed:
        raise TrustContextError()


def revalidate_trusted_context(trusted_context: Any) -> TrustedContext:
    context = _verify_context(trusted_context)
    now = datetime.now().astimezone()
    if now < _parse_rfc3339(context.valid_from):
        raise TrustContextError()
    if now >= _parse_rfc3339(context.expires_at):
        raise TrustContextError("RIGHTS_EXPIRED")
    try:
        principal = current_principal()
    except WinIOError as exc:
        raise TrustContextError() from exc
    if principal != context.principal:
        raise TrustContextError("RIGHTS_UNVERIFIED")
    _verify_descriptor_binding(context, now=now)
    try:
        _verify_referenced_paths(context)
    except TrustContextError:
        raise
    except (PathSecurityError, WinIOError, OSError) as exc:
        raise TrustContextError("RIGHTS_UNVERIFIED") from exc
    revocation = context.revocation_ref
    if "#" in revocation:
        revocation = revocation.split("#", 1)[0]
    try:
        payload = _validated_evidence(revocation)
    except TrustContextError as exc:
        raise TrustContextError("RIGHTS_UNVERIFIED") from exc
    error = _revocation_error(context, payload, now=now)
    if error is not None:
        raise TrustContextError(error)
    return context


def resolve_context_for_current_principal() -> TrustedContext:
    """Resolve the fixed deployment context; fail closed on every unknown."""

    try:
        payload = _read_pinned_descriptor()
        context = _parse_descriptor(
            payload,
            principal=current_principal(),
            now=datetime.now().astimezone(),
        )
        _verify_referenced_paths(context)
        sealed = _seal_resolved_context(context)
        return revalidate_trusted_context(sealed)
    except TrustContextError:
        raise
    except (WinIOError, OSError, PathSecurityError) as exc:
        raise TrustContextError() from exc
