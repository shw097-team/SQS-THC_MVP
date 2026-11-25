"""B0.ROOT path, reparse, ACL, handle, and identity checks.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .winio import WinHandle, WinIOError, map_open_error

_INVALID_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')
_DRIVE_ABS = re.compile(r"^[A-Za-z]:\\")
_ACL_SUMMARY = re.compile(
    r"^(Successfully processed 1 files; Failed processing 0 files\.|"
    r"已成功處理 1 個檔案; 0 個檔案處理失敗。?|"
    r"Successfully processed \d+ files?; Failed processing 0 files\.)$"
)
_ACL_ACE = re.compile(
    r"^(?P<principal>.+?):"
    r"(?P<flags>(?:\([A-Z]+\))*)"
    r"(?P<rights>(?:\([A-Z]+\))+)$"
)
_ACL_FLAGS = frozenset(
    {"CI", "OI", "IO", "NP", "I", "ID", "DENY", "ALLOW"}
)
_ACL_RIGHTS = frozenset(
    {
        "F",
        "M",
        "RX",
        "R",
        "W",
        "D",
        "DE",
        "RC",
        "WDAC",
        "WO",
        "S",
        "AS",
        "MA",
        "GR",
        "GW",
        "GE",
        "GA",
        "RD",
        "WD",
        "AD",
        "REA",
        "WEA",
        "X",
        "DC",
        "RA",
        "WA",
    }
)
_ACL_BROAD_PRINCIPALS = frozenset(
    {
        "everyone",
        "users",
        "builtin\\users",
        "authenticated users",
        "nt authority\\authenticated users",
        "anonymous",
        "anonymous logon",
        "nt authority\\anonymous logon",
        "s-1-1-0",
        "s-1-5-32-545",
        "s-1-5-11",
        "s-1-5-7",
    }
)
_ACL_WRITE_RIGHTS = frozenset(
    {"M", "F", "W", "WD", "AD", "DC", "WDAC", "WO", "DE", "GA", "GW", "MA"}
)


class PathSecurityError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _failure(
    code: str,
    *,
    realpath: str = "",
    acl_raw: str = "",
) -> dict[str, Any]:
    return {
        "ok": False,
        "realpath": realpath,
        "acl_raw": acl_raw,
        "code": code,
        "first_fail": code,
    }


def canonical_local_path(value: str | os.PathLike[str]) -> str:
    """Parse an unambiguous absolute local path without repairing syntax."""

    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise PathSecurityError("PATH_INVALID", "path type") from exc
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise PathSecurityError("PATH_INVALID", "empty or NUL")
    if raw.startswith(("\\\\", "//", "\\?\\", "\\\\.\\", "\\Device\\")):
        raise PathSecurityError("PATH_INVALID", "device or UNC")
    if not _DRIVE_ABS.match(raw):
        raise PathSecurityError("PATH_INVALID", "not a drive-absolute path")
    if any(part == ".." for part in re.split(r"[\\/]", raw)):
        raise PathSecurityError("PATH_INVALID", "parent component")
    if any(part == "." for part in re.split(r"[\\/]", raw)):
        raise PathSecurityError("PATH_INVALID", "dot component")
    drive, tail = os.path.splitdrive(raw)
    if not drive or not tail.startswith("\\"):
        raise PathSecurityError("PATH_INVALID", "drive")
    body = tail[1:]
    components = [part for part in re.split(r"[\\/]", body) if part != ""]
    for part in components:
        if _INVALID_CHARS.search(part):
            raise PathSecurityError("PATH_INVALID", "reserved character")
        if part.endswith((".", " ")):
            raise PathSecurityError("PATH_INVALID", "trailing dot or space")
    normalized = drive.upper() + "\\" + "\\".join(components)
    return normalized.rstrip("\\") if components else drive.upper() + "\\"


def path_components(path: str) -> tuple[str, ...]:
    canonical = canonical_local_path(path)
    drive, tail = os.path.splitdrive(canonical)
    body = tail.lstrip("\\")
    return (drive + "\\",) + tuple(
        part for part in body.split("\\") if part
    )


def is_component_contained(path: str, root: str) -> bool:
    source_parts = path_components(path)
    root_parts = path_components(root)
    if len(source_parts) < len(root_parts):
        return False
    return tuple(part.casefold() for part in source_parts[: len(root_parts)]) == tuple(
        part.casefold() for part in root_parts
    )


def _join_components(components: tuple[str, ...], index: int) -> str:
    drive = components[0]
    tail = components[1 : index + 1]
    if not tail:
        return drive
    return drive + "\\".join(tail)


def _parse_acl_output(path: str, raw: str, *, require_sealed: bool = False) -> str:
    """Parse a complete icacls DACL; reject broad write grants when sealed."""

    if not isinstance(raw, str) or not raw.strip():
        raise PathSecurityError(
            "PATH_IDENTITY_UNVERIFIED", "ACL output empty"
        )
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise PathSecurityError("PATH_IDENTITY_UNVERIFIED", "ACL output empty")
    # The trailing summary line is locale-dependent; accept it only when it is
    # not itself an ACE, and never let it substitute for the entry list.
    ace_lines = lines
    if _ACL_ACE.fullmatch(lines[-1]) is None:
        ace_lines = lines[:-1]
    if not ace_lines:
        raise PathSecurityError(
            "PATH_IDENTITY_UNVERIFIED", "ACL summary incomplete"
        )
    prefixes = (
        canonical_local_path(path),
        Path(path).name,
    )
    prefix = next(
        (
            candidate
            for candidate in prefixes
            if ace_lines[0].casefold().startswith(candidate.casefold())
        ),
        None,
    )
    if prefix is None:
        raise PathSecurityError(
            "PATH_IDENTITY_UNVERIFIED", "ACL path prefix mismatch"
        )
    ace_lines[0] = ace_lines[0][len(prefix) :].strip()
    if not ace_lines[0]:
        ace_lines = ace_lines[1:]
    for line in ace_lines:
        if ":" not in line:
            raise PathSecurityError(
                "PATH_IDENTITY_UNVERIFIED", "ACL entry unparseable"
            )
        principal, _, remainder = line.partition(":")
        principal = principal.strip().casefold()
        tokens = [
            token
            for group in re.findall(r"\(([^)]*)\)", remainder)
            for token in group.split(",")
            if token.strip()
        ]
        if not principal:
            raise PathSecurityError(
                "PATH_IDENTITY_UNVERIFIED", "ACL entry has no principal"
            )
        if "mandatory label" in principal:
            # Integrity labels are not access grants.
            continue
        if not tokens:
            raise PathSecurityError(
                "PATH_IDENTITY_UNVERIFIED", "ACL entry has no rights"
            )
        unknown = [token for token in tokens if token not in _ACL_RIGHTS and token not in _ACL_FLAGS]
        if unknown:
            raise PathSecurityError(
                "PATH_IDENTITY_UNVERIFIED", "ACL entry flags or rights unknown"
            )
        flags = {token for token in tokens if token in _ACL_FLAGS}
        rights = {token for token in tokens if token in _ACL_RIGHTS}
        if (
            require_sealed
            and principal in _ACL_BROAD_PRINCIPALS
            and "DENY" not in flags
            and bool(rights & _ACL_WRITE_RIGHTS)
        ):
            raise PathSecurityError(
                "PATH_IDENTITY_UNVERIFIED", "broad principal has write ACL"
            )
    return raw


def _read_acl(path: str, *, require_sealed: bool = False) -> str:
    try:
        result = subprocess.run(
            ["icacls", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PathSecurityError("PATH_IDENTITY_UNVERIFIED", "ACL query failed") from exc
    if result.returncode != 0:
        raise PathSecurityError("PATH_IDENTITY_UNVERIFIED", "ACL query rejected")
    try:
        raw = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw = result.stdout.decode("mbcs")
        except UnicodeDecodeError as exc:
            raise PathSecurityError(
                "PATH_IDENTITY_UNVERIFIED", "ACL undecodable"
            ) from exc
    return _parse_acl_output(path, raw, require_sealed=require_sealed)


def _lstat(path: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise PathSecurityError(
            "PATH_IDENTITY_UNVERIFIED", "lstat unavailable"
        ) from exc


def _reparse(metadata: os.stat_result) -> bool:
    return bool(
        getattr(metadata, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def validate_path_security(
    path: str | os.PathLike[str],
    *,
    allowed_root: str | os.PathLike[str],
    final_component_is_file: bool = True,
    require_sealed: bool = False,
) -> tuple[str, str]:
    """Check every ancestor to drive root and every component inside the root.

    ``require_sealed`` applies the trust-anchor rule (no broad-principal write)
    and is used for the deployment descriptor and its ancestors; ordinary
    sources are governed by the caller's OS token and the same-handle identity.
    """

    canonical = canonical_local_path(path)
    root = canonical_local_path(allowed_root)
    if not is_component_contained(canonical, root):
        raise PathSecurityError("PATH_ESCAPE")
    if tuple(part.casefold() for part in path_components(root)) == tuple(
        part.casefold() for part in path_components(canonical)
    ):
        raise PathSecurityError("PATH_INVALID", "source must descend from root")

    source_components = path_components(canonical)
    root_components = path_components(root)
    checked: list[str] = []
    for index in range(1, len(root_components) + 1):
        current = _join_components(source_components, index - 1)
        metadata = _lstat(current)
        if _reparse(metadata):
            raise PathSecurityError("PATH_REPARSE_DENIED")
        checked.append(current)
    for index in range(len(root_components), len(source_components) + 1):
        current = _join_components(source_components, index - 1)
        metadata = _lstat(current)
        if _reparse(metadata):
            raise PathSecurityError("PATH_REPARSE_DENIED")
        expected_directory = index < len(source_components) or not final_component_is_file
        if expected_directory and not stat.S_ISDIR(metadata.st_mode):
            raise PathSecurityError("PATH_IDENTITY_UNVERIFIED")
        if (
            index == len(source_components)
            and final_component_is_file
            and not stat.S_ISREG(metadata.st_mode)
        ):
            raise PathSecurityError("PATH_IDENTITY_UNVERIFIED")
        checked.append(current)
    # The sealed (trust-anchor) rule applies to the descriptor/code file and its
    # immediate parent only: drive-root and higher ancestors always inherit broad
    # ACEs on Windows, so applying it to every ancestor would make any read fail.
    sealed_scope = {canonical.casefold(), os.path.dirname(canonical).casefold()}
    for current in dict.fromkeys(checked):
        _read_acl(
            current,
            require_sealed=require_sealed and current.casefold() in sealed_scope,
        )
    return canonical, root


def _ancestor_paths(canonical: str) -> list[str]:
    source_components = path_components(canonical)
    return [
        _join_components(source_components, index - 1)
        for index in range(1, len(source_components))
    ]


def open_authorized_file(
    path: str | os.PathLike[str],
    *,
    allowed_root: str | os.PathLike[str],
) -> tuple[WinHandle, dict[str, Any]]:
    """Open an unambiguous contained file and prove its final identity."""

    canonical, root = validate_path_security(path, allowed_root=allowed_root)
    directory_handles: list[WinHandle] = []
    handle: WinHandle | None = None
    try:
        for current in _ancestor_paths(canonical):
            directory_handle = WinHandle.open(current, directory=True)
            directory_handles.append(directory_handle)
            opened_directory = directory_handle.identity()
            if (
                opened_directory.is_reparse
                or os.path.normcase(opened_directory.final_path)
                != os.path.normcase(current)
            ):
                raise PathSecurityError("PATH_REPARSE_DENIED")
        handle = WinHandle.open(canonical)
        opened = handle.identity()
        if opened.is_reparse:
            raise PathSecurityError("PATH_REPARSE_DENIED")
        if os.path.normcase(opened.final_path) != os.path.normcase(canonical):
            raise PathSecurityError("PATH_IDENTITY_UNVERIFIED")
    except BaseException:
        if handle is not None:
            handle.close()
        for directory_handle in directory_handles:
            directory_handle.close()
        raise
    verdict = {
        "ok": True,
        "realpath": opened.final_path,
        "acl_raw": _read_acl(canonical),
        "code": None,
        "first_fail": None,
        "canonical_path": canonical,
        "allowed_root": root,
        "identity": opened.tuple,
        "size": opened.size,
        "directory_handles": directory_handles,
    }
    return handle, verdict


def close_root_verdict(verdict: Mapping[str, Any]) -> None:
    handles = verdict.get("directory_handles", [])
    if isinstance(handles, list):
        for handle in handles:
            if isinstance(handle, WinHandle):
                handle.close()


def check_root(
    allowed_root: str | os.PathLike[str],
    source_ref: str | os.PathLike[str],
    *,
    expected_namespace: str | None = None,
    expected_version: str | None = None,
) -> dict[str, Any]:
    """Compatibility ROOT check; callers must not use it as authority."""

    del expected_namespace, expected_version
    if allowed_root is None:
        return _failure("ROOT_UNBOUND")
    try:
        handle, verdict = open_authorized_file(
            source_ref, allowed_root=allowed_root
        )
    except PathSecurityError as exc:
        return _failure(exc.code)
    except WinIOError as exc:
        return _failure(map_open_error(exc))
    except OSError as exc:
        return _failure(map_open_error(exc))
    handle.close()
    close_root_verdict(verdict)
    return {
        "ok": True,
        "realpath": verdict["realpath"],
        "acl_raw": verdict["acl_raw"],
        "code": None,
        "first_fail": None,
    }


def check_expected_identity(
    verdict: Mapping[str, Any],
    *,
    expected_namespace: str | None,
    expected_version: str | None,
    namespace: str | None,
    source_version: str | None,
) -> str | None:
    if expected_namespace is not None and namespace != expected_namespace:
        return "NAMESPACE_MISMATCH"
    if expected_version is not None and source_version != expected_version:
        return "VERSION_MISMATCH"
    return None
