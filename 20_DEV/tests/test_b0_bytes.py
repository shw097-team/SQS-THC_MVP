"""Tests for B0.BYTES v2 raw bytes and physical line spans.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from b0_reader.bytes_ import decode_payload, line_spans, read_bytes
from b0_reader.root import close_root_verdict, open_authorized_file


TEST_TEMP_ROOT = Path.cwd() / ".tmp_tests"


class B0BytesTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _read(
        self,
        payload: bytes,
        *,
        expected_sha: str | None = None,
        clause_span: list[int] | tuple[int, int] | None = None,
        close: bool = True,
    ) -> dict:
        source = self.root / "source.txt"
        source.write_bytes(payload)
        handle, verdict = open_authorized_file(
            source,
            allowed_root=self.root,
        )
        result = read_bytes(
            {**verdict, "handle": handle},
            expected_sha=expected_sha,
            clause_span=clause_span,
        )
        if close:
            handle.close()
            close_root_verdict(verdict)
        else:
            self.addCleanup(handle.close)
            self.addCleanup(close_root_verdict, verdict)
        return result

    def test_valid_digest_text_and_lines(self) -> None:
        payload = "one\ntwo\n".encode()
        result = self._read(payload)
        self.assertTrue(result["ok"])
        self.assertEqual(result["source_sha"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["line_count"], 2)
        self.assertEqual(result["byte_length"], len(payload))
        self.assertEqual(result["text"], "one\ntwo\n")
        self.assertIsNone(result["clause_sha"])

    def test_expected_sha_is_exact_lowercase_sha256(self) -> None:
        payload = b"abc\n"
        digest = hashlib.sha256(payload).hexdigest()
        self.assertTrue(self._read(payload, expected_sha=digest)["ok"])
        self.assertEqual(
            self._read(payload, expected_sha=digest.upper())["code"],
            "SOURCE_PIN_MISMATCH",
        )

    def test_SOURCE_PIN_MISMATCH_retains_observed_sha(self) -> None:
        payload = b"abc\n"
        result = self._read(payload, expected_sha="0" * 64)
        self.assertEqual(result["code"], "SOURCE_PIN_MISMATCH")
        self.assertEqual(result["first_fail"], "SOURCE_PIN_MISMATCH")
        self.assertEqual(
            result["source_sha"],
            hashlib.sha256(payload).hexdigest(),
        )

    def test_CRLF_clause_hash_preserves_carriage_returns(self) -> None:
        payload = b"first\r\nsecond\r\nthird"
        result = self._read(payload, clause_span=[1, 2])
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["clause_sha"],
            hashlib.sha256(b"first\r\nsecond\r\n").hexdigest(),
        )
        self.assertIn("\r\n", result["text"])

    def test_CR_and_LF_are_physical_line_boundaries(self) -> None:
        payload = b"a\rb\nc"
        self.assertEqual(line_spans(payload), [(0, 2), (2, 4), (4, 5)])
        result = self._read(payload, clause_span=[2, 3])
        self.assertEqual(result["line_count"], 3)
        self.assertEqual(
            result["clause_sha"],
            hashlib.sha256(b"b\nc").hexdigest(),
        )

    def test_last_clause_has_no_invented_newline(self) -> None:
        result = self._read(b"first\nlast", clause_span=[2, 2])
        self.assertEqual(
            result["clause_sha"],
            hashlib.sha256(b"last").hexdigest(),
        )

    def test_SPAN_INVALID_for_bad_or_out_of_range_span(self) -> None:
        cases = ("1:2", [0, 1], [1, 3], [2, 1], [-1, 1], [True, 1])
        for span in cases:
            with self.subTest(span=span):
                source = self.root / f"span-{len(str(span))}.txt"
                source.write_bytes(b"one\ntwo\n")
                handle, verdict = open_authorized_file(
                    source,
                    allowed_root=self.root,
                )
                try:
                    result = read_bytes(
                        {**verdict, "handle": handle},
                        clause_span=span,  # type: ignore[arg-type]
                    )
                finally:
                    handle.close()
                    close_root_verdict(verdict)
                self.assertEqual(result["code"], "SPAN_INVALID")
                self.assertEqual(result["first_fail"], "SPAN_INVALID")

    def test_malformed_span_is_SPAN_INVALID(self) -> None:
        result = self._read(b"one\n", clause_span="1:2")  # type: ignore[arg-type]
        self.assertEqual(result["code"], "SPAN_INVALID")

    def test_ENCODING_INVALID_is_strict_utf8(self) -> None:
        result = self._read(b"ok\xffbad")
        self.assertEqual(result["code"], "ENCODING_INVALID")
        self.assertIsNone(result["text"])
        with self.assertRaises(UnicodeDecodeError):
            decode_payload(b"\xff", "UTF-8")

    def test_failed_root_verdict_never_opens(self) -> None:
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
        self.assertIsNone(result["source_sha"])
        self.assertIsNone(result["text"])

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
                "byte_length",
                "code",
                "first_fail",
            },
        )


if __name__ == "__main__":
    unittest.main()
