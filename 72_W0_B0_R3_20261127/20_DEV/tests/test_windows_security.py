"""Wave 2 real-Windows checks for N02 and the OS half of N07.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

All fixtures are actual files below W/20_DEV/.tmp_tests. Real junctions and
Windows sharing locks are used; no path string monkeypatch stands in for an OS
operation.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import unittest
from ctypes import wintypes
from pathlib import Path

from b0_reader import winio
from b0_reader.bytes_ import read_bytes
from b0_reader.root import (
    PathSecurityError,
    canonical_local_path,
    close_root_verdict,
    is_component_contained,
    open_authorized_file,
    validate_path_security,
)
from b0_reader.winio import (
    ERROR_LOCK_VIOLATION,
    ERROR_SHARING_VIOLATION,
    WinHandle,
    WinIOError,
    map_open_error,
)

DEV_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = DEV_ROOT / ".tmp_tests"


class WindowsSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertNotIn(
            "TMPDIR",
            os.environ,
            "the bounded suite requires TMPDIR to be unset",
        )
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "root"
        self.root.mkdir()
        self.source = self.root / "source.txt"
        self.source.write_bytes(b"real-windows-source\n")

    def _assert_path_error(self, path: str | Path, code: str) -> None:
        with self.assertRaises(PathSecurityError) as raised:
            canonical_local_path(path)
        self.assertEqual(raised.exception.code, code)

    def test_N02_real_file_handle_identity_and_same_handle_read(self) -> None:
        handle, verdict = open_authorized_file(
            self.source,
            allowed_root=self.root,
        )
        self.addCleanup(handle.close)
        self.addCleanup(close_root_verdict, verdict)
        identity = handle.identity()
        self.assertFalse(identity.is_reparse)
        self.assertTrue(identity.is_regular_file)
        self.assertEqual(identity.tuple, verdict["identity"])
        self.assertEqual(
            os.path.normcase(identity.final_path),
            os.path.normcase(str(self.source)),
        )
        result = read_bytes({**verdict, "handle": handle})
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["source_sha"],
            hashlib.sha256(self.source.read_bytes()).hexdigest(),
        )

    def test_N02_missing_handle_is_never_reopened_via_path_fallback(self) -> None:
        handle, verdict = open_authorized_file(
            self.source,
            allowed_root=self.root,
        )
        handle.close()
        close_root_verdict(verdict)
        result = read_bytes(verdict)
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "PATH_IDENTITY_UNVERIFIED")
        self.assertIsNone(result["source_sha"])
        self.assertIsNone(result["text"])

    def test_N02_prefix_sibling_is_escape_not_containment(self) -> None:
        sibling = Path(self.temp.name) / "root_evil"
        sibling.mkdir()
        outside = sibling / "outside.txt"
        outside.write_bytes(b"outside\n")
        self.assertFalse(is_component_contained(outside, self.root))
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(outside, allowed_root=self.root)
        self.assertEqual(raised.exception.code, "PATH_ESCAPE")

    def test_N02_ambiguous_path_forms_are_invalid(self) -> None:
        absolute = str(self.source)
        invalid_values = (
            "relative.txt",
            "C:relative.txt",
            absolute + r"\..\outside.txt",
            absolute + r"\.\source.txt",
            r"\\.\C:\source.txt",
            r"\\server\share\source.txt",
            r"\??\C:\source.txt",
            str(self.root / "bad*name.txt"),
            str(self.root / "bad?name.txt"),
            str(self.root / "bad:ads.txt"),
            str(self.root / "trailing. "),
            str(self.root / "contain\x00nul"),
        )
        for value in invalid_values:
            with self.subTest(value=value):
                self._assert_path_error(value, "PATH_INVALID")

    def test_N02_allowed_root_itself_is_rejected_as_source(self) -> None:
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(self.root, allowed_root=self.root)
        self.assertEqual(raised.exception.code, "PATH_INVALID")

    def test_N02_missing_ancestor_fails_closed_as_identity_unknown(self) -> None:
        missing = self.root / "missing-parent" / "source.txt"
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(missing, allowed_root=self.root)
        self.assertEqual(
            raised.exception.code,
            "PATH_IDENTITY_UNVERIFIED",
        )

    def test_N02_real_child_junction_is_reparse_denied(self) -> None:
        target = self.root / "target"
        target.mkdir()
        (target / "linked.txt").write_bytes(b"linked\n")
        junction = self.root / "junction"
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr.decode(errors="replace"),
        )
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(
                junction / "linked.txt",
                allowed_root=self.root,
            )
        self.assertEqual(raised.exception.code, "PATH_REPARSE_DENIED")

    def test_N02_real_ancestor_junction_is_reparse_denied(self) -> None:
        base = Path(self.temp.name)
        target = base / "ancestor-target"
        target.mkdir()
        (target / "source.txt").write_bytes(b"ancestor\n")
        junction = base / "ancestor-junction"
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr.decode(errors="replace"),
        )
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(
                junction / "source.txt",
                allowed_root=junction,
            )
        self.assertEqual(raised.exception.code, "PATH_REPARSE_DENIED")

    def test_N02_open_share_mode_blocks_mutation_and_path_replacement(self) -> None:
        handle, verdict = open_authorized_file(
            self.source,
            allowed_root=self.root,
        )
        try:
            with self.assertRaises(OSError):
                with open(self.source, "r+b") as stream:
                    stream.write(b"CHANGED")
            with self.assertRaises(OSError):
                os.replace(self.source, self.root / "replacement.txt")
            with self.assertRaises(OSError):
                self.source.unlink()
            self.assertEqual(
                handle.read_all(),
                b"real-windows-source\n",
            )
        finally:
            handle.close()
            close_root_verdict(verdict)
        self.assertEqual(self.source.read_bytes(), b"real-windows-source\n")

    def test_N02_open_share_mode_blocks_ancestor_rename(self) -> None:
        directory = WinHandle.open(str(self.root), directory=True)
        try:
            with self.assertRaises(OSError):
                os.rename(self.root, self.root.with_name("root-renamed"))
            self.assertTrue(self.root.is_dir())
            with WinHandle.open(str(self.root), directory=True) as second:
                self.assertEqual(
                    directory.identity().tuple,
                    second.identity().tuple,
                )
        finally:
            directory.close()

    def test_N02_regular_path_after_close_can_be_replaced(self) -> None:
        held = WinHandle.open(str(self.source))
        original_identity = held.identity().tuple
        held.close()
        replacement = self.root / "new.txt"
        replacement.write_bytes(b"new\n")
        os.replace(replacement, self.source)
        with WinHandle.open(str(self.source)) as reopened:
            replacement_identity = reopened.identity().tuple
        self.assertNotEqual(replacement_identity, original_identity)

    def test_N02_share_violation_maps_to_retryable_source_unavailable(self) -> None:
        error = WinIOError("locked", ERROR_SHARING_VIOLATION)
        self.assertEqual(map_open_error(error), "SOURCE_UNAVAILABLE")
        lock_error = WinIOError("locked", ERROR_LOCK_VIOLATION)
        self.assertEqual(map_open_error(lock_error), "SOURCE_UNAVAILABLE")

    def test_N02_real_share_denied_handle_never_becomes_success(self) -> None:
        parent = winio.WinHandle.open(str(self.root), directory=True)
        self.addCleanup(parent.close)
        original_create = winio._kernel32.CreateFileW
        denied: list[bool] = []

        def create_after_exclusive_holder(
            path: str,
            access: int,
            share: int,
            security: object,
            disposition: int,
            flags: int,
            template: object,
        ) -> wintypes.HANDLE:
            if path.endswith("source.txt") and not denied:
                exclusive = self._create_exclusive_handle(
                    self.source,
                    create_file=original_create,
                )
                denied.append(True)
                try:
                    return original_create(
                        path,
                        access,
                        share,
                        security,
                        disposition,
                        flags,
                        template,
                    )
                finally:
                    self._close_raw_handle(exclusive)
            return original_create(
                path,
                access,
                share,
                security,
                disposition,
                flags,
                template,
            )

        winio._kernel32.CreateFileW = create_after_exclusive_holder
        try:
            with self.assertRaises(WinIOError) as raised:
                open_authorized_file(
                    self.source,
                    allowed_root=self.root,
                )
            self.assertEqual(
                map_open_error(raised.exception),
                "SOURCE_UNAVAILABLE",
            )
        finally:
            winio._kernel32.CreateFileW = original_create
        self.assertTrue(denied)

    def test_N07_closed_handle_cannot_be_mistaken_for_live_identity(self) -> None:
        handle = WinHandle.open(str(self.source))
        identity = handle.identity()
        handle.close()
        with self.assertRaises(WinIOError):
            handle.identity()
        self.assertTrue(identity.is_regular_file)
        self.assertEqual(identity.size, len(b"real-windows-source\n"))

    def test_N07_cancellation_by_close_releases_windows_sharing(self) -> None:
        handle, verdict = open_authorized_file(
            self.source,
            allowed_root=self.root,
        )
        handle.close()
        close_root_verdict(verdict)
        os.replace(self.source, self.root / "renamed.txt")
        self.assertFalse(self.source.exists())
        self.assertEqual(
            (self.root / "renamed.txt").read_bytes(),
            b"real-windows-source\n",
        )

    @staticmethod
    def _create_exclusive_handle(
        path: Path,
        *,
        create_file: object | None = None,
    ) -> wintypes.HANDLE:
        create = winio._kernel32.CreateFileW if create_file is None else create_file
        raw = create(
            winio._windows_path(str(path)),
            winio.GENERIC_READ,
            0,
            None,
            winio.OPEN_EXISTING,
            winio.FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )
        if raw is None or raw.value in (0, winio.INVALID_HANDLE_VALUE):
            raise AssertionError(f"CreateFileW failed: {winio.ctypes.get_last_error()}")
        return raw

    @staticmethod
    def _close_raw_handle(raw: wintypes.HANDLE) -> None:
        if not winio._kernel32.CloseHandle(raw):
            raise AssertionError(f"CloseHandle failed: {winio.ctypes.get_last_error()}")


if __name__ == "__main__":
    unittest.main()
