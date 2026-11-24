"""Tests for B0.BYTES.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from b0_reader.bytes_ import read_bytes
from b0_reader.root import check_root


class B0BytesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _read(
        self,
        payload: bytes,
        *,
        expected_sha: str | None = None,
        clause_span: list[int] | None = None,
    ):
        source = self.root / "source.txt"
        source.write_bytes(payload)
        verdict = check_root(self.root, source)
        self.assertTrue(verdict["ok"])
        return read_bytes(
            verdict,
            expected_sha=expected_sha,
            clause_span=clause_span,
        )

    def test_valid_digest_text_and_lines(self) -> None:
        payload = "one\ntwo\n".encode("utf-8")
        result = self._read(payload)
        self.assertTrue(result["ok"])
        self.assertEqual(result["source_sha"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["line_count"], 2)
        self.assertEqual(result["text"], "one\ntwo\n")
        self.assertIsNone(result["clause_sha"])

    def test_expected_sha_accepts_uppercase_hex(self) -> None:
        payload = b"abc\n"
        result = self._read(payload, expected_sha=hashlib.sha256(payload).hexdigest().upper())
        self.assertTrue(result["ok"])

    def test_SHA_MISMATCH(self) -> None:
        result = self._read(b"abc\n", expected_sha="0" * 64)
        self.assertEqual(result["code"], "SHA_MISMATCH")
        self.assertEqual(result["first_fail"], "SHA_MISMATCH")
        self.assertIsNotNone(result["source_sha"])

    def test_CRLF_clause_hash_preserves_carriage_returns(self) -> None:
        payload = b"first\r\nsecond\r\nthird"
        result = self._read(payload, clause_span=[1, 2])
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["clause_sha"],
            hashlib.sha256(b"first\r\nsecond\r\n").hexdigest(),
        )
        self.assertIn("\r\n", result["text"])

    def test_last_clause_has_no_invented_newline(self) -> None:
        payload = b"first\nlast"
        result = self._read(payload, clause_span=[2, 2])
        self.assertEqual(
            result["clause_sha"],
            hashlib.sha256(b"last").hexdigest(),
        )

    def test_SPAN_OUT_OF_RANGE(self) -> None:
        for span in ([0, 1], [1, 3], [2, 1], [-1, 1]):
            with self.subTest(span=span):
                result = self._read(b"one\ntwo\n", clause_span=span)
                self.assertEqual(result["code"], "SPAN_OUT_OF_RANGE")
                self.assertEqual(result["first_fail"], "SPAN_OUT_OF_RANGE")

    def test_malformed_span_is_SPAN_OUT_OF_RANGE(self) -> None:
        source = self.root / "malformed-span.txt"
        source.write_bytes(b"one\n")
        verdict = check_root(self.root, source)
        result = read_bytes(verdict, clause_span="1:2")
        self.assertEqual(result["code"], "SPAN_OUT_OF_RANGE")

    def test_ENCODING_INVALID_is_strict_utf8(self) -> None:
        result = self._read(b"ok\xffbad")
        self.assertEqual(result["code"], "ENCODING_INVALID")
        self.assertIsNone(result["text"])

    def test_failed_root_verdict_never_opens(self) -> None:
        with patch("b0_reader.bytes_.open") as opened:
            result = read_bytes(
                {
                    "ok": False,
                    "realpath": str(self.root / "x"),
                    "acl_raw": "",
                    "code": "PATH_ESCAPE",
                    "first_fail": "PATH_ESCAPE",
                }
            )
        self.assertEqual(result["code"], "PATH_ESCAPE")
        opened.assert_not_called()

    def test_result_contract_keys(self) -> None:
        result = self._read(b"x")
        self.assertEqual(
            set(result),
            {
                "ok",
                "source_sha",
                "clause_span",
                "clause_sha",
                "text",
                "line_count",
                "code",
                "first_fail",
            },
        )


if __name__ == "__main__":
    unittest.main()
