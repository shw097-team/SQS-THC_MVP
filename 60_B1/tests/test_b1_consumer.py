"""B1 consumer tests: real acceptance plus single-mutation rejects.

Fixtures are built from the real B0 envelope produced by the product
(40_OPS/ops_r4_h_pos.raw/stdout.txt) plus a synthetic owner receipt/window pair
created in a temp directory; no real credential material is copied.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "60_B1"))

from b1_consumer.receiver import Reject, receive  # noqa: E402

REAL_ENVELOPE = W / "40_OPS" / "ops_r4_h_pos.raw" / "stdout.txt"


class B1ConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        now = datetime.now(timezone.utc).astimezone()
        receipt = {
            "window_id": "WIN-test-0001",
            "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
            "scope": ["b0_source_read_authority", "sqs_thc_ph01_e00"],
            "expires_at": int((now + timedelta(hours=2)).timestamp()),
        }
        self.receipt = self.root / "receipt.json"
        self.receipt.write_text(json.dumps(receipt), encoding="utf-8")
        self.window = self.root / "window.json"
        self.window.write_text(json.dumps({**receipt, "state": "OPEN"}), encoding="utf-8")
        self.context = {
            "context_version": "B1ReceiveContext/1",
            "consumer_id": "B1",
            "verifier_version": "b1-consumer/test",
            "candidate_digest": json.loads(REAL_ENVELOPE.read_text(encoding="utf-8"))["candidate_digest"],
            "scope_id": "SQS-THC-PH01-E00-B0-SOURCE-READ",
            "source_ids": ["SST.ALL.W0.BLUEPRINT", "SST.W0M.MAIN"],
            "rights_receipt_ref": str(self.receipt),
            "rights_receipt_sha": hashlib.sha256(self.receipt.read_bytes()).hexdigest(),
            "rights_state_ref": str(self.window),
            "rights_task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
            "rights_scope": ["b0_source_read_authority", "sqs_thc_ph01_e00"],
        }

    # helpers ---------------------------------------------------------------
    def envelope(self) -> dict:
        return json.loads(REAL_ENVELOPE.read_text(encoding="utf-8"))

    def accept(self, doc: dict) -> dict:
        return receive(json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode(), self.context)

    def expect(self, doc: dict, code: str) -> None:
        with self.assertRaises(Reject) as ctx:
            self.accept(doc)
        self.assertEqual(ctx.exception.first_fail, code, ctx.exception.detail)

    # positive -------------------------------------------------------------
    def test_real_envelope_is_accepted(self) -> None:
        receipt = receive(REAL_ENVELOPE.read_bytes(), self.context)
        self.assertEqual(receipt["verdict"], "ACCEPTED")
        self.assertEqual(len(receipt["accepted"]), 2)
        self.assertEqual(receipt["rejected"], [])
        self.assertEqual(receipt["wire_version"], "SST.B0.SourceReadSet/2")

    # wire-level rejects ---------------------------------------------------
    def test_wrong_wire_version(self) -> None:
        doc = self.envelope(); doc["wire_version"] = "SST.B0.SourceReadSet/1"
        self.expect(doc, "WIRE_VERSION_UNSUPPORTED")

    def test_bom_is_rejected(self) -> None:
        payload = b"\xef\xbb\xbf" + REAL_ENVELOPE.read_bytes()
        with self.assertRaises(Reject) as ctx:
            receive(payload, self.context)
        self.assertEqual(ctx.exception.first_fail, "WIRE_INVALID")

    def test_duplicate_source_id(self) -> None:
        doc = self.envelope(); doc["entries"].append(dict(doc["entries"][0]))
        self.expect(doc, "WIRE_INVALID")

    def test_wrong_candidate_digest(self) -> None:
        doc = self.envelope(); doc["candidate_digest"] = "0" * 64
        self.expect(doc, "TUPLE_MISMATCH")

    def test_tampered_entry_sha_breaks_observed_provenance(self) -> None:
        doc = self.envelope(); doc["entries"][0]["sha"] = "1" * 64
        self.expect(doc, "TUPLE_MISMATCH")

    def test_missing_field_removed_breaks_partition(self) -> None:
        doc = self.envelope(); doc["entries"][0]["observed"] = {}
        self.expect(doc, "TUPLE_MISMATCH")

    def test_bad_epoch_strategy(self) -> None:
        doc = self.envelope(); doc["entries"][0]["authority"]["epoch_strategy"] = "GUESS"
        self.expect(doc, "WIRE_INVALID")

    def test_consumer_not_declared_in_scope(self) -> None:
        context = dict(self.context); context["consumer_id"] = "B9"
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), context)
        self.assertEqual(ctx.exception.first_fail, "SCOPE_MISMATCH")

    def test_unknown_source_id(self) -> None:
        context = dict(self.context); context["source_ids"] = ["SST.ALL.W0.BLUEPRINT"]
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), context)
        self.assertEqual(ctx.exception.first_fail, "SCOPE_MISMATCH")

    # rights-level rejects -------------------------------------------------
    def test_changed_receipt_hash_is_refused(self) -> None:
        self.receipt.write_text(json.dumps({"changed": True}), encoding="utf-8")
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), self.context)
        self.assertEqual(ctx.exception.first_fail, "RIGHTS_UNVERIFIED")

    def test_window_state_closed_is_revoked(self) -> None:
        doc = json.loads(self.window.read_text(encoding="utf-8")); doc["state"] = "CLOSED"
        self.window.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), self.context)
        self.assertEqual(ctx.exception.first_fail, "RIGHTS_REVOKED")

    def test_window_for_another_window_id_is_refused(self) -> None:
        doc = json.loads(self.window.read_text(encoding="utf-8")); doc["window_id"] = "WIN-other"
        self.window.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), self.context)
        self.assertEqual(ctx.exception.first_fail, "RIGHTS_UNVERIFIED")

    def test_window_extended_beyond_receipt_is_refused(self) -> None:
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        window = json.loads(self.window.read_text(encoding="utf-8"))
        window["expires_at"] = receipt["expires_at"] + 3600
        self.window.write_text(json.dumps(window), encoding="utf-8")
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), self.context)
        self.assertEqual(ctx.exception.first_fail, "RIGHTS_UNVERIFIED")

    def test_expired_window_is_expired(self) -> None:
        past = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        receipt["expires_at"] = past
        self.receipt.write_text(json.dumps(receipt), encoding="utf-8")
        window = json.loads(self.window.read_text(encoding="utf-8"))
        window["expires_at"] = past
        self.window.write_text(json.dumps(window), encoding="utf-8")
        context = dict(self.context)
        context["rights_receipt_sha"] = hashlib.sha256(self.receipt.read_bytes()).hexdigest()
        with self.assertRaises(Reject) as ctx:
            receive(REAL_ENVELOPE.read_bytes(), context)
        self.assertEqual(ctx.exception.first_fail, "RIGHTS_EXPIRED")


if __name__ == "__main__":
    unittest.main()
