# -*- coding: utf-8 -*-
"""Rights entry for the R3 receiver: trust root, receipt signature, live window, interval.

Three independent evidences must hold before any source byte is touched:
  1. the deployment descriptor is the pinned one and sits in a directory no broad
     principal can write (so the trust root is not caller-authored);
  2. the owner-signed receipt this deployment was configured against still hashes to
     its pin, its Ed25519 signature verifies against the pinned owner public key, and
     its task/scope tuple is the pinned one;
  3. the live window is that same window, is OPEN, not expired, not later than the
     receipt, and carries at least the required effect ceiling.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .wire import Reject, is_int, parse_rfc3339, sha256

EFFECT_ORDER = ["READ_ONLY_PROBE", "REPOSITORY_WRITE", "HOST_OPERATIONS", "USER_DATA_EFFECT"]
MASK_WRITE = 852310  # WriteData|AppendData|WriteExtAttr|DeleteSubdirs|WriteAttr|Delete|ChangePerm|TakeOwn
BROAD_WRITE_SIDS = {
    "S-1-1-0",        # Everyone
    "S-1-5-7",        # Anonymous
    "S-1-5-11",       # Authenticated Users
    "S-1-5-32-545",   # Users
    "S-1-5-32-546",   # Guests
    "S-1-5-21-2687334950-3868438633-1592137926-1003",  # local group CodexSandboxUsers
}
SIGNED_RECEIPT_FIELDS = (
    "window_id", "task_id", "opened_at", "expires_at", "scope", "max_ops",
    "effect_class_ceiling", "policy_epoch_at_open", "enrollments_sha256_at_open",
    "owner_fingerprint",
)


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def acl_entries(path: Path) -> list[dict[str, Any]]:
    """Effective DACL of `path`, by SID (localisation-proof)."""
    ps = (
        "$p='" + str(path).replace("'", "''") + "';"
        "(Get-Acl -LiteralPath $p).Access | ForEach-Object {"
        " $_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value"
        " + '|' + $_.AccessControlType + '|' + [int]$_.FileSystemRights };"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=60)
    if out.returncode != 0:
        raise Reject("TRUST_CONTEXT_UNBOUND", f"ACL unreadable: {out.stderr.strip()[:120]}")
    rows = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        sid, kind, rights = line.split("|")
        rows.append({"sid": sid, "type": kind, "rights": int(rights)})
    return rows


def broad_write_holders(path: Path) -> list[str]:
    holders = []
    for ace in acl_entries(path):
        if ace["type"] != "Allow":
            continue
        if ace["sid"] not in BROAD_WRITE_SIDS:
            continue
        if ace["rights"] & MASK_WRITE:
            holders.append(f'{ace["sid"]}:{ace["rights"]}')
    return holders


def assert_trust_root(descriptor: Path) -> None:
    for target in (descriptor, descriptor.parent):
        holders = broad_write_holders(target)
        if holders:
            raise Reject("TRUST_CONTEXT_UNBOUND",
                         f"broad principal has write on {target.name}: {holders}")


def current_principal() -> str:
    out = subprocess.run(["whoami"], capture_output=True, text=True, check=True).stdout.strip()
    return out.lower()


def verify_receipt_signature(receipt: dict[str, Any], public_hex: str) -> None:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception as exc:  # pragma: no cover - environment guard
        raise Reject("RIGHTS_UNVERIFIED", "ed25519 unavailable") from exc
    if receipt.get("alg") != "ed25519":
        raise Reject("RIGHTS_UNVERIFIED", "receipt alg is not ed25519")
    sig_hex = receipt.get("owner_signature_hex")
    if not isinstance(sig_hex, str) or len(sig_hex) != 128:
        raise Reject("RIGHTS_UNVERIFIED", "receipt signature absent")
    body = {k: receipt.get(k) for k in SIGNED_RECEIPT_FIELDS}
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(
            bytes.fromhex(sig_hex), canon(body))
    except Exception as exc:
        raise Reject("RIGHTS_UNVERIFIED", "receipt signature does not verify") from exc


def check_rights(deployment: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    rights = deployment["rights"]

    if current_principal() != deployment["os_principal"].lower():
        raise Reject("RIGHTS_DENIED", "process principal is not the pinned consumer principal")

    receipt_path = Path(rights["receipt_ref"])
    try:
        receipt_bytes = receipt_path.read_bytes()
    except OSError as exc:
        raise Reject("RIGHTS_UNVERIFIED", "receipt unreadable") from exc
    receipt_sha = sha256(receipt_bytes)
    if receipt_sha != rights["receipt_sha256"]:
        raise Reject("RIGHTS_UNVERIFIED", "receipt hash changed since the deployment was pinned")
    receipt = json.loads(receipt_bytes.decode("utf-8"))

    if list(receipt.get("scope") or []) != list(rights["scope"]):
        raise Reject("RIGHTS_UNVERIFIED", "receipt scope tuple differs (order included)")
    if receipt.get("task_id") != rights["task_id"]:
        raise Reject("RIGHTS_UNVERIFIED", "receipt task id differs")
    if receipt.get("window_id") != rights["receipt_window_id"]:
        raise Reject("RIGHTS_UNVERIFIED", "receipt window id differs from the pin")

    verify_receipt_signature(receipt, deployment["owner_public_hex"])

    state_path = Path(rights["state_ref"])
    try:
        state_bytes = state_path.read_bytes()
    except OSError as exc:
        raise Reject("RIGHTS_UNVERIFIED", "live window unreadable") from exc
    window = json.loads(state_bytes.decode("utf-8"))
    if window.get("window_id") != receipt.get("window_id"):
        raise Reject("RIGHTS_UNVERIFIED", "live window is not the pinned window")
    state = window.get("state")
    if state == "REVOKED":
        raise Reject("RIGHTS_REVOKED", "state=REVOKED")
    if state == "CLOSED":
        raise Reject("RIGHTS_REVOKED", "state=CLOSED")
    if state != "OPEN":
        raise Reject("RIGHTS_UNVERIFIED", f"state={state}")
    live_exp = window.get("expires_at")
    rec_exp = receipt.get("expires_at")
    if not is_int(live_exp) or not is_int(rec_exp):
        raise Reject("RIGHTS_UNVERIFIED", "expiry not an integer epoch")
    if live_exp > rec_exp:
        raise Reject("RIGHTS_UNVERIFIED", "live window expiry exceeds the pinned receipt")
    if int(now.timestamp()) >= live_exp:
        raise Reject("RIGHTS_EXPIRED", "owner window expired")
    ceiling = window.get("effect_class_ceiling")
    need = rights["required_effect_ceiling"]
    if ceiling not in EFFECT_ORDER or need not in EFFECT_ORDER:
        raise Reject("RIGHTS_DENIED", f"unknown effect ceiling {ceiling!r}")
    if EFFECT_ORDER.index(ceiling) < EFFECT_ORDER.index(need):
        raise Reject("RIGHTS_DENIED", f"ceiling {ceiling} < required {need}")
    if window.get("owner_public_hex") and window["owner_public_hex"] != deployment["owner_public_hex"]:
        raise Reject("RIGHTS_UNVERIFIED", "live window owner key differs from the pinned key")
    return {
        "receipt_ref": str(receipt_path),
        "receipt_sha256": receipt_sha,
        "receipt_window_id": receipt.get("window_id"),
        "state_ref": str(state_path),
        "state_sha256": sha256(state_bytes),
        "live_window_id": window.get("window_id"),
        "live_expires_at": live_exp,
        "effect_ceiling": ceiling,
        "task_id": receipt.get("task_id"),
        "scope": list(rights["scope"]),
        "principal": current_principal(),
        "checked_at": now.isoformat(),
    }


def check_envelope_authority(authority: dict[str, Any], rights_state: dict[str, Any],
                             deployment: dict[str, Any], now: datetime,
                             exp: dict[str, Any] | None = None) -> dict[str, Any]:
    """The envelope's own interval and currency, checked against the live receipt."""
    if authority.get("os_principal", "").lower() != deployment["os_principal"].lower():
        raise Reject("RIGHTS_DENIED", "envelope principal is not this consumer's principal")
    if authority.get("disclosure") not in deployment["rights"]["allowed_disclosure"]:
        raise Reject("RIGHTS_DENIED", f"disclosure {authority.get('disclosure')!r} not allowed")
    if authority.get("epoch_strategy") not in deployment["rights"]["epoch_strategy_allowed"]:
        raise Reject("RIGHTS_UNVERIFIED", "epoch strategy not allowed here")
    valid_from = parse_rfc3339(authority.get("valid_from"))
    expires_at = parse_rfc3339(authority.get("expires_at"))
    if expires_at <= valid_from:
        raise Reject("RIGHTS_UNVERIFIED", "authority interval is empty")
    if now < valid_from:
        raise Reject("RIGHTS_NOT_YET_VALID", "envelope authority not yet in force")
    if now >= expires_at:
        raise Reject("ENVELOPE_AUTHORITY_EXPIRED", "envelope authority interval has passed")
    if authority.get("usage_evidence_sha") != rights_state["receipt_sha256"]:
        raise Reject("ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW",
                     "usage evidence is not the receipt in force")
    if exp:
        # the authority block's stated source owner / evidence / revocation state must be the
        # ones the trusted descriptor pinned for *this* source -- not merely well-formed text
        if authority.get("source_owner") != exp.get("source_owner"):
            raise Reject("RIGHTS_UNVERIFIED", "authority.source_owner is not the pinned owner")
        if authority.get("usage_evidence_ref") != exp.get("usage_evidence_ref"):
            raise Reject("RIGHTS_UNVERIFIED", "authority.usage_evidence_ref is not the pinned evidence")
        if authority.get("revocation_check_ref") != exp.get("revocation_check_ref"):
            raise Reject("RIGHTS_UNVERIFIED", "authority.revocation_check_ref is not the pinned state")
        auth_from = parse_rfc3339(exp.get("authorization_valid_from"))
        auth_to = parse_rfc3339(exp.get("authorization_expires_at"))
        if valid_from < auth_from or expires_at > auth_to:
            raise Reject("RIGHTS_UNVERIFIED",
                         "authority interval is not inside the authorised period")
    return {"valid_from": authority["valid_from"], "expires_at": authority["expires_at"],
            "usage_evidence_sha": authority["usage_evidence_sha"],
            "currency": "CURRENT", "checked_at": now.isoformat()}
