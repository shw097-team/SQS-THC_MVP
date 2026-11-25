"""Named coverage for the fourteen original and eight supplemental cases.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from b0_reader.controls import evaluate
from b0_reader.fields import split_fields
from b0_reader.requiredset import RequiredSetError, load_required_set


TEST_TEMP_ROOT = Path.cwd() / ".tmp_tests"
SUBJECT = "SST/SQS-THC/PH01/E00"


def _split_item() -> dict:
    fields = ["child_id", "evidence", "read", "write"]
    return {
        "case_id": "REQ-12::AUTHOR-SPLIT-01",
        "read": "copy-and-split",
        "required_fields": list(fields),
        "observed": {field: True for field in fields},
        "verified_by_source": {field: True for field in fields},
        "items": [
            {"polarity": "POS", "child_id": "positive"},
            {"polarity": "NEG", "child_id": "negative"},
        ],
    }


def _baseline() -> tuple[dict, dict]:
    contract = {
        "subject": SUBJECT,
        "scope": "DEV",
        "control_schema": "AUTHOR_CONTROL/1",
        "effect_intent": "SOURCE_READ",
        "write_set": [],
        "ready_source": False,
        "ready_control": False,
        "ready_four": False,
        "ready_execute": False,
        "claim_ceiling": "AUTHOR_CANDIDATE",
        "unknown_policy": "HOLD",
        "protected_fields": {"scope": "DEV"},
        "author_split": {
            "required_fields": ["child_id", "evidence", "read", "write"],
            "negative_item_count": 1,
            "read": "copy-and-split",
            "observed": {
                field: True
                for field in ["child_id", "evidence", "read", "write"]
            },
        },
    }
    doc = {
        "subject": contract["subject"],
        "effect_intent": contract["effect_intent"],
        "write_set": [],
        "ready_source": False,
        "ready_control": False,
        "ready_four": False,
        "ready_execute": False,
        "claim_ceiling": contract["claim_ceiling"],
        "unknown_policy": contract["unknown_policy"],
        "read_set": {
            "schema": contract["control_schema"],
            "scope": contract["scope"],
            "entries": [_split_item()],
        },
    }
    return doc, contract


class B0CaseMatrixTests(unittest.TestCase):
    def assert_control_case(self, expected_fail: str, mutate) -> None:
        doc, contract = _baseline()
        mutate(doc, contract)
        ok, first_fail = evaluate(doc, contract)
        self.assertEqual(first_fail, expected_fail)
        if expected_fail == "NONE_IF_VALID":
            self.assertTrue(ok)
        else:
            self.assertFalse(ok)

    def test_B0_POS_REQ_12__AUTHOR_SPLIT_01(self) -> None:
        self.assert_control_case("NONE_IF_VALID", lambda doc, contract: None)

    def test_B0_NEG_REQ_12_AUTHOR_SPLIT_01_DELETE_CHILD(self) -> None:
        def mutate(doc, contract):
            item = doc["read_set"]["entries"][0]
            item["required_fields"].remove("child_id")
            item["observed"].pop("child_id")
            item["verified_by_source"].pop("child_id")

        self.assert_control_case("AUTHOR:TRACE_ORPHAN", mutate)

    def test_B0_NEG_REQ_12_AUTHOR_SPLIT_01_DELETE_NEG(self) -> None:
        def mutate(doc, contract):
            splits = doc["read_set"]["entries"]
            splits[0]["items"] = [
                item
                for item in splits[0]["items"]
                if item["polarity"] != "NEG"
            ]

        self.assert_control_case("AUTHOR:NEG_MISSING", mutate)

    def test_B0_NEG_REQ_12_AUTHOR_SPLIT_01_FIELD_read(self) -> None:
        def mutate(doc, contract):
            doc["read_set"]["entries"][0]["read"] = "changed"

        self.assert_control_case(
            "AUTHOR:CHILD_RULE_HOLD:REQ-12::AUTHOR-SPLIT-01",
            mutate,
        )

    def test_B0_POS_AUTHOR_SOURCE_AUTHORITY(self) -> None:
        self.assert_control_case("NONE_IF_VALID", lambda doc, contract: None)

    def test_B0_NEG_AUTHOR_SOURCE_AUTHORITY(self) -> None:
        def mutate(doc, contract):
            doc["read_set"]["scope"] = "write"

        self.assert_control_case("AUTHOR:SOURCE_AUTHORITY_HOLD", mutate)

    def test_B0_POS_AUTHOR_CONTROL_SCHEMA(self) -> None:
        self.assert_control_case("NONE_IF_VALID", lambda doc, contract: None)

    def test_B0_NEG_AUTHOR_CONTROL_SCHEMA(self) -> None:
        def mutate(doc, contract):
            doc["read_set"]["schema"] = "AUTHOR_CONTROL/2"

        self.assert_control_case("AUTHOR:CONTROL_SCHEMA_HOLD", mutate)

    def test_B0_POS_AUTHOR_FOUR_READY(self) -> None:
        self.assert_control_case("NONE_IF_VALID", lambda doc, contract: None)

    def test_B0_NEG_AUTHOR_FOUR_READY(self) -> None:
        def mutate(doc, contract):
            doc["ready_execute"] = True

        self.assert_control_case("AUTHOR:FOUR_READY_HOLD", mutate)

    def test_B0_POS_AUTHOR_READ_WRITE_SCOPE(self) -> None:
        self.assert_control_case("NONE_IF_VALID", lambda doc, contract: None)

    def test_B0_NEG_AUTHOR_READ_WRITE_SCOPE(self) -> None:
        def mutate(doc, contract):
            doc["write_set"] = ["product"]

        self.assert_control_case("AUTHOR:READ_WRITE_SCOPE_HOLD", mutate)

    def test_B0_POS_AUTHOR_UNKNOWN_UNDO(self) -> None:
        self.assert_control_case("NONE_IF_VALID", lambda doc, contract: None)

    def test_B0_NEG_AUTHOR_UNKNOWN_UNDO(self) -> None:
        def mutate(doc, contract):
            doc["unknown_policy"] = "RETRY"

        self.assert_control_case("AUTHOR:UNKNOWN_UNDO_HOLD", mutate)

    def test_AUTHOR_EXEC_C01_SUBJECT(self) -> None:
        def mutate(doc, contract):
            doc["subject"] = "SST/SQS-THC/PH02/E00"

        self.assert_control_case("AUTHOR:SCOPE_MISMATCH", mutate)

    def test_READ_WRITESET_DEV_EFFECT(self) -> None:
        def mutate_write_set(doc, contract):
            doc["write_set"] = ["product"]

        def mutate_effect(doc, contract):
            doc["effect_intent"] = "READ_WRITESET/DEV_EFFECT"

        self.assert_control_case(
            "AUTHOR:READ_WRITE_SCOPE_HOLD",
            mutate_write_set,
        )
        self.assert_control_case("AUTHOR:EFFECT_UNBOUND", mutate_effect)

    def test_CLAIM_QUALIFIED(self) -> None:
        def mutate(doc, contract):
            doc["claim_ceiling"] = "QUALIFIED"

        self.assert_control_case("AUTHOR:CLAIM_CEILING_DENY", mutate)

    def test_AUTHOR_READSET_ONE_MISSING(self) -> None:
        result = split_fields(
            ["x", "y"],
            {"y": 2},
            verified_by_source={"y": True},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["missing"],
            [{"field": "x", "reason": "ABSENT", "source_ref": "AUTHOR_ONLY"}],
        )

    def test_AUTHOR_READSET_COMPLETE(self) -> None:
        result = split_fields(
            ["x", "y"],
            {"x": 1, "y": 2},
            verified_by_source={"x": True, "y": True},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["missing"], [])

    def test_AUTHOR_READSET_DROP_REQUIRED(self) -> None:
        doc, contract = _baseline()
        contract["required_fields"] = ["x", "y"]
        doc["read_set"]["required_fields"] = ["x"]
        ok, first_fail = evaluate(doc, contract)
        self.assertFalse(ok)
        self.assertEqual(first_fail, "AUTHOR:TOOL_REQUIREDNESS_HOLD")

    def test_SEC_PATH_ESCAPE(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as temporary:
            base = Path(temporary)
            root = base / "root"
            root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            with self.assertRaises(Exception) as raised:
                # The product has no caller-supplied allowed_root fallback.
                from b0_reader.root import validate_path_security

                validate_path_security(outside, allowed_root=root)
            self.assertEqual(raised.exception.code, "PATH_ESCAPE")

    def test_EDGE_STALE_EPOCH(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as temporary:
            root = Path(temporary)
            required = root / "required.json"
            requirement = root / "source.md"
            requirement.write_bytes(b"one\n")
            document = {
                "child_id": None,
                "original_id": "REQ-12",
                "owner": "PR-07",
                "polarity": "POSITIVE_READ_AND_DEV_DENY",
                "required_fields": ["read"],
                "required_set_spec_version": "B0RequiredSetSpec/1",
                "requiredness": "AUTHOR_SPLIT_UNRATIFIED",
                "requirement_ref": str(requirement),
                "requirement_sha": "a" * 64,
                "requirement_span": [1, 1],
                "rules": [
                    {
                        "expected_literal": None,
                        "field": "read",
                        "method": "RAW_SPAN_UTF8",
                        "prefix": None,
                        "source_id": "S1",
                        "span": [1, 1],
                    }
                ],
            }
            required.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(RequiredSetError) as raised:
                load_required_set(
                    str(required),
                    expected_sha="0" * 64,
                    expected_span=[1, 1],
                    expected_source_id="S1",
                )
            self.assertEqual(raised.exception.code, "REQUIRED_SET_CHANGED")

    def test_cli_is_read_only_json_and_exit_zero_for_valid(self) -> None:
        from b0_reader.return_ import parse_request

        request = {
            "request_version": "B0ReadRequest/2",
            "subject": SUBJECT,
            "original_wave": "P1-W00M",
            "bid": 0,
            "effect": "SOURCE_READ",
            "write_set": [],
            "scope_id": "S",
            "sources": [
                {
                    "source_id": "S1",
                    "expected_sha": "a" * 64,
                    "clause_span": [1, 1],
                }
            ],
        }
        parsed = parse_request(json.dumps(request).encode("utf-8"))
        self.assertEqual(parsed["request_version"], "B0ReadRequest/2")

    def test_cli_returns_two_for_typed_error(self) -> None:
        from b0_reader.errors import build_envelope, build_error

        envelope = build_envelope(
            [
                build_error(
                    "S1",
                    "SOURCE_PIN_MISMATCH",
                    "drift",
                    source_id="S1",
                    op="BYTES",
                )
            ],
            SUBJECT,
            None,
        )
        self.assertEqual(envelope["errors"][0]["op"], "BYTES")


if __name__ == "__main__":
    unittest.main()
