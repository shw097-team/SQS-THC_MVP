"""Wave 2 product-read tests for N01, N03, N04, N05, N06, and N07.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

The fixtures here are isolated OS files under W/20_DEV/.tmp_tests. Trust
contexts are created only by the production resolver after its fixed
descriptor location and pin are redirected to a test fixture.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import b0_reader.native_entry as native_entry
from b0_reader import winio
from b0_reader.errors import build_error
from b0_reader.fields import extract_fields as native_entry_read_fields
from b0_reader.fields import split_fields
from b0_reader.native_entry import (
    TrustContextError,
    TrustedContext,
    revalidate_trusted_context,
)
from b0_reader.return_ import (
    ORIGINAL_WAVE,
    REQUEST_VERSION,
    SUBJECT,
    InvocationError,
    parse_request,
    read_sources,
)
from b0_reader.root import check_expected_identity
from tests.trust_fixture import (
    DEV_ROOT,
    LABEL,
    TEST_TEMP_ROOT,
    IsolatedProductHarness,
    SourceArtifacts,
    raw_baseline,
)

class ProductReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertNotIn(
            "TMPDIR",
            os.environ,
            "the bounded suite requires TMPDIR to be unset",
        )
        temporary = os.environ.get("TEMP", "")
        self.assertEqual(
            os.path.normcase(os.path.abspath(temporary)),
            os.path.normcase(str(TEST_TEMP_ROOT)),
        )
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.harness = IsolatedProductHarness(self)

    def _baseline(self) -> tuple[TrustedContext, dict[str, Any], SourceArtifacts]:
        artifacts = self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        return context, self.harness.request(context), artifacts

    def test_N01_isolated_valid_source_reaches_all_four_operations(self) -> None:
        context, request, artifacts = self._baseline()
        envelope, exit_code = read_sources(
            request,
            trusted_context=context,
        )
        self.assertEqual(exit_code, 0, envelope)
        self.assertEqual(envelope["wire_version"], "SST.B0.SourceReadSet/2")
        self.assertEqual(envelope["write_set"], [])
        self.assertEqual(envelope["preimage"], "N/A")
        self.assertEqual(envelope["fin_order"], "DENY")
        self.assertEqual(envelope["errors"], [])
        self.assertEqual(len(envelope["entries"]), 1)
        entry = envelope["entries"][0]
        self.assertEqual(entry["sha"], artifacts.source_sha)
        self.assertEqual(entry["source_ref"]["source_id"], "S1")
        self.assertEqual(entry["required_fields"], ["read"])
        self.assertEqual(entry["missing"], [])
        self.assertEqual(
            entry["observed"]["read"]["value"],
            "<LOCAL_ONLY_REDACTED>",
        )
        self.assertEqual(len(entry["authority"]), 14)
        self.assertEqual(entry["authority"]["disclosure"], "LOCAL_ONLY")

    def test_N01_missing_trusted_context_fails_before_source_content(self) -> None:
        context, request, artifacts = self._baseline()
        before = artifacts.source.read_bytes()
        envelope, exit_code = read_sources(
            request,
            trusted_context=None,  # type: ignore[arg-type]
        )
        self.assertEqual((envelope, exit_code), ({}, 64))
        self.assertEqual(artifacts.source.read_bytes(), before)
        self.assertIsNotNone(context)

    def test_N01_scope_mismatch_is_pre_content_invocation_rejection(self) -> None:
        context, request, artifacts = self._baseline()
        wrong = {**request, "scope_id": "different-scope"}
        before = artifacts.source.read_bytes()
        self.assertEqual(read_sources(wrong, trusted_context=context), ({}, 64))
        self.assertEqual(artifacts.source.read_bytes(), before)

    def test_N01_fake_usage_evidence_returns_rights_unverified(self) -> None:
        artifacts = self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve(
            source_overrides={"S1": {"usage_evidence_sha": "0" * 64}}
        )
        request = self.harness.request(context)
        envelope, exit_code = read_sources(request, trusted_context=context)
        self.assertEqual(exit_code, 2)
        self.assertEqual(envelope["entries"], [])
        self.assertEqual(envelope["errors"][0]["code"], "RIGHTS_UNVERIFIED")
        self.assertEqual(envelope["errors"][0]["op"], "ROOT")
        self.assertNotIn(
            artifacts.payload.decode("utf-8"),
            json.dumps(envelope, ensure_ascii=False),
        )

    def test_N01_revocation_is_revalidated_before_return(self) -> None:
        context, request, artifacts = self._baseline()
        self.harness._set_owner_state("REVOKED")
        with self.assertRaises(TrustContextError) as raised:
            revalidate_trusted_context(context)
        self.assertEqual(raised.exception.code, "RIGHTS_REVOKED")
        envelope, exit_code = read_sources(request, trusted_context=context)
        self.assertEqual((envelope, exit_code), ({}, 64))
        self.assertEqual(artifacts.source.read_bytes(), raw_baseline())

    def test_N01_revocation_change_after_fields_is_rejected_before_return(
        self,
    ) -> None:
        context, request, artifacts = self._baseline()
        original_extract = native_entry_read_fields
        state = {"changed": False}

        def extract_then_revoke(*args: Any, **kwargs: Any) -> Any:
            result = original_extract(*args, **kwargs)
            if not state["changed"]:
                self.harness._set_owner_state("REVOKED")
                state["changed"] = True
            return result

        with patch(
            "b0_reader.return_.extract_fields",
            side_effect=extract_then_revoke,
        ):
            envelope, exit_code = read_sources(
                request,
                trusted_context=context,
            )
        self.assertTrue(state["changed"])
        self.assertEqual(exit_code, 2)
        self.assertEqual(envelope["entries"], [])
        self.assertEqual(envelope["errors"][0]["op"], "RETURN")
        self.assertEqual(
            envelope["errors"][0]["code"],
            "RIGHTS_REVOKED",
        )
        rendered = json.dumps(envelope, ensure_ascii=False)
        self.assertNotIn(artifacts.payload.decode("utf-8"), rendered)
        self.assertNotIn(
            "READ 只讀合法來源",
            rendered,
        )

    def test_N01_unknown_or_malformed_revocation_fails_as_rights_unverified(
        self,
    ) -> None:
        self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        valid_window = self.harness.owner.read_bytes()
        for payload in (
            b'{"state":"OTHER"}\n',
            b'{"state":',
            b'{"schema":"OwnerSigningWindow@1"}\n',
            b'{"state":"OPEN","state":"OPEN"}\n',
            (
                self.harness.owner.read_text(encoding="utf-8").rstrip()
                + ',"unexpected":true}\n'
            ).encode("utf-8"),
        ):
            with self.subTest(payload=payload):
                self.harness.set_owner_window(payload)
                with self.assertRaises(TrustContextError) as raised:
                    revalidate_trusted_context(context)
                self.assertEqual(
                    raised.exception.code,
                    "RIGHTS_UNVERIFIED",
                )
                self.harness.set_owner_window(valid_window)

    def test_N01_open_revocation_requires_matching_scope_and_unexpired_window(
        self,
    ) -> None:
        self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        now = int(datetime.now(timezone.utc).timestamp())
        invalid = (
            {},
            {"state": "OPEN"},
            {
                "schema": "OwnerSigningWindow@1",
                "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
                "scope": ["wrong", "sqs_thc_ph01_e00"],
                "expires_at": now + 60,
                "max_ops": 10,
                "ops_used": 0,
                "effect_class_ceiling": "READ_ONLY_PROBE",
                "state": "OPEN",
            },
            {
                "schema": "OwnerSigningWindow@1",
                "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
                "scope": [
                    "b0_source_read_authority",
                    "sqs_thc_ph01_e00",
                ],
                "expires_at": now - 1,
                "max_ops": 10,
                "ops_used": 0,
                "effect_class_ceiling": "READ_ONLY_PROBE",
                "state": "OPEN",
            },
        )
        for payload in invalid:
            with self.subTest(payload=payload):
                self.harness.set_owner_window(payload)
                with self.assertRaises(TrustContextError) as raised:
                    revalidate_trusted_context(context)
                self.assertIn(
                    raised.exception.code,
                    {"RIGHTS_UNVERIFIED", "RIGHTS_EXPIRED"},
                )

    def test_R1_live_window_must_be_the_window_the_receipt_was_issued_for(self) -> None:
        """R1.1: OPEN is not enough - the live window must be the receipt's window.

        Three single mutations, each from a valid baseline: a different window id,
        a window without identifiers, and a receipt that cannot bind any window.
        """

        self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        now = int(datetime.now(timezone.utc).timestamp())
        base = {
            "schema": "OwnerSigningWindow@1",
            "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
            "scope": ["b0_source_read_authority", "sqs_thc_ph01_e00"],
            "expires_at": now + 600,
            "max_ops": 100,
            "ops_used": 0,
            "effect_class_ceiling": "READ_ONLY_PROBE",
            "state": "OPEN",
            "window_id": "WIN-test-0001",
            "owner_fingerprint": "test-fingerprint",
        }
        for mutation in (
            {**base, "window_id": "WIN-someone-else"},
            {**base, "owner_fingerprint": "other-fingerprint"},
            {k: v for k, v in base.items() if k not in {"window_id", "owner_fingerprint"}},
        ):
            with self.subTest(mutation=sorted(mutation)):
                self.harness.set_owner_window(mutation)
                with self.assertRaises(TrustContextError) as raised:
                    revalidate_trusted_context(context)
                self.assertEqual(raised.exception.code, "RIGHTS_UNVERIFIED")
                self.harness._set_owner_state("OPEN")

    def test_R1_receipt_without_window_identity_cannot_authorise(self) -> None:
        """R1.1: an unverifiable receipt binding fails closed instead of being assumed valid."""

        self.harness.add_source("S1", raw_baseline())
        self.harness.authorization.write_text(
            '{"kind":"isolated-test-authorization"}\n', encoding="utf-8"
        )
        with self.assertRaises(TrustContextError) as raised:
            self.harness.resolve()
        self.assertEqual(raised.exception.code, "RIGHTS_UNVERIFIED")

    def test_R1_pinned_receipt_bytes_cannot_substitute_for_revocation_state(self) -> None:
        """R1.1/C-R1-03: immutable issuance bytes are not live revocation evidence.

        Swapping the hash-pinned authorization document in as the revocation file must
        fail closed instead of skipping state/schema/window/expiry validation.
        """

        self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        self.harness.set_owner_window(self.harness.authorization.read_bytes())
        with self.assertRaises(TrustContextError) as raised:
            revalidate_trusted_context(context)
        self.assertEqual(raised.exception.code, "RIGHTS_UNVERIFIED")

    def test_N07_source_read_budget_reports_unknown_and_keeps_siblings(self) -> None:
        """N07/R1.3: a source that exceeds the content-read cap is reported UNKNOWN,
        not silently truncated, and its siblings still report independently."""

        import b0_reader.return_ as b0_return

        self.harness.add_source("S1", raw_baseline())
        self.harness.add_source("S2", raw_baseline())
        context = self.harness.resolve()
        request = self.harness.request(context)
        original_read_one = b0_return._read_one
        calls = {"S1": 0}

        def slow_s1(request_source: Any, trusted: Any, ctx: Any, *, attempt: int = 1) -> Any:
            if trusted.source_id == "S1":
                calls["S1"] += 1
                time.sleep(6.0)
            return original_read_one(request_source, trusted, ctx, attempt=attempt)

        with patch.object(b0_return, "_read_one", side_effect=slow_s1), patch.object(
            b0_return, "SOURCE_READ_LIMIT_SECONDS", 4.0
        ):
            envelope, exit_code = read_sources(request, trusted_context=context)

        self.assertEqual(exit_code, 2)
        self.assertEqual([error["source_id"] for error in envelope["errors"]], ["S1"])
        self.assertEqual(envelope["errors"][0]["code"], "UNKNOWN_RECONCILE_REQUIRED")
        self.assertEqual(envelope["errors"][0]["op"], "BYTES")
        self.assertEqual(
            [entry["source_ref"]["source_id"] for entry in envelope["entries"]], ["S2"]
        )
        # The abandoned read still holds its handle until it finishes; the result is
        # UNKNOWN either way, and the source must be readable again afterwards.
        time.sleep(3.5)
        self.assertEqual(self.harness.sources["S1"].source.read_bytes(), raw_baseline())
        for key in b0_return.quarantine_keys("S1"):
            for entry in [b0_return.quarantine_state()[key]]:
                entry["worker"].join(timeout=20)
            self.assertTrue(b0_return.reconcile_source(key))
        self.assertFalse(b0_return.quarantine_keys("S1"))
        self.assertEqual(calls["S1"], 1)

    def test_N07_timed_out_source_is_quarantined_until_reconciled(self) -> None:
        """N07/R1.3 (C-R1-01): no re-entry into a source whose read was abandoned.

        The first call abandons the read; the second call must refuse *without*
        invoking the reader again, and only a reconcile may re-open it.
        """

        import b0_reader.return_ as b0_return

        self.harness.add_source("S1", raw_baseline())
        self.harness.add_source("S2", raw_baseline())
        context = self.harness.resolve()
        request = self.harness.request(context)
        original_read_one = b0_return._read_one
        calls = {"S1": 0}

        def slow_s1(request_source: Any, trusted: Any, ctx: Any, *, attempt: int = 1) -> Any:
            if trusted.source_id == "S1":
                calls["S1"] += 1
                time.sleep(6.0)
            return original_read_one(request_source, trusted, ctx, attempt=attempt)

        try:
            with patch.object(b0_return, "_read_one", side_effect=slow_s1), patch.object(
                b0_return, "SOURCE_READ_LIMIT_SECONDS", 4.0
            ):
                first, first_exit = read_sources(request, trusted_context=context)
            self.assertEqual(first_exit, 2)
            self.assertEqual(
                [e["code"] for e in first["errors"]], ["UNKNOWN_RECONCILE_REQUIRED"]
            )
            self.assertEqual(calls["S1"], 1)
            self.assertTrue(b0_return.quarantine_state())

            # the gate: reconcile is refused while the abandoned worker is still alive
            keys = b0_return.quarantine_keys("S1")
            self.assertEqual(len(keys), 1)
            key = keys[0]
            self.assertFalse(b0_return.reconcile_source(key))
            self.assertEqual(b0_return.quarantine_keys("S1"), [key])

            # second attempt: refused before any reader work happens
            second, second_exit = read_sources(request, trusted_context=context)
            self.assertEqual(second_exit, 2)
            self.assertEqual(
                [e["code"] for e in second["errors"]], ["UNKNOWN_RECONCILE_REQUIRED"]
            )
            self.assertEqual(calls["S1"], 1, "quarantined source must not be re-entered")
            self.assertEqual(
                [entry["source_ref"]["source_id"] for entry in second["entries"]], ["S2"]
            )

            # after the worker terminates reconcile succeeds and the source may be read again
            b0_return.quarantine_state()[key]["worker"].join(timeout=20)
            self.assertTrue(b0_return.reconcile_source(key))
            self.assertEqual(b0_return.quarantine_keys("S1"), [])
            self.assertFalse(b0_return.quarantine_state())
            with patch.object(b0_return, "_read_one", side_effect=slow_s1):
                third, third_exit = read_sources(request, trusted_context=context)
            self.assertEqual(third_exit, 0)
            self.assertEqual(len(third["entries"]), 2)
            self.assertEqual(calls["S1"], 2)
        finally:
            for leftover in b0_return.quarantine_keys("S1"):
                entry = b0_return.quarantine_state().get(leftover)
                if entry and entry.get("worker"):
                    entry["worker"].join(timeout=20)
                b0_return.reconcile_source(leftover)

    def test_N01_valid_open_revocation_window_is_accepted(self) -> None:
        context, _, _ = self._baseline()
        self.assertEqual(revalidate_trusted_context(context), context)

    def test_N01_known_revocation_remains_rights_revoked(self) -> None:
        context, _, _ = self._baseline()
        self.harness._set_owner_state("REVOKED")
        with self.assertRaises(TrustContextError) as raised:
            revalidate_trusted_context(context)
        self.assertEqual(raised.exception.code, "RIGHTS_REVOKED")

    def test_N01_missing_revocation_file_is_rights_unverified(self) -> None:
        context, _, _ = self._baseline()
        self.harness.owner.unlink()
        with self.assertRaises(TrustContextError) as raised:
            revalidate_trusted_context(context)
        self.assertEqual(raised.exception.code, "RIGHTS_UNVERIFIED")

    def test_N01_expired_context_does_not_emit_source_content(self) -> None:
        self.harness.add_source("S1", raw_baseline())
        with self.assertRaises(TrustContextError) as raised:
            self.harness.resolve(expires_delta=timedelta(seconds=-1))
        self.assertEqual(raised.exception.code, "RIGHTS_EXPIRED")

    def test_N01_mint_apis_removed_and_only_resolver_seals_context(self) -> None:
        import ast
        import subprocess
        import sys

        forbidden = {
            "_mint_test_context",
            "_mint_isolated_context",
            "_MINT_KEY",
            "verify_mint",
        }
        self.assertFalse(forbidden & set(dir(native_entry)))
        path = Path(native_entry.__file__)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        functions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        seal_callers = {
            name
            for name, function in functions.items()
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_seal_resolved_context"
        }
        self.assertEqual(
            seal_callers,
            {"resolve_context_for_current_principal"},
        )
        boot = (
            f"import sys;sys.path.insert(0,{str(DEV_ROOT)!r});"
            "import b0_reader.native_entry as n;"
            "print(n._CONTEXT_SEAL_KEY.hex())"
        )
        first = subprocess.run(
            [sys.executable, "-I", "-B", "-c", boot],
            cwd=str(DEV_ROOT),
            capture_output=True,
            check=False,
            timeout=30,
            shell=False,
        )
        second = subprocess.run(
            [sys.executable, "-I", "-B", "-c", boot],
            cwd=str(DEV_ROOT),
            capture_output=True,
            check=False,
            timeout=30,
            shell=False,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(first.stdout, second.stdout)

    def test_N01_tampered_sealed_context_fails_closed(self) -> None:
        context, request, _ = self._baseline()
        tampered = replace(context, expires_at="2099-01-01T00:00:00+00:00")
        with self.assertRaises(TrustContextError) as raised:
            revalidate_trusted_context(tampered)
        self.assertEqual(raised.exception.code, "TRUST_CONTEXT_UNBOUND")
        self.assertEqual(
            read_sources(request, trusted_context=tampered),
            ({}, 64),
        )
        source = replace(context.sources[0], locator=str(self.harness.owner))
        source_tampered = replace(context, sources=(source,))
        with self.assertRaises(TrustContextError) as raised:
            revalidate_trusted_context(source_tampered)
        self.assertEqual(raised.exception.code, "TRUST_CONTEXT_UNBOUND")
        self.assertEqual(
            read_sources(request, trusted_context=source_tampered),
            ({}, 64),
        )
        root_tampered = replace(
            context,
            sources=(
                replace(context.sources[0], allowed_root=str(DEV_ROOT)),
            ),
        )
        self.assertEqual(
            read_sources(request, trusted_context=root_tampered),
            ({}, 64),
        )

    def test_N03_raw_sha_clause_span_and_bom_are_byte_exact(self) -> None:
        payload = raw_baseline()
        artifacts = self.harness.add_source("S1", payload)
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 0)
        entry = envelope["entries"][0]
        self.assertEqual(entry["sha"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(entry["byte_length"], len(payload))
        self.assertEqual(entry["clause_span"], [1, 3])
        self.assertEqual(
            entry["clause_sha"],
            hashlib.sha256(payload).hexdigest(),
        )
        self.assertEqual(artifacts.source.read_bytes(), payload)

    def test_N03_expected_pin_mismatch_preserves_observed_hash(self) -> None:
        self.harness.add_source(
            "S1",
            raw_baseline(),
            expected_sha="0" * 64,
        )
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        error = envelope["errors"][0]
        self.assertEqual(error["op"], "BYTES")
        self.assertEqual(error["code"], "SOURCE_PIN_MISMATCH")
        self.assertEqual(error["expected_sha"], "0" * 64)
        self.assertRegex(error["observed_sha"], r"^[0-9a-f]{64}$")
        self.assertEqual(envelope["entries"], [])

    def test_N03_invalid_utf8_is_encoding_invalid(self) -> None:
        self.harness.add_source("S1", b"ok\xffbad\n")
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(envelope["errors"][0]["op"], "BYTES")
        self.assertEqual(envelope["errors"][0]["code"], "ENCODING_INVALID")
        self.assertNotIn("ok", json.dumps(envelope, ensure_ascii=False))

    def test_N03_out_of_range_span_is_span_invalid(self) -> None:
        self.harness.add_source(
            "S1",
            b"only-line\n",
            requirement_span=(1, 1),
            context_span=(1, 2),
        )
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(envelope["errors"][0]["code"], "SPAN_INVALID")
        self.assertEqual(envelope["entries"], [])

    def test_N03_namespace_and_version_mismatches_stay_distinct(self) -> None:
        self.assertEqual(
            check_expected_identity(
                {},
                expected_namespace="n1",
                expected_version="v1",
                namespace="n2",
                source_version="v1",
            ),
            "NAMESPACE_MISMATCH",
        )
        self.assertEqual(
            check_expected_identity(
                {},
                expected_namespace="n1",
                expected_version="v1",
                namespace="n1",
                source_version="v2",
            ),
            "VERSION_MISMATCH",
        )

    def test_N04_complete_and_one_missing_keep_original_requiredness(self) -> None:
        artifacts = self.harness.add_source(
            "S1",
            raw_baseline(),
            required_fields=("missing", "read"),
            rules=[
                {
                    "field": "missing",
                    "method": "MD_LABEL",
                    "source_id": "S1",
                    "span": [2, 2],
                    "prefix": "- **Missing**：",
                    "expected_literal": None,
                },
                {
                    "field": "read",
                    "method": "MD_LABEL",
                    "source_id": "S1",
                    "span": [2, 2],
                    "prefix": LABEL,
                    "expected_literal": (
                        "<LOCAL_ONLY_REDACTED>"
                    ),
                },
            ],
        )
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        entry = envelope["entries"][0]
        self.assertEqual(entry["required_fields"], ["missing", "read"])
        self.assertEqual(set(entry["observed"]), {"read"})
        self.assertEqual(
            entry["missing"],
            [
                {
                    "field": "missing",
                    "reason": "ABSENT",
                    "source_ref": "S1",
                }
            ],
        )
        self.assertTrue(entry["sha"] == artifacts.source_sha)

    def test_N04_caller_verified_field_is_rejected_by_request_schema(self) -> None:
        context, request, _ = self._baseline()
        forged = {
            **request,
            "sources": [
                {
                    **request["sources"][0],
                    "verified_by_source": True,
                }
            ],
        }
        with self.assertRaises(InvocationError) as raised:
            parse_request(json.dumps(forged).encode("utf-8"))
        self.assertEqual(raised.exception.code, "INVOCATION_INVALID")
        self.assertEqual(read_sources(forged, trusted_context=context), ({}, 64))

    def test_N04_required_set_change_is_detected_by_pinned_hash(self) -> None:
        context, request, artifacts = self._baseline()
        document = json.loads(
            artifacts.required_set.read_text(encoding="utf-8")
        )
        document["required_fields"] = []
        document["rules"] = []
        artifacts.required_set.write_text(
            json.dumps(document, separators=(",", ":")),
            encoding="utf-8",
        )
        envelope, exit_code = read_sources(request, trusted_context=context)
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            envelope["errors"][0]["code"],
            "REQUIRED_SET_CHANGED",
        )
        self.assertEqual(envelope["errors"][0]["op"], "FIELDS")

    def test_N04_cross_source_rule_is_clause_rule_mismatch(self) -> None:
        self.harness.add_source(
            "S1",
            raw_baseline(),
            rules=[
                {
                    "field": "read",
                    "method": "MD_LABEL",
                    "source_id": "S2",
                    "span": [2, 2],
                    "prefix": LABEL,
                    "expected_literal": (
                        "<LOCAL_ONLY_REDACTED>"
                    ),
                }
            ],
        )
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            envelope["errors"][0]["code"],
            "CLAUSE_RULE_MISMATCH",
        )

    def test_N04_unsupported_rule_is_a_missing_reason(self) -> None:
        self.harness.add_source(
            "S1",
            raw_baseline(),
            rules=[
                {
                    "field": "read",
                    "method": "UNSUPPORTED_TEST_FORMAT",
                    "source_id": "S1",
                    "span": [2, 2],
                    "prefix": None,
                    "expected_literal": None,
                }
            ],
        )
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(len(envelope["entries"]), 1)
        self.assertEqual(
            envelope["entries"][0]["missing"][0]["reason"],
            "FORMAT_UNSUPPORTED",
        )

    def test_N04_ambiguous_label_is_missing_not_observed(self) -> None:
        payload = (
            f"{LABEL}first\n{LABEL}second\n".encode("utf-8")
        )
        self.harness.add_source(
            "S1",
            payload,
            rules=[
                {
                    "field": "read",
                    "method": "MD_LABEL",
                    "source_id": "S1",
                    "span": [1, 2],
                    "prefix": LABEL,
                    "expected_literal": None,
                }
            ],
            requirement_span=(1, 2),
        )
        context = self.harness.resolve()
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        entry = envelope["entries"][0]
        self.assertEqual(entry["observed"], {})
        self.assertEqual(entry["missing"][0]["reason"], "AMBIGUOUS")

    def test_N04_extra_field_is_not_silently_required(self) -> None:
        result = split_fields(["read"], {"extra": "caller-value"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["first_fail"], "FIELD_NOT_REQUIRED")
        self.assertNotIn("extra", result["required_fields"])

    def test_N05_brothers_continue_when_one_rights_check_fails(self) -> None:
        self.harness.add_source("S1", raw_baseline())
        self.harness.add_source("S2", raw_baseline())
        self.harness.add_source("S3", raw_baseline())
        context = self.harness.resolve(
            source_overrides={"S2": {"usage_evidence_sha": "0" * 64}}
        )
        envelope, exit_code = read_sources(
            self.harness.request(context),
            trusted_context=context,
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            [entry["source_ref"]["source_id"] for entry in envelope["entries"]],
            ["S1", "S3"],
        )
        self.assertEqual(envelope["errors"][0]["source_id"], "S2")
        self.assertIsNone(envelope["errors"][0]["affected_locator"])

    def test_N05_dev_and_fin_effects_are_denied_before_read(self) -> None:
        context, request, artifacts = self._baseline()
        before = artifacts.source.stat().st_mtime_ns
        for effect in ("DEV", "FIN", "READ_WRITESET"):
            with self.subTest(effect=effect):
                forged = {**request, "effect": effect}
                with self.assertRaises(InvocationError) as raised:
                    parse_request(json.dumps(forged).encode("utf-8"))
                self.assertEqual(raised.exception.code, "EFFECT_DENIED")
        self.assertEqual(artifacts.source.stat().st_mtime_ns, before)
        self.assertEqual(context.epoch_strategy, "LIVE_REVALIDATE")

    def test_N05_nonempty_write_set_is_denied_before_read(self) -> None:
        _, request, artifacts = self._baseline()
        forged = {**request, "write_set": ["source"]}
        with self.assertRaises(InvocationError) as raised:
            parse_request(json.dumps(forged).encode("utf-8"))
        self.assertEqual(raised.exception.code, "EFFECT_DENIED")
        self.assertEqual(artifacts.source.read_bytes(), raw_baseline())

    def test_N05_product_read_does_not_change_fixture_tree_or_bytes(self) -> None:
        context, request, _ = self._baseline()
        before = {
            path.relative_to(self.harness.root).as_posix(): (
                path.read_bytes(),
                path.stat().st_mtime_ns,
            )
            for path in self.harness.root.rglob("*")
            if path.is_file()
        }
        envelope, exit_code = read_sources(
            request,
            trusted_context=context,
        )
        after = {
            path.relative_to(self.harness.root).as_posix(): (
                path.read_bytes(),
                path.stat().st_mtime_ns,
            )
            for path in self.harness.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(exit_code, 0)
        self.assertEqual(envelope["write_set"], [])
        self.assertEqual(after, before)

    def test_N06_envelope_tuple_matches_product_raw_source(self) -> None:
        context, request, artifacts = self._baseline()
        envelope, exit_code = read_sources(
            request,
            trusted_context=context,
        )
        rendered = json.dumps(
            envelope,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(exit_code, 0)
        self.assertFalse(rendered.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(rendered.count(b"SST.B0.SourceReadSet/2"), 1)
        self.assertEqual(json.loads(rendered), envelope)
        self.assertEqual(envelope["entries"][0]["sha"], artifacts.source_sha)

    def test_N07_rights_and_schema_errors_are_not_retryable(self) -> None:
        error = build_error(
            "opaque-S1",
            "RIGHTS_DENIED",
            "not serialized",
            source_id="S1",
            op="ROOT",
        )
        self.assertFalse(error["retryable"])
        pin = build_error(
            "opaque-S1",
            "SOURCE_PIN_MISMATCH",
            "not serialized",
            source_id="S1",
            op="BYTES",
        )
        self.assertFalse(pin["retryable"])
        self.assertEqual(error["attempt"], 1)
        self.assertEqual(pin["attempt"], 1)

    def test_N07_real_transient_share_lock_gets_one_retry(self) -> None:
        artifacts = self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve()
        request = self.harness.request(context)
        original_sleep = time.sleep
        original_create = winio._kernel32.CreateFileW
        raw: Any = None
        released = False

        def create_after_exclusive_holder(
            path: str,
            access: int,
            share: int,
            security: object,
            disposition: int,
            flags: int,
            template: object,
        ) -> Any:
            nonlocal raw
            if (
                path.casefold()
                == winio._windows_path(str(artifacts.source)).casefold()
                and raw is None
            ):
                raw = original_create(
                    winio._windows_path(str(artifacts.source)),
                    winio.GENERIC_READ,
                    0,
                    None,
                    winio.OPEN_EXISTING,
                    winio.FILE_FLAG_BACKUP_SEMANTICS,
                    None,
                )
                self.assertNotIn(
                    raw,
                    (None, 0, winio.INVALID_HANDLE_VALUE),
                )
            return original_create(
                path,
                access,
                share,
                security,
                disposition,
                flags,
                template,
            )

        def release_after_first_retry_delay(seconds: float) -> None:
            nonlocal released
            original_sleep(seconds)
            if raw is not None and not released:
                self.assertTrue(winio._kernel32.CloseHandle(raw))
                released = True

        winio._kernel32.CreateFileW = create_after_exclusive_holder
        time.sleep = release_after_first_retry_delay
        try:
            envelope, exit_code = read_sources(request, trusted_context=context)
        finally:
            time.sleep = original_sleep
            winio._kernel32.CreateFileW = original_create
            if raw is not None and not released:
                winio._kernel32.CloseHandle(raw)
        self.assertTrue(released, (raw, envelope))
        self.assertEqual(exit_code, 0, envelope)
        self.assertEqual(len(envelope["entries"]), 1)
        self.assertEqual(envelope["entries"][0]["sha"], artifacts.source_sha)

    def test_N07_same_failure_has_no_new_delta_and_parks(self) -> None:
        artifacts = self.harness.add_source("S1", raw_baseline())
        context = self.harness.resolve(
            source_overrides={"S1": {"usage_evidence_sha": "0" * 64}}
        )
        request = self.harness.request(context)
        first, first_exit = read_sources(request, trusted_context=context)
        second, second_exit = read_sources(request, trusted_context=context)
        self.assertEqual(first_exit, second_exit)
        self.assertEqual(first, second)
        self.assertEqual(
            first["errors"][0]["first_fail"],
            "RIGHTS_UNVERIFIED",
        )
        self.assertEqual(artifacts.source.read_bytes(), raw_baseline())


if __name__ == "__main__":
    unittest.main()
