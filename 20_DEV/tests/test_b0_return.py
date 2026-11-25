"""Tests for B0.RETURN v2 assembly and trusted-context admission.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import builtins
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from b0_reader import cli
from b0_reader.errors import ERROR_CODES, build_envelope, build_error
from b0_reader.native_entry import (
    TrustContextError,
    TrustedContext,
)
from b0_reader.return_ import (
    ORIGINAL_WAVE,
    REQUEST_VERSION,
    SUBJECT,
    WIRE_VERSION,
    InvocationError,
    parse_request,
    read_sources,
)
from tests.trust_fixture import IsolatedProductHarness, raw_baseline


class B0ReturnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = IsolatedProductHarness(self)
        self.root = self.harness.root
        self.context, self.request, self.source = self._fixture()

    def _fixture(self) -> tuple[TrustedContext, dict, Path]:
        artifacts = self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        return context, self.harness.request(context), artifacts.source

    def test_read_set_schema_and_entry_contract(self) -> None:
        result, exit_code = read_sources(
            self.request,
            trusted_context=self.context,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            set(result),
            {
                "wire_version",
                "subject",
                "original_wave",
                "bid",
                "spec_version",
                "candidate_digest",
                "scope",
                "source_manifest",
                "entries",
                "errors",
                "write_set",
                "preimage",
                "fin_order",
                "extensions",
            },
        )
        self.assertEqual(result["wire_version"], WIRE_VERSION)
        self.assertEqual(result["write_set"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["fin_order"], "DENY")
        entry = result["entries"][0]
        self.assertEqual(
            set(entry),
            {
                "source_ref",
                "sha",
                "byte_length",
                "encoding",
                "clause_span",
                "clause_sha",
                "original_id",
                "child_id",
                "polarity",
                "requiredness",
                "owner",
                "provenance",
                "required_fields",
                "observed",
                "missing",
                "authority",
                "acl_epoch",
                "rights_epoch",
            },
        )
        self.assertEqual(entry["missing"], [])
        self.assertEqual(entry["required_fields"], ["read"])
        self.assertEqual(set(entry["authority"]), {
            "source_owner",
            "usage_evidence_ref",
            "usage_evidence_sha",
            "os_principal",
            "verification_method",
            "rights_check_ref",
            "checked_at",
            "valid_from",
            "expires_at",
            "revocation_check_ref",
            "epoch_strategy",
            "epoch_provider_ref",
            "epoch_evidence_ref",
        } | {"disclosure"})

    def test_one_missing_field_entry_uses_exit_two(self) -> None:
        payload = (
            "header\n"
            "- **How／Predicate**：READ 只讀合法來源，不能繼承 DEV 效應。\n".encode()
        )
        rules = [
            {
                "expected_literal": None,
                "field": "missing",
                "method": "MD_LABEL",
                "prefix": "- **Missing**：",
                "source_id": "S1",
                "span": [2, 2],
            },
            {
                "expected_literal": "READ 只讀合法來源，不能繼承 DEV 效應。",
                "field": "read",
                "method": "MD_LABEL",
                "prefix": "- **How／Predicate**：",
                "source_id": "S1",
                "span": [2, 2],
            },
        ]
        self.harness.add_source(
            "S1",
            payload,
            required_fields=("missing", "read"),
            rules=rules,
            requirement_span=(1, 2),
        )
        context = self.harness.resolve()
        request = self.harness.request(context, source_ids=("S1",))
        result, exit_code = read_sources(request, trusted_context=context)
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["entries"][0]["missing"], [
            {
                "field": "missing",
                "reason": "ABSENT",
                "source_ref": "S1",
            }
        ])

    def test_partial_reference_errors_do_not_suppress_valid_entry(self) -> None:
        self.harness.add_source(
            "S2",
            b"second\n",
            rules=[],
            required_fields=(),
            requirement_span=(1, 1),
        )
        context = self.harness.resolve()
        request = self.harness.request(context, source_ids=("S1", "S2"))
        request["sources"][1]["clause_span"] = [1, 2]
        result, exit_code = read_sources(request, trusted_context=context)
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["code"], "SPAN_INVALID")

    def test_build_does_not_open_any_write_mode(self) -> None:
        real_open = builtins.open
        modes: list[str] = []

        def guarded_open(file, mode="r", *args, **kwargs):
            modes.append(mode)
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                raise AssertionError(f"write mode attempted: {mode}")
            return real_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=guarded_open):
            result, exit_code = read_sources(
                self.request,
                trusted_context=self.context,
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["write_set"], [])
        self.assertFalse(any(flag in mode for mode in modes for flag in ("w", "a", "x", "+")))

    def test_error_envelope_v2_contract(self) -> None:
        errors = [
            build_error(
                "loc",
                "SOURCE_PIN_MISMATCH",
                "drift",
                first_fail="SOURCE_PIN_MISMATCH",
                source_id="S1",
                op="BYTES",
                expected_sha="a" * 64,
                observed_sha="b" * 64,
            )
        ]
        envelope = build_envelope(errors, SUBJECT, None)
        self.assertEqual(set(envelope), {
            "wire_version",
            "subject",
            "original_wave",
            "bid",
            "spec_version",
            "candidate_digest",
            "scope",
            "source_manifest",
            "entries",
            "errors",
            "write_set",
            "preimage",
            "fin_order",
            "extensions",
        })
        self.assertEqual(envelope["wire_version"], WIRE_VERSION)
        self.assertEqual(envelope["entries"], [])
        self.assertEqual(
            set(envelope["errors"][0]),
            {
                "source_id",
                "op",
                "code",
                "first_fail",
                "affected_locator",
                "retryable",
                "attempt",
                "resume",
                "expected_sha",
                "observed_sha",
            },
        )

    def test_all_typed_codes_are_fixed(self) -> None:
        expected = (
            "INVOCATION_INVALID",
            "TRUST_CONTEXT_UNBOUND",
            "SUBJECT_MISMATCH",
            "SCOPE_MISMATCH",
            "EFFECT_DENIED",
            "ROOT_UNBOUND",
            "PATH_INVALID",
            "PATH_ESCAPE",
            "PATH_REPARSE_DENIED",
            "PATH_IDENTITY_UNVERIFIED",
            "RIGHTS_UNVERIFIED",
            "RIGHTS_DENIED",
            "RIGHTS_EXPIRED",
            "RIGHTS_REVOKED",
            "EPOCH_STALE",
            "SOURCE_UNAVAILABLE",
            "SOURCE_PIN_MISMATCH",
            "SOURCE_CHANGED",
            "ENCODING_INVALID",
            "NAMESPACE_MISMATCH",
            "VERSION_MISMATCH",
            "SPAN_INVALID",
            "REQUIRED_SET_UNBOUND",
            "REQUIRED_SET_CHANGED",
            "FIELD_NOT_REQUIRED",
            "FIELD_METADATA_UNVERIFIED",
            "CLAUSE_RULE_MISMATCH",
            "WIRE_VERSION_UNSUPPORTED",
            "WIRE_INVALID",
            "TUPLE_MISMATCH",
            "CONSUMER_NOT_YET_EXECUTED",
            "UNKNOWN_RECONCILE_REQUIRED",
            "NATIVE_DEPENDENCY_FAILED",
            "EVIDENCE_TUPLE_MISMATCH",
            "INDEPENDENCE_NOT_PROVEN",
            "PRODUCT_NOT_PROVEN",
        )
        self.assertEqual(ERROR_CODES, expected)

    def test_cli_resolves_trust_before_reading_stdin(self) -> None:
        class FailingStdin(io.BytesIO):
            def read(self, *args, **kwargs):
                raise AssertionError("stdin was read")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch(
            "b0_reader.cli.resolve_context_for_current_principal",
            side_effect=TrustContextError("TRUST_CONTEXT_UNBOUND"),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(
                ["read", "--request-json", "-"],
                stdin=FailingStdin(b"{}"),
            )
        self.assertEqual(code, 64)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "TRUST_CONTEXT_UNBOUND")

    def _cli_pre_content(self, request: dict) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        payload = json.dumps(
            request,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        with patch(
            "b0_reader.cli.resolve_context_for_current_principal",
            return_value=self.context,
        ), patch(
            "b0_reader.return_.open_authorized_file",
            side_effect=AssertionError("source was opened"),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(
                ["read", "--request-json", "-"],
                stdin=io.BytesIO(payload),
            )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_scope_error_keeps_scope_mismatch_code(self) -> None:
        request = {**self.request, "scope_id": "wrong-scope"}
        code, stdout, stderr = self._cli_pre_content(request)
        self.assertEqual(code, 64)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "SCOPE_MISMATCH")

    def test_cli_effect_denied_is_not_relabeled_as_invocation_invalid(
        self,
    ) -> None:
        variants = (
            {**self.request, "effect": "DEV"},
            {**self.request, "write_set": ["source"]},
        )
        for request in variants:
            with self.subTest(fields=set(request) - set(self.request)):
                code, stdout, stderr = self._cli_pre_content(request)
                self.assertEqual(code, 64)
                self.assertEqual(stdout, "")
                self.assertEqual(stderr, "EFFECT_DENIED")

    def test_cli_source_outside_scope_is_pre_content_scope_mismatch(
        self,
    ) -> None:
        request = {
            **self.request,
            "sources": [
                {
                    **self.request["sources"][0],
                    "source_id": "OUTSIDE-SCOPE",
                }
            ],
        }
        code, stdout, stderr = self._cli_pre_content(request)
        self.assertEqual(code, 64)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "SCOPE_MISMATCH")

    def test_cli_pin_mismatch_is_typed_exit_two_before_source_read(
        self,
    ) -> None:
        request = {
            **self.request,
            "sources": [
                {
                    **self.request["sources"][0],
                    "expected_sha": "0" * 64,
                }
            ],
        }
        code, stdout, stderr = self._cli_pre_content(request)
        self.assertEqual(code, 2)
        self.assertEqual(stderr, "SOURCE_PIN_MISMATCH")
        envelope = json.loads(stdout)
        self.assertEqual(envelope["entries"], [])
        self.assertEqual(envelope["errors"][0]["code"], "SOURCE_PIN_MISMATCH")
        self.assertEqual(envelope["errors"][0]["op"], "BYTES")
        self.assertNotIn(self.source.read_text(encoding="utf-8"), stdout)

    def test_cli_pinned_span_mismatch_is_typed_exit_two_before_source_read(
        self,
    ) -> None:
        request = {
            **self.request,
            "sources": [
                {
                    **self.request["sources"][0],
                    "clause_span": [1, 1],
                }
            ],
        }
        code, stdout, stderr = self._cli_pre_content(request)
        self.assertEqual(code, 2)
        self.assertEqual(stderr, "SPAN_INVALID")
        envelope = json.loads(stdout)
        self.assertEqual(envelope["entries"], [])
        self.assertEqual(envelope["errors"][0]["code"], "SPAN_INVALID")
        self.assertEqual(envelope["errors"][0]["op"], "BYTES")
        self.assertNotIn(self.source.read_text(encoding="utf-8"), stdout)

    def test_parse_request_rejects_unknown_and_duplicate_keys(self) -> None:
        valid = json.dumps(self.request).encode()
        self.assertEqual(parse_request(valid)["sources"][0]["source_id"], "S1")
        duplicate = valid.replace(b"{\"request_version\"", b"{\"request_version\":1,\"request_version\"", 1)
        with self.assertRaises(InvocationError):
            parse_request(duplicate)
        unknown = dict(self.request)
        unknown["unknown"] = True
        with self.assertRaises(InvocationError):
            parse_request(json.dumps(unknown).encode())


if __name__ == "__main__":
    unittest.main()
