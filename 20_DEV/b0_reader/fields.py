"""B0.FIELDS requiredness-preserving observed-field partitioning.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _invariants_hold(
    required_fields: list[str],
    observed: Mapping[str, Any],
    missing_fields: list[dict[str, str]],
) -> bool:
    required_set = set(required_fields)
    missing_set = {item["field"] for item in missing_fields}
    return (
        missing_set.issubset(required_set)
        and set(observed).isdisjoint(missing_set)
        and len(required_fields) >= len(set(required_fields))
    )


def _failure(
    required_fields: list[str],
    observed: dict[str, Any],
    missing_fields: list[dict[str, str]],
    invariants: dict[str, bool],
    code: str,
    first_fail: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "required_fields": required_fields,
        "observed": observed,
        "missing_fields": missing_fields,
        "invariants": invariants,
        "code": code,
        "first_fail": first_fail,
    }


def split_fields(
    required_fields: list[str],
    observed: Mapping[str, Any],
    *,
    verified_by_source: Mapping[str, bool],
) -> dict[str, Any]:
    """Split source-verified observations without deleting requirements."""

    try:
        required = list(required_fields)
    except TypeError:
        required = []
    required = [str(field) for field in required]
    observed_source = observed if isinstance(observed, Mapping) else {}
    verified = verified_by_source if isinstance(verified_by_source, Mapping) else {}
    required_set = set(required)

    partitioned = {
        field: value
        for field, value in observed_source.items()
        if field in required_set and verified.get(field) is True
    }
    missing = [
        {
            "field": field,
            "reason": (
                "NOT_OBSERVED"
                if field not in observed_source
                else "NOT_VERIFIED_BY_SOURCE"
            ),
        }
        for field in required
        if field not in partitioned
    ]
    invariants = {
        "subset": {item["field"] for item in missing}.issubset(required_set),
        "disjoint": set(partitioned).isdisjoint(
            {item["field"] for item in missing}
        ),
        "r_unchanged": len(required) == len(required_fields),
    }

    extra_fields = [field for field in observed_source if field not in required_set]
    duplicate_fields = len(required) != len(required_set)
    if extra_fields or duplicate_fields or not _invariants_hold(
        required, partitioned, missing
    ):
        invariants = {
            "subset": False if not invariants["subset"] else invariants["subset"],
            "disjoint": (
                False if not invariants["disjoint"] else invariants["disjoint"]
            ),
            "r_unchanged": (
                False if duplicate_fields else invariants["r_unchanged"]
            ),
        }
        if extra_fields and not duplicate_fields and all(invariants.values()):
            invariants = {
                "subset": True,
                "disjoint": True,
                "r_unchanged": True,
            }
        if extra_fields and invariants == {
            "subset": True,
            "disjoint": True,
            "r_unchanged": True,
        }:
            return _failure(
                required,
                partitioned,
                missing,
                invariants,
                "SCHEMA_INVALID",
                "SCHEMA_INVALID",
            )
        return _failure(
            required,
            partitioned,
            missing,
            invariants,
            "REQUIREDNESS_HOLD",
            "AUTHOR:TOOL_REQUIREDNESS_HOLD",
        )

    return {
        "ok": True,
        "required_fields": required,
        "observed": partitioned,
        "missing_fields": missing,
        "invariants": invariants,
    }
