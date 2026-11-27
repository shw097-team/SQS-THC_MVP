#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Receiver self-test: one POS baseline plus single-mutation negatives.

Every arm drives the real `receive()` callable with one mutation applied to a valid
baseline.  An arm passes only when the observed first_fail equals the expected contract
code; a negative whose baseline is invalid reports HOLD_BASELINE_NOT_VALID instead of a
count.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

WAVE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WAVE / "10_CODE"))

from b0_r3_receiver import deployment, wire                      # noqa: E402
from b0_r3_receiver.receiver import receive, load_pinned_deployment  # noqa: E402
from b0_r3_receiver.rights import canon                          # noqa: E402
from b0_r3_receiver.wire import Reject                           # noqa: E402

FX = WAVE / "20_TESTS" / "fixture"
ENVELOPE = FX / "envelope_fixture.json"
RECEIPT = FX / "receipt.json"
WINDOW = FX / "window.json"
KEYPAIR = FX / "TEST_ONLY_keypair.json"
FAR_NOW = datetime(2026, 11, 27, 22, 0, 0, tzinfo=timezone.utc)


def raw_of(path: Path) -> bytes:
    return path.read_bytes()


class ReceiverBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dep = deployment.load("fixture")
        cls.base_raw = ENVELOPE.read_bytes()
        cls.base = json.loads(cls.base_raw)
        cls.receipt0 = RECEIPT.read_bytes()
        cls.window0 = WINDOW.read_bytes()
        cls.key = json.loads(KEYPAIR.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        RECEIPT.write_bytes(cls.receipt0)
        WINDOW.write_bytes(cls.window0)

    def setUp(self) -> None:
        RECEIPT.write_bytes(self.receipt0)
        WINDOW.write_bytes(self.window0)

    # ---- helpers ----
    def run_env(self, doc: dict, consumer: str = "B1", now: datetime | None = None,
                dep: dict | None = None) -> dict:
        payload = json.dumps(doc, ensure_ascii=False).encode("utf-8")
        return receive(dep or self.dep, consumer, payload, now=now or FAR_NOW)

    def run_raw(self, payload: bytes, consumer: str = "B1",
                now: datetime | None = None) -> dict:
        return receive(self.dep, consumer, payload, now=now or FAR_NOW)

    def assert_reject(self, receipt: dict, code: str) -> None:
        self.assertEqual(receipt["verdict"], "REJECTED", receipt)
        self.assertTrue(all(r["decision"] == "REJECT" for r in receipt["rows"]))
        if receipt["global_first_fail"] is not None:
            self.assertEqual(receipt["global_first_fail"], code,
                             f'expected {code}, got {receipt["global_first_fail"]}')
        else:
            # source-scoped refusal: every expected source must carry the same contract code
            self.assertEqual([r["first_fail"] for r in receipt["rows"]], [code] * len(receipt["rows"]),
                             f'expected {code} per source, got {[r["first_fail"] for r in receipt["rows"]]}')

    def ressign_receipt(self, mutate) -> None:
        doc = json.loads(self.receipt0)
        signed = {k: doc[k] for k in
                  ("window_id", "task_id", "opened_at", "expires_at", "scope", "max_ops",
                   "effect_class_ceiling", "policy_epoch_at_open",
                   "enrollments_sha256_at_open", "owner_fingerprint")}
        mutate(signed)
        signed["owner_signature_hex"] = self._sign(canon(signed))
        signed["alg"] = "ed25519"
        signed["claim_ceiling"] = doc["claim_ceiling"]
        RECEIPT.write_bytes(json.dumps(signed, ensure_ascii=False, indent=1).encode("utf-8"))

    def _sign(self, body: bytes) -> str:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(self.key["private_hex"]))
        return priv.sign(body).hex()

    def mutate_window(self, **fields) -> None:
        doc = json.loads(self.window0)
        doc.update(fields)
        WINDOW.write_bytes(json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8"))


class POS(ReceiverBase):
    def test_pos_baseline_accepts_every_consumer(self):
        for cid in ("B1", "B2", "B3"):
            r = self.run_env(self.base, cid)
            self.assertEqual(r["verdict"], "ACCEPTED", r)
            self.assertEqual(r["sources_accepted"], 1)
            self.assertEqual(r["consumer_id"], cid)
            self.assertEqual(r["validator_name"], f"{cid.lower()}_b0_r3_receiver")

    def test_thirteen_columns_present_and_measured(self):
        r = self.run_env(self.base, "B1")
        cols = ["consumer_id", "validator_name", "validator_version", "subject", "scope_id",
                "spec_version", "candidate_digest", "source_id", "sha", "rights_check_ref",
                "decision", "first_fail", "checked_at"]
        row = r["rows"][0]
        for c in cols:
            self.assertIn(c, row)
        self.assertEqual(sorted(row), sorted(cols + ["evidence"]))
        self.assertEqual(row["sha"], wire.sha256(raw_of(FX / "source_fixture.md")))
        self.assertIsNone(row["first_fail"])
        self.assertRegex(row["rights_check_ref"], r"^FIXTURE-WIN-0001:[0-9a-f]{16}:FIXTURE\.SOURCE$")
        self.assertTrue(row["evidence"]["clause_sha"])
        self.assertEqual(row["evidence"]["R"], ["read"])
        self.assertEqual(row["evidence"]["P"], ["read"])
        self.assertEqual(row["evidence"]["M"], [])

    def test_byte_level_equivalence_is_not_dict_equivalence(self):
        pretty = json.dumps(self.base, ensure_ascii=False, indent=2).encode("utf-8")
        compact = json.dumps(self.base, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        a, b = self.run_raw(pretty), self.run_raw(compact)
        self.assertEqual(a["verdict"], "ACCEPTED")
        self.assertEqual(b["verdict"], "ACCEPTED")
        self.assertNotEqual(a["envelope_sha256"], b["envelope_sha256"])
        self.assertEqual(a["rows"][0]["evidence"]["P"], b["rows"][0]["evidence"]["P"])

    def test_equivalent_offset_timestamp_still_accepts(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["expires_at"] = "2099-01-01T08:00:00+08:00"  # same instant
        self.assertEqual(self.run_env(doc)["verdict"], "ACCEPTED")

    def test_cli_accepts_and_refuses_caller_trust_root(self):
        env = dict(os.environ, PYTHONPATH=str(WAVE / "10_CODE"))
        r = subprocess.run([sys.executable, "-B", "-m", "b0_r3_receiver.cli", "receive",
                            "--consumer", "B1", "--envelope", str(ENVELOPE),
                            "--deployment", "fixture"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('"verdict": "ACCEPTED"', r.stdout)
        for flag in ("--context", "--root", "--epoch"):
            bad = subprocess.run([sys.executable, "-B", "-m", "b0_r3_receiver.cli", "receive",
                                  "--consumer", "B1", "--envelope", str(ENVELOPE),
                                  "--deployment", "fixture", flag, "X"],
                                 capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(bad.returncode, 64, bad.stdout)
            self.assertIn("CALLER_SUPPLIED_TRUST_ROOT", bad.stdout)


class WireNegatives(ReceiverBase):
    def test_bom(self):
        self.assert_reject(self.run_raw(b"\xef\xbb\xbf" + self.base_raw), "WIRE_INVALID")

    def test_not_utf8(self):
        self.assert_reject(self.run_raw(self.base_raw[:-2] + b"\xff\xfe"), "WIRE_INVALID")

    def test_duplicate_key(self):
        text = self.base_raw.decode("utf-8").replace(
            '"bid": 0,', '"bid": 0, "bid": 0,', 1)
        self.assert_reject(self.run_raw(text.encode("utf-8")), "WIRE_INVALID")

    def test_nan(self):
        text = self.base_raw.decode("utf-8").replace('"bid": 0,', '"bid": NaN,', 1)
        self.assert_reject(self.run_raw(text.encode("utf-8")), "WIRE_INVALID")

    def test_two_objects(self):
        self.assert_reject(self.run_raw(self.base_raw + b'{"a":1}'), "WIRE_INVALID")

    def test_empty(self):
        self.assert_reject(self.run_raw(b""), "WIRE_INVALID")

    def test_top_level_array(self):
        self.assert_reject(self.run_raw(b'[1,2,3]'), "WIRE_INVALID")

    def test_unknown_top_key(self):
        doc = copy.deepcopy(self.base)
        doc["extra"] = 1
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_wire_version(self):
        doc = copy.deepcopy(self.base)
        doc["wire_version"] = "SST.B0.SourceReadSet/3"
        self.assert_reject(self.run_env(doc), "WIRE_VERSION_UNSUPPORTED")

    def test_bid_bool(self):
        doc = copy.deepcopy(self.base)
        doc["bid"] = False
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_spec_version(self):
        doc = copy.deepcopy(self.base)
        doc["spec_version"] = "2026-11-27_r7"
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_subject(self):
        doc = copy.deepcopy(self.base)
        doc["subject"] = "SST/SQS-THC/PH01/E01"
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")


class TupleAndPinNegatives(ReceiverBase):
    def test_candidate_digest_not_the_pin(self):
        doc = copy.deepcopy(self.base)
        doc["candidate_digest"] = "f" * 64
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_candidate_digest_not_a_sha(self):
        doc = copy.deepcopy(self.base)
        doc["candidate_digest"] = "not-a-digest"
        self.assert_reject(self.run_env(doc), "PRODUCER_FREEZE_UNBOUND")

    def test_effect_claim(self):
        doc = copy.deepcopy(self.base)
        doc["fin_order"] = "ALLOW"
        self.assert_reject(self.run_env(doc), "EFFECT_DENIED")

    def test_write_set(self):
        doc = copy.deepcopy(self.base)
        doc["write_set"] = ["x"]
        self.assert_reject(self.run_env(doc), "EFFECT_DENIED")

    def test_scope_id(self):
        doc = copy.deepcopy(self.base)
        doc["scope"]["scope_id"] = "OTHER"
        self.assert_reject(self.run_env(doc), "SCOPE_MISMATCH")

    def test_purpose(self):
        doc = copy.deepcopy(self.base)
        doc["scope"]["purpose"] = "some other use"
        self.assert_reject(self.run_env(doc), "SCOPE_MISMATCH")

    def test_consumer_membership(self):
        doc = copy.deepcopy(self.base)
        doc["scope"]["consumer_ids"] = ["B4"]
        self.assert_reject(self.run_env(doc), "SCOPE_MISMATCH")

    def test_source_set(self):
        doc = copy.deepcopy(self.base)
        doc["scope"]["source_ids"] = ["FIXTURE.OTHER"]
        self.assert_reject(self.run_env(doc), "SCOPE_MISMATCH")

    def test_raw_sha(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["sha"] = "0" * 64
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_span(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["clause_span"] = [3, 6]
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_namespace(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["source_ref"]["namespace"] = "FIXTURE/OTHER"
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_source_version(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["source_ref"]["source_version"] = "fixture_r2"
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_envelope_locator_cannot_choose_the_file(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["source_ref"]["locator"] = str(FX / "does_not_exist.md")
        r = self.run_env(doc)
        # refused on the tuple, before any open() of the caller-declared path
        self.assert_reject(r, "TUPLE_MISMATCH")
        self.assertNotIn("SOURCE_UNAVAILABLE", json.dumps(r))

    def test_provenance_requirement_sha(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["provenance"]["requirement_sha"] = "a" * 64
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_manifest_unverified_with_evidence(self):
        doc = copy.deepcopy(self.base)
        doc["source_manifest"]["evidence_ref"] = "somewhere"
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")


class RequiredSetNegatives(ReceiverBase):
    def test_required_set_changed(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["required_fields"] = ["read", "write"]
        self.assert_reject(self.run_env(doc), "REQUIRED_SET_CHANGED")

    def test_required_set_emptied(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["required_fields"] = []
        self.assert_reject(self.run_env(doc), "REQUIRED_SET_CHANGED")

    def test_observed_field_not_in_r(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"]["write"] = copy.deepcopy(
            doc["entries"][0]["observed"]["read"])
        self.assert_reject(self.run_env(doc), "FIELD_NOT_REQUIRED")

    def test_value_tampered(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"]["read"]["value"] = "tampered"
        self.assert_reject(self.run_env(doc), "CLAUSE_RULE_MISMATCH")

    def test_value_sha_mismatch(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"]["read"]["value_sha"] = "b" * 64
        self.assert_reject(self.run_env(doc), "CLAUSE_RULE_MISMATCH")

    def test_observed_span(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"]["read"]["span"] = [4, 4]
        self.assert_reject(self.run_env(doc), "CLAUSE_RULE_MISMATCH")

    def test_observed_source_sha(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"]["read"]["source_sha"] = "c" * 64
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_missing_null(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["missing"] = None
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_missing_reason_enum(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["missing"] = [{"field": "read", "reason": "WHATEVER",
                                         "source_ref": "FIXTURE.SOURCE"}]
        doc["entries"][0]["observed"] = {}
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_missing_is_not_partition(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"] = {}
        doc["entries"][0]["missing"] = []
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_legal_missing_is_draft_not_accept(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["observed"] = {}
        doc["entries"][0]["missing"] = [{"field": "read", "reason": "ABSENT",
                                         "source_ref": "FIXTURE.SOURCE"}]
        r = self.run_env(doc)
        self.assertEqual(r["verdict"], "PARTIAL_DRAFT", r)
        self.assertEqual(r["rows"][0]["first_fail"], "MANDATORY_FIELD_MISSING")
        self.assertEqual(r["rows"][0]["decision"], "DRAFT_MISSING")


class StructureNegatives(ReceiverBase):
    def test_duplicate_entry(self):
        doc = copy.deepcopy(self.base)
        doc["entries"].append(copy.deepcopy(doc["entries"][0]))
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_entry_and_error_for_same_source(self):
        doc = copy.deepcopy(self.base)
        doc["errors"] = [{"source_id": "FIXTURE.SOURCE", "op": "BYTES", "code": "X",
                          "first_fail": "SOURCE_CHANGED_SINCE_READ", "retryable": False,
                          "attempt": 1, "resume": "owner"}]
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_missing_source_entirely(self):
        doc = copy.deepcopy(self.base)
        doc["entries"] = []
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_unrequested_source_entry(self):
        doc = copy.deepcopy(self.base)
        doc["scope"]["source_ids"] = ["FIXTURE.SOURCE"]
        extra = copy.deepcopy(doc["entries"][0])
        extra["source_ref"]["source_id"] = "FIXTURE.STRAY"
        doc["entries"].append(extra)
        self.assert_reject(self.run_env(doc), "SCOPE_MISMATCH")

    def test_error_retryable_type(self):
        doc = copy.deepcopy(self.base)
        doc["entries"] = []
        doc["errors"] = [{"source_id": "FIXTURE.SOURCE", "op": "BYTES", "code": "X",
                          "first_fail": "SOURCE_CHANGED_SINCE_READ", "retryable": 0,
                          "attempt": 1, "resume": "owner"}]
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")


class AuthorityNegatives(ReceiverBase):
    def test_authority_shape(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"].pop("disclosure")
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_authority_null_field(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["verification_method"] = None
        self.assert_reject(self.run_env(doc), "RIGHTS_UNVERIFIED")

    def test_authority_principal(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["os_principal"] = "desktop-57eo414\\someoneelse"
        self.assert_reject(self.run_env(doc), "RIGHTS_DENIED")

    def test_authority_disclosure_enum(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["disclosure"] = "PUBLIC"
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_epoch_strategy_enum(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["epoch_strategy"] = "STATIC"
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_envelope_expired(self):
        doc = copy.deepcopy(self.base)
        self.assert_reject(self.run_env(doc, now=datetime(2099, 6, 1, tzinfo=timezone.utc)),
                           "ENVELOPE_AUTHORITY_EXPIRED")

    def test_envelope_not_yet_valid(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["valid_from"] = "2098-01-01T00:00:00+00:00"
        self.assert_reject(self.run_env(doc), "RIGHTS_NOT_YET_VALID")

    def test_naive_timestamp(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["expires_at"] = "2099-01-01T00:00:00"
        self.assert_reject(self.run_env(doc), "RIGHTS_UNVERIFIED")

    def test_truncated_timestamp(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["expires_at"] = "2099-13-01T00:00:00+00:00"
        self.assert_reject(self.run_env(doc), "RIGHTS_UNVERIFIED")

    def test_usage_evidence_not_the_live_receipt(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["usage_evidence_sha"] = "d" * 64
        self.assert_reject(self.run_env(doc), "ENVELOPE_MINTED_UNDER_A_DIFFERENT_WINDOW")


class RightsNegatives(ReceiverBase):
    def test_window_closed(self):
        self.mutate_window(state="CLOSED")
        self.assert_reject(self.run_env(self.base), "RIGHTS_REVOKED")

    def test_window_revoked(self):
        self.mutate_window(state="REVOKED")
        self.assert_reject(self.run_env(self.base), "RIGHTS_REVOKED")

    def test_window_is_not_the_pinned_window(self):
        self.mutate_window(window_id="FIXTURE-WIN-0002")
        self.assert_reject(self.run_env(self.base), "RIGHTS_UNVERIFIED")

    def test_window_expiry_beyond_receipt(self):
        self.mutate_window(expires_at=4102444800 + 10)
        self.assert_reject(self.run_env(self.base), "RIGHTS_UNVERIFIED")

    def test_window_expired(self):
        self.mutate_window(expires_at=1700000000)
        RECEIPT.write_bytes(self.receipt0)  # receipt expiry still far; the live window is the gate
        self.assert_reject(self.run_env(self.base), "RIGHTS_EXPIRED")

    def test_receipt_tampered(self):
        doc = json.loads(self.receipt0)
        doc["max_ops"] = 99
        RECEIPT.write_bytes(json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8"))
        self.assert_reject(self.run_env(self.base), "RIGHTS_UNVERIFIED")

    def test_receipt_signature_flipped(self):
        doc = json.loads(self.receipt0)
        sig = doc["owner_signature_hex"]
        doc["owner_signature_hex"] = ("0" if sig[0] != "0" else "1") + sig[1:]
        RECEIPT.write_bytes(json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8"))
        self.assert_reject(self.run_env(self.base), "RIGHTS_UNVERIFIED")

    def test_receipt_scope_order_is_the_contract(self):
        self.ressign_receipt(lambda r: r.__setitem__("scope", list(reversed(r["scope"]))))
        self.assert_reject(self.run_env(self.base), "RIGHTS_UNVERIFIED")

    def test_receipt_task_id(self):
        self.ressign_receipt(lambda r: r.__setitem__("task_id", "SOME_OTHER_TASK"))
        self.assert_reject(self.run_env(self.base), "RIGHTS_UNVERIFIED")

    def test_principal_override(self):
        dep = copy.deepcopy(self.dep)
        dep["os_principal"] = "desktop-57eo414\\someoneelse"
        RECEIPT.write_bytes(self.receipt0)
        r = receive(dep, "B1", self.base_raw, now=FAR_NOW)
        self.assert_reject(r, "RIGHTS_DENIED")

    def test_effect_ceiling_insufficient(self):
        dep = copy.deepcopy(self.dep)
        dep["rights"] = dict(dep["rights"], required_effect_ceiling="HOST_OPERATIONS")
        r = receive(dep, "B1", self.base_raw, now=FAR_NOW)
        self.assert_reject(r, "RIGHTS_DENIED")

    def test_candidate_pin_override(self):
        dep = copy.deepcopy(self.dep)
        dep["producer_candidate_digest"] = "e" * 64
        r = receive(dep, "B1", self.base_raw, now=FAR_NOW)
        self.assert_reject(r, "TUPLE_MISMATCH")


class TrustRootNegatives(ReceiverBase):
    def test_descriptor_hash_is_the_pin(self):
        with self.assertRaises(Reject) as ctx:
            load_pinned_deployment("fixture", "0" * 64, str(FX / "DEPLOYMENT_fixture_20261127_r9.json"))
        self.assertEqual(ctx.exception.code, "TRUST_CONTEXT_UNBOUND")

    def test_descriptor_in_an_unsealed_directory_is_refused(self):
        stolen = WAVE / "tmp" / "unsealed"
        stolen.mkdir(parents=True, exist_ok=True)
        target = stolen / "DEPLOYMENT_copy.json"
        target.write_bytes((FX / "DEPLOYMENT_fixture_20261127_r9.json").read_bytes())
        sha = wire.sha256(target.read_bytes())
        with self.assertRaises(Reject) as ctx:
            load_pinned_deployment("fixture", sha, str(target))
        self.assertEqual(ctx.exception.code, "TRUST_CONTEXT_UNBOUND")
        self.assertIn("broad principal has write", ctx.exception.detail)

    def test_sealed_descriptor_passes_the_same_gate(self):
        dep = load_pinned_deployment("fixture",
                                     "59c5553466fa36737edaf8bf7b3bb5ac37ff9e9279f076ddf0e9858f92696e95",
                                     str(FX / "DEPLOYMENT_fixture_20261127_r9.json"))
        self.assertEqual(dep["deployment_id"], "fixture")


class HardeningNegatives(ReceiverBase):
    """Arms added after the first separated verdict (attempt 1 -> attempt 2)."""

    def test_error_attempt_bool(self):
        doc = copy.deepcopy(self.base)
        doc["entries"] = []
        doc["errors"] = [{"source_id": "FIXTURE.SOURCE", "op": "BYTES", "code": "X",
                          "first_fail": "SOURCE_CHANGED_SINCE_READ", "retryable": False,
                          "attempt": True, "resume": "owner"}]
        self.assert_reject(self.run_env(doc), "WIRE_INVALID")

    def test_inherited_manifest_is_pinned(self):
        doc = copy.deepcopy(self.base)
        doc["source_manifest"]["inherited_sha"] = "0" * 64
        self.assert_reject(self.run_env(doc), "TUPLE_MISMATCH")

    def test_verified_manifest_needs_resolvable_evidence(self):
        doc = copy.deepcopy(self.base)
        doc["source_manifest"]["verification"] = "VERIFIED"
        doc["source_manifest"]["evidence_ref"] = "C:/no/such/manifest.json"
        # the deployment holds this manifest as UNVERIFIED, so the claim cannot be upgraded
        self.assert_reject(self.run_env(doc), "MANIFEST_VERIFICATION_ESCALATED")

    def test_verified_manifest_without_evidence_ref(self):
        doc = copy.deepcopy(self.base)
        doc["source_manifest"]["verification"] = "VERIFIED"
        doc["source_manifest"]["evidence_ref"] = None
        self.assert_reject(self.run_env(doc), "MANIFEST_VERIFICATION_ESCALATED")

    def test_provider_epoch_cannot_be_nulled(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["epoch_strategy"] = "PROVIDER_VERSIONED"
        self.assert_reject(self.run_env(doc), "EPOCH_UNBOUND")

    def test_rights_decided_before_any_source_byte(self):
        """An expired authority must be refused before the pinned locator is ever opened."""
        dep = copy.deepcopy(self.dep)
        absent = str(FX / "absent.md")
        dep["consumers"]["B1"]["sources"]["FIXTURE.SOURCE"]["locator"] = absent
        doc = copy.deepcopy(self.base)
        for e in doc["entries"]:
            e["source_ref"]["locator"] = absent      # tuple still consistent
            e["authority"]["valid_from"] = "2025-01-01T00:00:00+00:00"
            e["authority"]["expires_at"] = "2026-01-01T00:00:00+00:00"
        r = receive(dep, "B1", json.dumps(doc, ensure_ascii=False).encode("utf-8"), now=FAR_NOW)
        self.assert_reject(r, "ENVELOPE_AUTHORITY_EXPIRED")
        self.assertNotIn("SOURCE_UNAVAILABLE", json.dumps(r))


    def test_verified_manifest_bound_to_the_deployment_digest(self):
        """With a deployment-held digest, VERIFIED still needs those exact bytes."""
        dep = copy.deepcopy(self.dep)
        dep["source_manifest_expected"] = dict(dep["source_manifest_expected"],
                                               verification="VERIFIED",
                                               evidence_sha256="a" * 64)
        doc = copy.deepcopy(self.base)
        doc["source_manifest"] = {"inherited_sha": dep["source_manifest_expected"]["inherited_sha"],
                                  "verification": "VERIFIED",
                                  "evidence_ref": str(FX / "source_fixture.md")}
        r = receive(dep, "B1", json.dumps(doc, ensure_ascii=False).encode("utf-8"), now=FAR_NOW)
        self.assert_reject(r, "MANIFEST_EVIDENCE_UNRESOLVED")

    def test_epoch_string_without_provider_is_not_an_epoch(self):
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["epoch_strategy"] = "PROVIDER_VERSIONED"
        doc["entries"][0]["acl_epoch"] = "acl:v1"
        doc["entries"][0]["rights_epoch"] = "rights:v1"
        self.assert_reject(self.run_env(doc), "EPOCH_UNBOUND")

    def test_epoch_bound_provider_with_stale_epoch(self):
        dep = copy.deepcopy(self.dep)
        dep["epoch_provider"] = {"provider_ref": "prov:A", "expected_rights_epoch": "rights:v9"}
        doc = copy.deepcopy(self.base)
        doc["entries"][0]["authority"]["epoch_strategy"] = "PROVIDER_VERSIONED"
        doc["entries"][0]["authority"]["epoch_provider_ref"] = "prov:A"
        doc["entries"][0]["acl_epoch"] = "acl:v1"
        doc["entries"][0]["rights_epoch"] = "rights:v1"
        r = receive(dep, "B1", json.dumps(doc, ensure_ascii=False).encode("utf-8"), now=FAR_NOW)
        self.assert_reject(r, "EPOCH_STALE")

    def test_pinned_locator_outside_allowed_roots(self):
        dep = copy.deepcopy(self.dep)
        dep["allowed_roots"] = [str(WAVE / "tmp")]
        r = receive(dep, "B1", self.base_raw, now=FAR_NOW)
        self.assert_reject(r, "TUPLE_MISMATCH")


if __name__ == "__main__":
    unittest.main(verbosity=2)
