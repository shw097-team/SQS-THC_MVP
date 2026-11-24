"""Tests for B0.ROOT.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from b0_reader.root import check_root


class B0RootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "root"
        self.root.mkdir()
        self.source = self.root / "source.txt"

    def test_valid_root_and_exact_verdict_keys(self) -> None:
        self.source.write_text("payload\n", encoding="utf-8")
        verdict = check_root(self.root, self.source)
        self.assertEqual(
            set(verdict),
            {"ok", "realpath", "acl_raw", "code", "first_fail"},
        )
        self.assertTrue(verdict["ok"])
        self.assertIsNone(verdict["code"])
        self.assertIsNone(verdict["first_fail"])
        self.assertEqual(verdict["realpath"], os.path.realpath(self.source))
        self.assertIsInstance(verdict["acl_raw"], str)

    def test_acls_are_read_with_icacls(self) -> None:
        self.source.write_text("payload\n", encoding="utf-8")
        completed = subprocess.CompletedProcess(
            ["icacls", str(self.source)],
            0,
            stdout=b"ACL ORIGINAL BYTES",
            stderr=b"",
        )
        with patch("b0_reader.root.subprocess.run", return_value=completed) as run:
            verdict = check_root(self.root, self.source)
        self.assertTrue(verdict["ok"])
        self.assertIn("ACL ORIGINAL BYTES", verdict["acl_raw"])
        self.assertEqual(run.call_args.args[0][0], "icacls")

    def test_ROOT_NOT_FOUND_does_not_read_source_content(self) -> None:
        missing = Path(self.temp.name) / "missing"
        with patch("b0_reader.root.open") as opened:
            verdict = check_root(missing, self.root / "x.txt")
        self.assertEqual(verdict["code"], "ROOT_NOT_FOUND")
        self.assertEqual(verdict["first_fail"], "ROOT_NOT_FOUND")
        opened.assert_not_called()

    def test_ROOT_NOT_DIR(self) -> None:
        not_dir = Path(self.temp.name) / "file"
        not_dir.write_text("x", encoding="utf-8")
        verdict = check_root(not_dir, self.source)
        self.assertEqual(verdict["code"], "ROOT_NOT_DIR")

    def test_PATH_ESCAPE_and_sibling_prefix(self) -> None:
        sibling_root = Path(self.temp.name) / "root_evil"
        sibling_root.mkdir()
        escaped = sibling_root / "source.txt"
        escaped.write_text("outside\n", encoding="utf-8")
        verdict = check_root(self.root, escaped)
        self.assertEqual(verdict["code"], "PATH_ESCAPE")
        self.assertEqual(verdict["first_fail"], "PATH_ESCAPE")

    def test_PATH_ESCAPE_with_parent_traversal(self) -> None:
        escaped = self.root / ".." / "outside.txt"
        escaped.write_text("outside\n", encoding="utf-8")
        verdict = check_root(self.root, escaped)
        self.assertEqual(verdict["code"], "PATH_ESCAPE")

    @unittest.skipUnless(os.name == "nt", "Windows alternate streams")
    def test_ADS_PATH(self) -> None:
        self.source.write_text("payload\n", encoding="utf-8")
        verdict = check_root(self.root, f"{self.source}:hidden")
        self.assertEqual(verdict["code"], "ADS_PATH")

    def test_REPARSE_POINT_with_actual_link_when_available(self) -> None:
        target = self.root / "target"
        target.mkdir()
        created = False
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(self.root / "link"), str(target)],
                    capture_output=True,
                    check=False,
                )
                created = result.returncode == 0
            else:
                os.symlink(target, self.root / "link", target_is_directory=True)
                created = True
        except OSError:
            created = False
        if not created:
            self.skipTest("junction/privileged symlink unavailable")
        verdict = check_root(self.root, self.root / "link")
        self.assertEqual(verdict["code"], "REPARSE_POINT")
        self.assertEqual(verdict["first_fail"], "REPARSE_POINT")

    def test_REPARSE_POINT_attribute_is_rejected(self) -> None:
        self.source.write_text("payload\n", encoding="utf-8")
        with patch(
            "b0_reader.root._is_reparse_point",
            side_effect=lambda path, metadata: os.path.normcase(os.path.abspath(path))
            == os.path.normcase(os.path.abspath(self.source)),
        ):
            verdict = check_root(self.root, self.source)
        self.assertEqual(verdict["code"], "REPARSE_POINT")

    def test_RIGHTS_DENIED(self) -> None:
        self.source.write_text("payload\n", encoding="utf-8")
        with patch("b0_reader.root.open", side_effect=PermissionError):
            verdict = check_root(self.root, self.source)
        self.assertEqual(verdict["code"], "RIGHTS_DENIED")

    def test_NAMESPACE_MISMATCH(self) -> None:
        namespace_root = self.root / "tenant-a"
        namespace_root.mkdir()
        source = namespace_root / "source.txt"
        source.write_text("payload\n", encoding="utf-8")
        verdict = check_root(
            self.root,
            source,
            expected_namespace="tenant-b",
        )
        self.assertEqual(verdict["code"], "NAMESPACE_MISMATCH")

    def test_VERSION_DRIFT(self) -> None:
        version_root = self.root / "v2"
        version_root.mkdir()
        source = version_root / "source.txt"
        source.write_text("payload\n", encoding="utf-8")
        verdict = check_root(self.root, source, expected_version="v3")
        self.assertEqual(verdict["code"], "VERSION_DRIFT")

    def test_identity_expectations_match_when_present(self) -> None:
        namespace_root = self.root / "tenant-a" / "v2"
        namespace_root.mkdir(parents=True)
        source = namespace_root / "source.txt"
        source.write_text("payload\n", encoding="utf-8")
        verdict = check_root(
            self.root,
            source,
            expected_namespace="tenant-a",
            expected_version="v2",
        )
        self.assertTrue(verdict["ok"])


if __name__ == "__main__":
    unittest.main()
