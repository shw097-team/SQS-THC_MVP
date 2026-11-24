"""B0.ROOT path, reparse-point, ADS, ACL, and identity checks.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import json
import locale
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_MISSING = object()


def _verdict(
    *,
    ok: bool,
    realpath: str,
    acl_raw: str,
    code: str | None,
    first_fail: str | None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "realpath": realpath,
        "acl_raw": acl_raw,
        "code": code,
        "first_fail": first_fail,
    }


def _is_under(path: str, root: str) -> bool:
    try:
        common = os.path.commonpath([path, root])
    except ValueError:
        return False
    return os.path.normcase(os.path.normpath(common)) == os.path.normcase(
        os.path.normpath(root)
    )


def _has_ads_segment(path: str) -> bool:
    _, tail = os.path.splitdrive(path)
    return any(":" in segment for segment in re.split(r"[\\/]", tail) if segment)


def _is_reparse_point(path: str, metadata: os.stat_result) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & reparse_flag) or os.path.islink(path)


def _decode_process_output(value: bytes) -> str:
    for encoding in ("utf-8", locale.getpreferredencoding(False), "mbcs"):
        try:
            return value.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return value.decode("utf-8", errors="replace")


def _read_acl(path: str) -> str:
    try:
        completed = subprocess.run(
            ["icacls", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    output = completed.stdout
    if not output and completed.returncode != 0:
        output = completed.stderr
    return _decode_process_output(output)


def _candidate_identity_strings(path: str) -> set[str]:
    candidates = {os.path.basename(path), Path(path).stem}
    current = Path(path).parent
    for _ in range(4):
        if not current.name:
            break
        candidates.add(current.name)
        current = current.parent
    return candidates


def _identity_from_payload(payload: bytes) -> Mapping[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {}
    try:
        document = json.loads(text)
    except (TypeError, ValueError):
        document = None
    if isinstance(document, Mapping):
        return document
    identity: dict[str, Any] = {}
    for line in text.splitlines()[:20]:
        match = re.match(
            r"^\s*(?:#|//)?\s*(namespace|version|acl_epoch)\s*[:=]\s*(.+?)\s*$",
            line,
            flags=re.IGNORECASE,
        )
        if match:
            identity[match.group(1).lower()] = match.group(2).strip("\"'")
    return identity


def _measure_identity(
    path: str,
    field: str,
    identity_document: Mapping[str, Any],
) -> list[str]:
    values = set(_candidate_identity_strings(path))
    for part in Path(path).parts:
        if part:
            values.add(part)
    raw_value = identity_document.get(field, _MISSING)
    if raw_value is not _MISSING and raw_value is not None:
        values.add(str(raw_value))
    return [value for value in values if value]


def _first_mismatch(
    path: str,
    field: str,
    expected: Any,
    identity_document: Mapping[str, Any],
) -> bool:
    if expected is None:
        return False
    expected_text = str(expected)
    return expected_text not in _measure_identity(path, field, identity_document)


def check_root(
    allowed_root: str | os.PathLike[str],
    source_ref: str | os.PathLike[str],
    *,
    expected_namespace: str | None = None,
    expected_version: str | None = None,
) -> dict[str, Any]:
    """Check that a source is safely contained and readable below a root.

    Path and ACL checks never read source content. Identity metadata is examined
    only after all path, reparse, and readability gates have passed.
    """

    root_raw = os.path.abspath(os.fspath(allowed_root))
    source_raw = os.path.abspath(os.fspath(source_ref))
    source_real = os.path.realpath(source_raw)
    root_real = os.path.realpath(root_raw)

    if not os.path.exists(root_real):
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw="",
            code="ROOT_NOT_FOUND",
            first_fail="ROOT_NOT_FOUND",
        )
    if not os.path.isdir(root_real):
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw="",
            code="ROOT_NOT_DIR",
            first_fail="ROOT_NOT_DIR",
        )
    if not _is_under(source_real, root_real):
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw="",
            code="PATH_ESCAPE",
            first_fail="PATH_ESCAPE",
        )
    if _has_ads_segment(source_raw):
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw="",
            code="ADS_PATH",
            first_fail="ADS_PATH",
        )

    cursor = source_raw
    while True:
        try:
            metadata = os.lstat(cursor)
        except FileNotFoundError:
            metadata = None
        except OSError:
            metadata = None
        if metadata is not None and _is_reparse_point(cursor, metadata):
            return _verdict(
                ok=False,
                realpath=source_real,
                acl_raw="",
                code="REPARSE_POINT",
                first_fail="REPARSE_POINT",
            )
        if os.path.normcase(cursor) == os.path.normcase(root_raw):
            break
        parent = os.path.dirname(cursor)
        if parent == cursor:
            break
        cursor = parent

    acl_raw = _read_acl(source_real)
    identity_document: Mapping[str, Any] = {}
    try:
        with open(source_real, "rb") as stream:
            if expected_namespace is not None or expected_version is not None:
                identity_document = _identity_from_payload(
                    stream.read(1024 * 1024)
                )
    except PermissionError:
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw=acl_raw,
            code="RIGHTS_DENIED",
            first_fail="RIGHTS_DENIED",
        )
    except FileNotFoundError:
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw=acl_raw,
            code="ROOT_NOT_FOUND",
            first_fail="ROOT_NOT_FOUND",
        )
    except IsADirectoryError:
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw=acl_raw,
            code="ROOT_NOT_DIR",
            first_fail="ROOT_NOT_DIR",
        )
    except OSError:
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw=acl_raw,
            code="RIGHTS_DENIED",
            first_fail="RIGHTS_DENIED",
        )

    if _first_mismatch(
        source_raw,
        "namespace",
        expected_namespace,
        identity_document,
    ):
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw=acl_raw,
            code="NAMESPACE_MISMATCH",
            first_fail="NAMESPACE_MISMATCH",
        )
    if _first_mismatch(
        source_raw,
        "version",
        expected_version,
        identity_document,
    ):
        return _verdict(
            ok=False,
            realpath=source_real,
            acl_raw=acl_raw,
            code="VERSION_DRIFT",
            first_fail="VERSION_DRIFT",
        )

    return _verdict(
        ok=True,
        realpath=source_real,
        acl_raw=acl_raw,
        code=None,
        first_fail=None,
    )
