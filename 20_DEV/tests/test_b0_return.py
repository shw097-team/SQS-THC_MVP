"""Tests for B0.RETURN and SourceErrorEnvelope conversion.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import builtins
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from b0_reader.errors import ERROR_CODES, build_error
from b0_reader.return_ import build_read_set, to_envelope


class B0ReturnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.txt"
        self.source.write_text("alpha\nbeta\n", encoding="utf-8")

    def _ref(self, **updates):
        ref = {
            "allowed_root": self.root,
            "source_ref": self.source,
            "required_fields": ["alpha"],
            "observed": {"alpha": "verified"},
            "verified_by_source": {"alpha": True},
            "original_id": "REQ-12",
            "child_id": "AUTHOR-SPLIT-01",
            "polarity": "POS",
            "requiredness": "required",
            "owner": "AUTHOR",
            "locator": "REQ-12::AUTHOR-SPLIT-01",
        }
        ref.update(updates)
        return ref

    def test_read_set_schema_and_entry_contract(self) -> None:
        result = build_read_set(
            "SST/SQS-THC/PH01/E00",
            "scope-a",
            "v1",
            [self._ref()],
        )
        self.assertEqual(
            set(result),
            {
                "schema",
                "subject",
                "scope",
                "batch_id",
                "version",
                "entries",
                "errors",
                "write_set",
            },
        )
        self.assertEqual(result["schema"], "B0.SOURCE_READ_SET/1")
        self.assertEqual(result["batch_id"], "B0")
        self.assertEqual(result["errors"], [])
        self.assertIn("write_set", result)
        self.assertEqual(result["write_set"], [])
        entry = result["entries"][0]
        self.assertEqual(
            set(entry),
            {
                "source_ref",
                "source_sha",
                "clause_span",
                "clause_sha",
                "acl_epoch",
                "rights_epoch",
                "reader",
                "original_id",
                "child_id",
                "polarity",
                "requiredness",
                "owner",
                "required_fields",
                "missing_fields",
                "observed",
                "locator",
            },
        )
        self.assertEqual(
            entry["reader"],
            "B0.ROOT+BYTES+FIELDS(engine)",
        )
        self.assertEqual(entry["observed"], {"alpha": "verified"})

    def test_one_missing_field_does_not_block_entry(self) -> None:
        result = build_read_set(
            "SST/SQS-THC/PH01/E00",
            None,
            "v1",
            [self._ref(required_fields=["alpha", "beta"], observed={"alpha": 1})],
        )
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            result["entries"][0]["missing_fields"],
            [{"field": "beta", "reason": "NOT_OBSERVED"}],
        )

    def test_partial_reference_errors_do_not_suppress_valid_entry(self) -> None:
        missing_source = self.root / "missing.txt"
        result = build_read_set(
            "SST/SQS-THC/PH01/E00",
            None,
            "v1",
            [self._ref(), self._ref(source_ref=missing_source, locator="missing")],
        )
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["code"], "ROOT_NOT_FOUND")
        self.assertTrue(result["errors"][0]["retryable"])

    @unittest.skipUnless(hasattr(Path, "cwd"), "unittest mock needs a real cwd")
    def test_build_does_not_open_any_write_mode(self) -> None:
        real_open = builtins.open
        modes: list[str] = []

        def guarded_open(file, mode="r", *args, **kwargs):
            modes.append(mode)
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                raise AssertionError(f"write mode attempted: {mode}")
            return real_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=guarded_open):
            result = build_read_set(
                "SST/SQS-THC/PH01/E00",
                None,
                "v1",
                [self._ref()],
            )
        self.assertIn("write_set", result)
        self.assertEqual(result["write_set"], [])
        self.assertNotIn("w", modes)
        self.assertNotIn("wb", modes)
        self.assertNotIn("a", modes)

    def test_to_envelope_contract(self) -> None:
        errors = [
            build_error(
                "loc",
                "SHA_MISMATCH",
                "drift",
                first_fail="SHA_MISMATCH",
            )
        ]
        envelope = to_envelope(errors, "subject", "scope")
        self.assertEqual(
            set(envelope),
            {"schema", "subject", "scope", "batch_id", "errors"},
        )
        self.assertEqual(envelope["schema"], "B0.SOURCE_ERROR_ENVELOPE/1")
        self.assertEqual(envelope["batch_id"], "B0")
        self.assertEqual(
            set(envelope["errors"][0]),
            {"affected_locator", "code", "detail", "first_fail", "retryable"},
        )

    def test_all_typed_codes_are_fixed(self) -> None:
        self.assertEqual(
            ERROR_CODES,
            (
                "ROOT_NOT_FOUND",
                "ROOT_NOT_DIR",
                "PATH_ESCAPE",
                "REPARSE_POINT",
                "ADS_PATH",
                "RIGHTS_DENIED",
                "NAMESPACE_MISMATCH",
                "VERSION_DRIFT",
                "ENCODING_INVALID",
                "SHA_MISMATCH",
                "SPAN_OUT_OF_RANGE",
                "REQUIREDNESS_HOLD",
                "SCHEMA_INVALID",
            ),
        )


if __name__ == "__main__":
    unittest.main()
