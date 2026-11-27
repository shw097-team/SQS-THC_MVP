"""Tests for B0.ROOT v2 path and Windows identity checks.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from b0_reader.root import (
    PathSecurityError,
    canonical_local_path,
    check_expected_identity,
    check_root,
    close_root_verdict,
    is_component_contained,
    open_authorized_file,
    validate_path_security,
)


TEST_TEMP_ROOT = Path.cwd() / ".tmp_tests"


class B0RootTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "root"
        self.root.mkdir()
        self.source = self.root / "source.txt"
        self.source.write_bytes(b"payload\n")

    def test_valid_root_uses_the_approved_windows_handle(self) -> None:
        handle, verdict = open_authorized_file(
            self.source,
            allowed_root=self.root,
        )
        self.addCleanup(handle.close)
        self.addCleanup(close_root_verdict, verdict)
        self.assertTrue(verdict["ok"])
        self.assertEqual(
            verdict["canonical_path"],
            canonical_local_path(self.source),
        )
        self.assertEqual(verdict["identity"], handle.identity().tuple)
        self.assertTrue(verdict["acl_raw"])
        self.assertIsNone(verdict["first_fail"])

    def test_ROOT_UNBOUND_is_terminal_and_does_not_read_source(self) -> None:
        verdict = check_root(None, self.source)  # type: ignore[arg-type]
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["code"], "ROOT_UNBOUND")
        self.assertEqual(verdict["first_fail"], "ROOT_UNBOUND")

    def test_PATH_INVALID_rejects_ambiguous_path_forms(self) -> None:
        source = canonical_local_path(self.source)
        invalid = (
            "source.txt",
            str(self.root) + r"\..\outside.txt",
            str(self.root) + r"\.\source.txt",
            r"\\server\share\source.txt",
            r"\\.\C:\source.txt",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(PathSecurityError) as raised:
                    canonical_local_path(value)
                self.assertEqual(raised.exception.code, "PATH_INVALID")
        with self.assertRaises(PathSecurityError) as raised:
            canonical_local_path(source + ":hidden")
        self.assertEqual(raised.exception.code, "PATH_INVALID")
        with self.assertRaises(PathSecurityError) as raised:
            canonical_local_path(str(self.root) + "\\bad*name.txt")
        self.assertEqual(raised.exception.code, "PATH_INVALID")

    def test_PATH_ESCAPE_rejects_component_prefix_sibling(self) -> None:
        sibling_root = Path(self.temp.name) / "root_evil"
        sibling_root.mkdir()
        outside = sibling_root / "outside.txt"
        outside.write_bytes(b"outside\n")
        self.assertFalse(is_component_contained(outside, self.root))
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(outside, allowed_root=self.root)
        self.assertEqual(raised.exception.code, "PATH_ESCAPE")

    def test_PATH_INVALID_rejects_allowed_root_itself(self) -> None:
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(self.root, allowed_root=self.root)
        self.assertEqual(raised.exception.code, "PATH_INVALID")

    def test_PATH_IDENTITY_UNVERIFIED_for_missing_or_non_file_source(self) -> None:
        missing = self.root / "missing.txt"
        directory = self.root / "directory"
        directory.mkdir()
        for source in (missing, directory):
            with self.subTest(source=source.name):
                with self.assertRaises(PathSecurityError) as raised:
                    validate_path_security(source, allowed_root=self.root)
                self.assertEqual(
                    raised.exception.code,
                    "PATH_IDENTITY_UNVERIFIED",
                )

    def test_PATH_REPARSE_DENIED_for_real_junction(self) -> None:
        target = self.root / "target"
        target.mkdir()
        link = self.root / "junction"
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            check=False,
            shell=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr.decode(errors="replace"),
        )
        linked_source = link / "source.txt"
        linked_source.write_bytes(b"linked\n")
        with self.assertRaises(PathSecurityError) as raised:
            validate_path_security(linked_source, allowed_root=self.root)
        self.assertEqual(raised.exception.code, "PATH_REPARSE_DENIED")

    def test_check_root_returns_only_the_compatibility_projection(self) -> None:
        verdict = check_root(self.root, self.source)
        self.assertEqual(
            set(verdict),
            {"ok", "realpath", "acl_raw", "code", "first_fail"},
        )
        self.assertTrue(verdict["ok"])
        self.assertEqual(
            os.path.normcase(verdict["realpath"]),
            os.path.normcase(self.source),
        )

    def test_namespace_and_version_mismatches_are_distinct(self) -> None:
        verdict: dict[str, object] = {}
        self.assertEqual(
            check_expected_identity(
                verdict,
                expected_namespace="tenant-a",
                expected_version="v2",
                namespace="tenant-b",
                source_version="v2",
            ),
            "NAMESPACE_MISMATCH",
        )
        self.assertEqual(
            check_expected_identity(
                verdict,
                expected_namespace="tenant-a",
                expected_version="v2",
                namespace="tenant-a",
                source_version="v3",
            ),
            "VERSION_MISMATCH",
        )
        self.assertIsNone(
            check_expected_identity(
                verdict,
                expected_namespace="tenant-a",
                expected_version="v2",
                namespace="tenant-a",
                source_version="v2",
            )
        )


if __name__ == "__main__":
    unittest.main()
