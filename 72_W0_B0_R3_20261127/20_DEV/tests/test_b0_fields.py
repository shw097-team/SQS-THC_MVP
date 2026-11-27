"""Tests for B0.FIELDS v2 RequiredSet extraction.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

import hashlib
import unittest

from b0_reader.fields import extract_fields, split_fields, value_sha
from b0_reader.requiredset import RequiredSetSpec, RuleSpec


def _required_set(
    fields: tuple[str, ...],
    rules: tuple[RuleSpec, ...],
    *,
    requirement_span: tuple[int, int] = (1, 2),
) -> RequiredSetSpec:
    return RequiredSetSpec(
        requirement_ref=r"C:\isolated\requirement.md",
        requirement_sha="a" * 64,
        requirement_span=requirement_span,
        original_id="REQ-12",
        child_id="REQ-12::AUTHOR-SPLIT-01",
        polarity="POSITIVE_READ_AND_DEV_DENY",
        requiredness="AUTHOR_SPLIT_UNRATIFIED",
        owner="PR-07",
        required_fields=fields,
        rules=rules,
        rule_ref=r"C:\isolated\required-set.json",
        rule_sha="b" * 64,
        raw_bytes=100,
    )


class B0FieldsTests(unittest.TestCase):
    def test_complete_fields_are_source_verified(self) -> None:
        payload = b"alpha\nbeta\n"
        span = (1, 1)
        self.assertEqual(span, (1, 1))
        rule = RuleSpec("alpha", "RAW_SPAN_UTF8", "S", span, None, None)
        result = extract_fields(
            _required_set(
                ("alpha",),
                (rule,),
                requirement_span=(1, 2),
            ),
            payload,
            source_id="S",
            source_sha=hashlib.sha256(payload).hexdigest(),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["required_fields"], ["alpha"])
        self.assertIn("alpha", result["observed"])
        self.assertEqual(
            result["observed"]["alpha"],
            {
                "value": "alpha\n",
                "source_sha": hashlib.sha256(payload).hexdigest(),
                "span": [1, 1],
                "value_sha": value_sha("alpha\n"),
            },
        )
        self.assertEqual(result["missing"], [])

    def test_missing_reasons_are_closed_and_do_not_drop_requiredness(self) -> None:
        payload = b"no label\n- absent: present\n"
        rules = (
            RuleSpec("absent", "MD_LABEL", "S", (1, 1), "- label: ", None),
            RuleSpec("ambiguous", "MD_LABEL", "S", (1, 1), "", None),
            RuleSpec(
                "unverified",
                "MD_LABEL",
                "S",
                (1, 1),
                "- absent: ",
                "not-the-value",
            ),
        )
        result = extract_fields(
            _required_set(
                ("absent", "ambiguous", "unverified"),
                rules,
                requirement_span=(1, 1),
            ),
            payload,
            source_id="S",
            source_sha=hashlib.sha256(payload).hexdigest(),
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["ok"])
        self.assertEqual(
            {item["field"]: item["reason"] for item in result["missing"]},
            {
                "absent": "ABSENT",
                "ambiguous": "AMBIGUOUS",
                "unverified": "ABSENT",
            },
        )
        self.assertEqual(
            result["required_fields"],
            ["absent", "ambiguous", "unverified"],
        )

    def test_valid_missing_field_is_reported_without_fatal_error(self) -> None:
        payload = b"first\nsecond\n"
        rule = RuleSpec("label", "MD_LABEL", "S", (2, 2), "- label: ", None)
        result = extract_fields(
            _required_set(("label",), (rule,)),
            b"first\nsecond\n",
            source_id="S",
            source_sha=hashlib.sha256(payload).hexdigest(),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["missing"],
            [{"field": "label", "reason": "ABSENT", "source_ref": "S"}],
        )
        self.assertEqual(result["observed"], {})

    def test_requiredness_list_is_never_deleted(self) -> None:
        required = ("alpha", "beta")
        rules = (
            RuleSpec("alpha", "RAW_SPAN_UTF8", "S", (1, 1), None, None),
            RuleSpec("beta", "RAW_SPAN_UTF8", "S", (2, 2), None, None),
        )
        result = extract_fields(
            _required_set(required, rules),
            b"alpha\nbeta\n",
            source_id="S",
            source_sha=hashlib.sha256(b"alpha\nbeta\n").hexdigest(),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["required_fields"], list(required))
        self.assertEqual(set(result["required_fields"]), {"alpha", "beta"})

    def test_scramble_or_drop_never_uses_caller_observed_values(self) -> None:
        rule = RuleSpec("alpha", "RAW_SPAN_UTF8", "S", (1, 1), None, None)
        result = extract_fields(
            _required_set(
                ("alpha",),
                (rule,),
                requirement_span=(1, 1),
            ),
            b"from-source\n",
            source_id="S",
            source_sha=hashlib.sha256(b"from-source\n").hexdigest(),
        )
        self.assertEqual(
            result["observed"]["alpha"]["value"],
            "from-source\n",
        )
        self.assertNotIn(
            "caller-value",
            [item["value"] for item in result["observed"].values()],
        )

    def test_missing_is_subset_and_disjoint_from_observed(self) -> None:
        rules = (
            RuleSpec("a", "RAW_SPAN_UTF8", "S", (1, 1), None, None),
            RuleSpec("b", "MD_LABEL", "S", (1, 1), "- missing: ", None),
        )
        result = extract_fields(
            _required_set(
                ("a", "b"),
                rules,
                requirement_span=(1, 1),
            ),
            b"a\n",
            source_id="S",
            source_sha=hashlib.sha256(b"a\n").hexdigest(),
        )
        self.assertTrue(result["ok"])
        required = set(result["required_fields"])
        missing = {item["field"] for item in result["missing"]}
        self.assertTrue(missing.issubset(required))
        self.assertTrue(set(result["observed"]).isdisjoint(missing))
        self.assertEqual(set(result["observed"]) | missing, required)

    def test_author_compatibility_keeps_required_fields(self) -> None:
        result = split_fields(
            ["a", "b"],
            {"a": 1},
            verified_by_source={"a": True},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["required_fields"], ["a", "b"])
        self.assertEqual(
            result["missing"],
            [{"field": "b", "reason": "ABSENT", "source_ref": "AUTHOR_ONLY"}],
        )


if __name__ == "__main__":
    unittest.main()
