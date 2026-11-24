"""Tests for B0.FIELDS.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from b0_reader.fields import split_fields


class B0FieldsTests(unittest.TestCase):
    def test_complete_fields_are_source_verified(self) -> None:
        result = split_fields(
            ["a", "b"],
            {"a": 1, "b": 2},
            verified_by_source={"a": True, "b": True},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["required_fields"], ["a", "b"])
        self.assertEqual(result["observed"], {"a": 1, "b": 2})
        self.assertEqual(result["missing_fields"], [])
        self.assertEqual(
            result["invariants"],
            {"subset": True, "disjoint": True, "r_unchanged": True},
        )

    def test_missing_reasons(self) -> None:
        result = split_fields(
            ["a", "b", "c"],
            {"a": 1, "b": 2, "extra": 3},
            verified_by_source={"a": True, "b": False, "c": False},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "SCHEMA_INVALID")
        self.assertEqual(
            result["missing_fields"],
            [
                {"field": "b", "reason": "NOT_VERIFIED_BY_SOURCE"},
                {"field": "c", "reason": "NOT_OBSERVED"},
            ],
        )

    def test_valid_missing_field_is_reported_without_error(self) -> None:
        result = split_fields(
            ["a", "b"],
            {"a": 1},
            verified_by_source={"a": True},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["missing_fields"],
            [{"field": "b", "reason": "NOT_OBSERVED"}],
        )

    def test_requiredness_list_is_never_deleted(self) -> None:
        required = ["a", "a", "b"]
        result = split_fields(
            required,
            {"a": 1, "b": 2},
            verified_by_source={"a": True, "b": True},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "REQUIREDNESS_HOLD")
        self.assertEqual(result["first_fail"], "AUTHOR:TOOL_REQUIREDNESS_HOLD")
        self.assertEqual(result["required_fields"], required)

    def test_scramble_or_drop_raises_REQUIREDNESS_HOLD(self) -> None:
        with patch("b0_reader.fields._invariants_hold", return_value=False):
            result = split_fields(
                ["a", "b"],
                {"a": 1, "b": 2},
                verified_by_source={"a": True, "b": True},
            )
        self.assertEqual(result["code"], "REQUIREDNESS_HOLD")
        self.assertEqual(result["first_fail"], "AUTHOR:TOOL_REQUIREDNESS_HOLD")
        self.assertEqual(result["required_fields"], ["a", "b"])

    def test_missing_is_subset_and_disjoint_from_observed(self) -> None:
        result = split_fields(
            ["a", "b"],
            {"a": 1},
            verified_by_source={"a": True},
        )
        required = set(result["required_fields"])
        missing = {item["field"] for item in result["missing_fields"]}
        self.assertTrue(missing.issubset(required))
        self.assertTrue(set(result["observed"]).isdisjoint(missing))


if __name__ == "__main__":
    unittest.main()
