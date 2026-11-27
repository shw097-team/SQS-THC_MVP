"""Author-document boundary checks used by the B0 case matrix.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

This evaluator checks the bounded author projection supplied by the work order.
It is not a CaseRegistry and does not admit any product operation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _lookup(document: Mapping[str, Any], dotted_path: str) -> Any:
    value: Any = document
    for part in dotted_path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _projected_lookup(document: Mapping[str, Any], dotted_path: str) -> Any:
    value = _lookup(document, dotted_path)
    if value is not None:
        return value
    read_set = document.get("read_set")
    if isinstance(read_set, Mapping):
        return _lookup(read_set, dotted_path)
    return None


def _read_set(document: Mapping[str, Any]) -> Mapping[str, Any]:
    value = document.get("read_set")
    return value if isinstance(value, Mapping) else {}


def _protected_values(contract: Mapping[str, Any]) -> dict[str, Any]:
    protected = contract.get("protected_fields", {})
    if isinstance(protected, Mapping):
        return dict(protected)
    if isinstance(protected, (list, tuple, set)):
        return {
            field: contract.get(field)
            for field in protected
            if isinstance(field, str) and field in contract
        }
    authority = contract.get("authority_fields")
    if isinstance(authority, Mapping):
        return dict(authority)
    return {}


def _find_split(document: Mapping[str, Any]) -> Mapping[str, Any] | None:
    direct = document.get("author_split")
    if isinstance(direct, Mapping):
        return direct
    read_set = document.get("read_set")
    items: list[Any] = []
    if isinstance(read_set, Mapping):
        candidate = read_set.get("entries", read_set.get("items", []))
        if isinstance(candidate, list):
            items = candidate
    elif isinstance(read_set, list):
        items = read_set
    for item in items:
        if not isinstance(item, Mapping):
            continue
        marker = " ".join(
            str(item.get(key, ""))
            for key in ("case_id", "author_id", "id", "locator")
        )
        if "AUTHOR-SPLIT-01" in marker or "REQ-12" in marker:
            return item
    return None


def _negative_count(split: Mapping[str, Any], document: Mapping[str, Any]) -> int:
    count = 0
    for key in ("items", "design_items", "negative_items"):
        values = split.get(key)
        if isinstance(values, list):
            count += sum(
                1
                for value in values
                if isinstance(value, Mapping) and value.get("polarity") == "NEG"
            )
    values = document.get("negative_items")
    if isinstance(values, list):
        count += sum(
            1
            for value in values
            if isinstance(value, Mapping) and value.get("polarity") == "NEG"
        )
    if split.get("polarity") == "NEG":
        count += 1
    return count


def _evaluate_equal_split(
    document: Mapping[str, Any], contract: Mapping[str, Any]
) -> tuple[bool, str]:
    expected = contract.get("author_split")
    if not isinstance(expected, Mapping):
        return True, "NONE_IF_VALID"
    actual = _find_split(document)
    if actual is None:
        return False, "AUTHOR:TRACE_ORPHAN"

    expected_fields = expected.get("required_fields", [])
    actual_fields = actual.get("required_fields", [])
    if "child_id" in expected_fields and "child_id" not in actual_fields:
        return False, "AUTHOR:TRACE_ORPHAN"
    if any(field not in actual_fields for field in expected_fields):
        return False, "AUTHOR:TOOL_REQUIREDNESS_HOLD"

    expected_negatives = int(expected.get("negative_item_count", 1))
    if _negative_count(actual, document) < expected_negatives:
        return False, "AUTHOR:NEG_MISSING"

    expected_read = expected.get("read")
    if expected_read is not None and actual.get("read") != expected_read:
        return False, "AUTHOR:CHILD_RULE_HOLD:REQ-12::AUTHOR-SPLIT-01"

    expected_observed = expected.get("observed")
    actual_observed = actual.get("observed")
    if isinstance(expected_observed, Mapping):
        for field in expected_fields:
            if field not in actual_fields:
                continue
            if not isinstance(actual_observed, Mapping) or field not in actual_observed:
                reason = (
                    "AUTHOR:TRACE_ORPHAN"
                    if field == "child_id"
                    else "AUTHOR:NEG_MISSING"
                )
                return False, reason
            verified = actual.get("verified_by_source")
            if not isinstance(verified, Mapping) or verified.get(field) is not True:
                return False, "AUTHOR:CHILD_RULE_HOLD:REQ-12::AUTHOR-SPLIT-01"
    return True, "NONE_IF_VALID"


def evaluate(
    doc: Mapping[str, Any], contract: Mapping[str, Any]
) -> tuple[bool, str]:
    """Evaluate a caller-declared author projection against its contract."""

    if not isinstance(doc, Mapping) or not isinstance(contract, Mapping):
        return False, "AUTHOR:CONTROL_SCHEMA_HOLD"

    if "required_fields" in contract:
        read_set = _read_set(doc)
        actual_required = read_set.get(
            "required_fields",
            doc.get("required_fields"),
        )
        if list(actual_required or []) != list(contract.get("required_fields") or []):
            return False, "AUTHOR:TOOL_REQUIREDNESS_HOLD"

    expected_subject = contract.get("subject")
    if expected_subject is not None and doc.get("subject") != expected_subject:
        return False, "AUTHOR:SCOPE_MISMATCH"

    expected_schema = contract.get("control_schema", contract.get("schema"))
    if expected_schema is not None:
        read_set = _read_set(doc)
        actual_schema = read_set.get(
            "schema",
            doc.get("control_schema", doc.get("schema")),
        )
        if actual_schema != expected_schema:
            return False, "AUTHOR:CONTROL_SCHEMA_HOLD"

    for field, expected_value in _protected_values(contract).items():
        if _projected_lookup(doc, field) != expected_value:
            return False, "AUTHOR:SOURCE_AUTHORITY_HOLD"

    expected_effect = contract.get("effect_intent")
    actual_effect = doc.get("effect_intent")
    if expected_effect is not None and actual_effect != expected_effect:
        return False, "AUTHOR:EFFECT_UNBOUND"

    expected_write_set = contract.get("write_set", [])
    actual_write_set = doc.get("write_set", [])
    if actual_write_set != expected_write_set:
        if expected_effect == "SOURCE_READ":
            return False, "AUTHOR:READ_WRITE_SCOPE_HOLD"
        return False, "AUTHOR:EFFECT_UNBOUND"

    ready_keys = {
        key
        for key in contract
        if str(key).startswith("ready_") or str(key).endswith("_ready")
    }
    for key in ready_keys:
        expected_ready = bool(contract.get(key))
        actual_ready = bool(doc.get(key))
        if actual_ready and not expected_ready:
            return False, "AUTHOR:FOUR_READY_HOLD"
        if actual_ready != expected_ready:
            return False, "AUTHOR:FOUR_READY_HOLD"

    if "claim_ceiling" in contract:
        if doc.get("claim_ceiling") != contract.get("claim_ceiling"):
            return False, "AUTHOR:CLAIM_CEILING_DENY"

    expected_unknown = contract.get("unknown_policy")
    if expected_unknown is not None:
        actual_unknown = doc.get("unknown_policy")
        if actual_unknown != expected_unknown and str(actual_unknown).upper() == "RETRY":
            return False, "AUTHOR:UNKNOWN_UNDO_HOLD"
        if (
            str(doc.get("state", "")).upper() == "UNKNOWN"
            and bool(doc.get("retry", False))
            and str(expected_unknown).upper() != "RETRY"
        ):
            return False, "AUTHOR:UNKNOWN_UNDO_HOLD"

    split_ok, split_failure = _evaluate_equal_split(doc, contract)
    if not split_ok:
        return False, split_failure
    return True, "NONE_IF_VALID"
