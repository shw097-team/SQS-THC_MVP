"""Independent v2 wire probe for N06.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

The validator in this module is transcribed from the bounded r4 contract. It
does not import the product serializer, error builder, or field splitter as an
oracle. A real B1/B2/B3 Consumer is not present; these checks establish only
contract compatibility with the declared v2 shape.
"""

from __future__ import annotations

import copy
import hashlib
import json
import ntpath
import re
import unittest
from datetime import datetime
from typing import Any, Callable

from b0_reader.return_ import read_sources

try:
    from test_product_read import IsolatedProductHarness, raw_baseline
except ImportError:  # Support both discover and tests.* invocation.
    from tests.test_product_read import IsolatedProductHarness, raw_baseline


WIRE_VERSION = "SST.B0.SourceReadSet/2"
SPEC_VERSION = "2026-11-25_r4_Native-first"
SUBJECT = "SST/SQS-THC/PH01/E00"
ORIGINAL_WAVE = "P1-W00M"
MANIFEST_SHA = (
    "2012a28f630f4e28d60309de0bb5734ce138b18c677445a475c670f1d9f4245e"
)
SHA_RE = re.compile(r"^[0-9a-f]{64}$")

TOP_KEYS = {
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
}
ENTRY_KEYS = {
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
}
SOURCE_REF_KEYS = {"source_id", "namespace", "locator", "source_version"}
PROVENANCE_KEYS = {
    "requirement_ref",
    "requirement_sha",
    "requirement_span",
    "rule_ref",
    "rule_sha",
}
AUTHORITY_KEYS = {
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
    "disclosure",
}
ERROR_KEYS = {
    "source_id",
    "op",
    "code",
    "first_fail",
    "affected_locator",
    "retryable",
    "attempt",
    "resume",
}
ERROR_OPTIONAL_KEYS = {"expected_sha", "observed_sha"}
ERROR_OPS = {"ROOT", "BYTES", "FIELDS", "RETURN"}
ERROR_CODES = {
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
}
MISSING_REASONS = {
    "ABSENT",
    "UNVERIFIED",
    "FORMAT_UNSUPPORTED",
    "AMBIGUOUS",
}


class WireRejected(ValueError):
    def __init__(self, code: str, path: str = "$") -> None:
        super().__init__(f"{code} at {path}")
        self.code = code
        self.path = path


def _reject(code: str, path: str) -> None:
    raise WireRejected(code, path)


def _object(value: Any, keys: set[str], path: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        _reject("WIRE_INVALID", path)
    return value


def _string(value: Any, path: str) -> str:
    if type(value) is not str or not value:
        _reject("WIRE_INVALID", path)
    return value


def _sha(value: Any, path: str) -> str:
    if type(value) is not str or SHA_RE.fullmatch(value) is None:
        _reject("WIRE_INVALID", path)
    return value


def _integer(value: Any, minimum: int, path: str) -> int:
    if type(value) is not int or value < minimum:
        _reject("WIRE_INVALID", path)
    return value


def _span(value: Any, path: str) -> tuple[int, int]:
    if (
        type(value) is not list
        or len(value) != 2
        or type(value[0]) is not int
        or type(value[1]) is not int
        or value[0] < 1
        or value[1] < value[0]
    ):
        _reject("WIRE_INVALID", path)
    return value[0], value[1]


def _sorted_strings(value: Any, path: str, *, nonempty: bool) -> tuple[str, ...]:
    if type(value) is not list:
        _reject("WIRE_INVALID", path)
    if nonempty and not value:
        _reject("WIRE_INVALID", path)
    if value != sorted(value) or len(value) != len(set(value)):
        _reject("WIRE_INVALID", path)
    for index, item in enumerate(value):
        text = _string(item, f"{path}[{index}]")
        if text == "*":
            _reject("WIRE_INVALID", f"{path}[{index}]")
    return tuple(value)


def _rfc3339(value: Any, path: str) -> datetime:
    text = _string(value, path)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        _reject("WIRE_INVALID", path)
    if parsed.tzinfo is None:
        _reject("WIRE_INVALID", path)
    return parsed


def _optional_string(value: Any, path: str) -> str | None:
    if value is None:
        return None
    return _string(value, path)


def parse_wire(payload: bytes) -> dict[str, Any]:
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf"):
        _reject("WIRE_INVALID", "$.bytes")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _reject("WIRE_INVALID", f"$.{key}")
            result[key] = value
        return result

    def invalid_constant(value: str) -> None:
        _reject("WIRE_INVALID", f"$.{value}")

    try:
        text = payload.decode("utf-8", errors="strict")
        document = json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=invalid_constant,
        )
    except WireRejected:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise WireRejected("WIRE_INVALID", "$.json") from exc
    if type(document) is not dict:
        _reject("WIRE_INVALID", "$")
    return document


def _validate_scope(value: Any) -> tuple[str, ...]:
    scope = _object(
        value,
        {"scope_id", "source_ids", "purpose", "consumer_ids"},
        "$.scope",
    )
    _string(scope["scope_id"], "$.scope.scope_id")
    _string(scope["purpose"], "$.scope.purpose")
    source_ids = _sorted_strings(
        scope["source_ids"],
        "$.scope.source_ids",
        nonempty=True,
    )
    _sorted_strings(
        scope["consumer_ids"],
        "$.scope.consumer_ids",
        nonempty=True,
    )
    return source_ids


def _validate_manifest(value: Any) -> None:
    manifest = _object(
        value,
        {"inherited_sha", "verification", "evidence_ref"},
        "$.source_manifest",
    )
    if _sha(manifest["inherited_sha"], "$.source_manifest.inherited_sha") != MANIFEST_SHA:
        _reject("WIRE_INVALID", "$.source_manifest.inherited_sha")
    verification = manifest["verification"]
    if verification not in {"VERIFIED", "UNVERIFIED"}:
        _reject("WIRE_INVALID", "$.source_manifest.verification")
    evidence_ref = manifest["evidence_ref"]
    if evidence_ref is not None:
        _string(evidence_ref, "$.source_manifest.evidence_ref")
    if verification == "VERIFIED" and evidence_ref is None:
        _reject("WIRE_INVALID", "$.source_manifest.evidence_ref")
    if verification == "UNVERIFIED" and evidence_ref is not None:
        _reject("WIRE_INVALID", "$.source_manifest.evidence_ref")


def _validate_source_ref(value: Any, path: str) -> str:
    source_ref = _object(value, SOURCE_REF_KEYS, path)
    for key in ("source_id", "namespace", "locator", "source_version"):
        _string(source_ref[key], f"{path}.{key}")
    locator = source_ref["locator"]
    if (
        not ntpath.isabs(locator)
        or locator.startswith(("\\\\", "//", "\\?\\", "\\\\.\\"))
        or re.match(r"^[A-Za-z]:\\", locator) is None
    ):
        _reject("WIRE_INVALID", f"{path}.locator")
    return source_ref["source_id"]


def _validate_provenance(value: Any, path: str) -> None:
    provenance = _object(value, PROVENANCE_KEYS, path)
    _string(provenance["requirement_ref"], f"{path}.requirement_ref")
    _sha(provenance["requirement_sha"], f"{path}.requirement_sha")
    _span(provenance["requirement_span"], f"{path}.requirement_span")
    _string(provenance["rule_ref"], f"{path}.rule_ref")
    _sha(provenance["rule_sha"], f"{path}.rule_sha")


def _validate_observation(
    value: Any,
    path: str,
    *,
    required_fields: set[str],
    source_sha: str,
) -> set[str]:
    if type(value) is not dict:
        _reject("WIRE_INVALID", path)
    observed_fields: set[str] = set()
    for field, observation in value.items():
        field_name = _string(field, f"{path}.<key>")
        if field_name not in required_fields or field_name in observed_fields:
            _reject("WIRE_INVALID", f"{path}.{field_name}")
        observed_fields.add(field_name)
        item = _object(
            observation,
            {"value", "source_sha", "span", "value_sha"},
            f"{path}.{field_name}",
        )
        observed_value = _string(item["value"], f"{path}.{field_name}.value")
        if _sha(item["source_sha"], f"{path}.{field_name}.source_sha") != source_sha:
            _reject("WIRE_INVALID", f"{path}.{field_name}.source_sha")
        _span(item["span"], f"{path}.{field_name}.span")
        expected_value_sha = hashlib.sha256(
            observed_value.encode("utf-8")
        ).hexdigest()
        if _sha(item["value_sha"], f"{path}.{field_name}.value_sha") != expected_value_sha:
            _reject("WIRE_INVALID", f"{path}.{field_name}.value_sha")
    return observed_fields


def _validate_missing(
    value: Any,
    path: str,
    *,
    expected_fields: set[str],
    source_id: str,
) -> None:
    if type(value) is not list:
        _reject("WIRE_INVALID", path)
    names: list[str] = []
    for index, item_value in enumerate(value):
        item = _object(
            item_value,
            {"field", "reason", "source_ref"},
            f"{path}[{index}]",
        )
        field = _string(item["field"], f"{path}[{index}].field")
        if item["reason"] not in MISSING_REASONS:
            _reject("WIRE_INVALID", f"{path}[{index}].reason")
        if item["source_ref"] != source_id:
            _reject("WIRE_INVALID", f"{path}[{index}].source_ref")
        names.append(field)
    if (
        names != sorted(names)
        or len(names) != len(set(names))
        or set(names) != expected_fields
    ):
        _reject("WIRE_INVALID", path)


def _validate_authority(
    value: Any,
    path: str,
    *,
    acl_epoch: Any,
    rights_epoch: Any,
) -> None:
    authority = _object(value, AUTHORITY_KEYS, path)
    for key in (
        "source_owner",
        "usage_evidence_ref",
        "os_principal",
        "verification_method",
        "rights_check_ref",
        "revocation_check_ref",
    ):
        _string(authority[key], f"{path}.{key}")
    _sha(authority["usage_evidence_sha"], f"{path}.usage_evidence_sha")
    checked_at = _rfc3339(authority["checked_at"], f"{path}.checked_at")
    valid_from = _rfc3339(authority["valid_from"], f"{path}.valid_from")
    expires_at = authority["expires_at"]
    if expires_at is not None:
        expires = _rfc3339(expires_at, f"{path}.expires_at")
        if valid_from > expires:
            _reject("WIRE_INVALID", f"{path}.expires_at")
        if checked_at >= expires:
            _reject("RIGHTS_EXPIRED", f"{path}.expires_at")
    strategy = authority["epoch_strategy"]
    if strategy not in {"PROVIDER_VERSIONED", "LIVE_REVALIDATE"}:
        _reject("WIRE_INVALID", f"{path}.epoch_strategy")
    provider = _optional_string(authority["epoch_provider_ref"], f"{path}.epoch_provider_ref")
    evidence = _optional_string(authority["epoch_evidence_ref"], f"{path}.epoch_evidence_ref")
    if strategy == "PROVIDER_VERSIONED":
        if provider is None or evidence is None:
            _reject("WIRE_INVALID", f"{path}.epoch_provider_ref")
        if not any(type(value) is str and value for value in (acl_epoch, rights_epoch)):
            _reject("WIRE_INVALID", "$.acl_epoch/rights_epoch")
    if authority["disclosure"] not in {"LOCAL_ONLY", "APPROVED_CONSUMER"}:
        _reject("WIRE_INVALID", f"{path}.disclosure")


def _validate_entry(value: Any, index: int) -> tuple[str, dict[str, Any]]:
    path = f"$.entries[{index}]"
    entry = _object(value, ENTRY_KEYS, path)
    source_id = _validate_source_ref(entry["source_ref"], f"{path}.source_ref")
    source_sha = _sha(entry["sha"], f"{path}.sha")
    _integer(entry["byte_length"], 0, f"{path}.byte_length")
    if entry["encoding"] != "UTF-8":
        _reject("WIRE_INVALID", f"{path}.encoding")
    _span(entry["clause_span"], f"{path}.clause_span")
    _sha(entry["clause_sha"], f"{path}.clause_sha")
    for key in ("original_id", "polarity", "requiredness", "owner"):
        _string(entry[key], f"{path}.{key}")
    child_id = entry["child_id"]
    if child_id is not None:
        _string(child_id, f"{path}.child_id")
    _validate_provenance(entry["provenance"], f"{path}.provenance")
    required = _sorted_strings(
        entry["required_fields"],
        f"{path}.required_fields",
        nonempty=True,
    )
    required_set = set(required)
    observed = _validate_observation(
        entry["observed"],
        f"{path}.observed",
        required_fields=required_set,
        source_sha=source_sha,
    )
    _validate_missing(
        entry["missing"],
        f"{path}.missing",
        expected_fields=required_set - observed,
        source_id=source_id,
    )
    for key in ("acl_epoch", "rights_epoch"):
        _optional_string(entry[key], f"{path}.{key}")
    _validate_authority(
        entry["authority"],
        f"{path}.authority",
        acl_epoch=entry["acl_epoch"],
        rights_epoch=entry["rights_epoch"],
    )
    return source_id, entry


def _validate_error(value: Any, index: int) -> str:
    path = f"$.errors[{index}]"
    if type(value) is not dict:
        _reject("WIRE_INVALID", path)
    keys = set(value)
    if not ERROR_KEYS.issubset(keys) or keys - ERROR_KEYS - ERROR_OPTIONAL_KEYS:
        _reject("WIRE_INVALID", path)
    error = value
    source_id = _string(error["source_id"], f"{path}.source_id")
    if error["op"] not in ERROR_OPS:
        _reject("WIRE_INVALID", f"{path}.op")
    if error["code"] not in ERROR_CODES:
        _reject("WIRE_INVALID", f"{path}.code")
    _string(error["first_fail"], f"{path}.first_fail")
    if error["affected_locator"] is not None:
        _string(error["affected_locator"], f"{path}.affected_locator")
    if type(error["retryable"]) is not bool:
        _reject("WIRE_INVALID", f"{path}.retryable")
    attempt = _integer(error["attempt"], 1, f"{path}.attempt")
    if attempt not in {1, 2}:
        _reject("WIRE_INVALID", f"{path}.attempt")
    if error["retryable"] != (
        error["code"] == "SOURCE_UNAVAILABLE" and attempt == 1
    ):
        _reject("WIRE_INVALID", f"{path}.retryable")
    _string(error["resume"], f"{path}.resume")
    for key in ERROR_OPTIONAL_KEYS:
        if key in error:
            _sha(error[key], f"{path}.{key}")
    return source_id


def validate_envelope(document: Any) -> dict[str, Any]:
    if type(document) is not dict:
        _reject("WIRE_INVALID", "$")
    if document.get("wire_version") != WIRE_VERSION:
        _reject("WIRE_VERSION_UNSUPPORTED", "$.wire_version")
    envelope = _object(document, TOP_KEYS, "$")
    if envelope["subject"] != SUBJECT:
        _reject("WIRE_INVALID", "$.subject")
    if envelope["original_wave"] != ORIGINAL_WAVE:
        _reject("WIRE_INVALID", "$.original_wave")
    if type(envelope["bid"]) is not int or envelope["bid"] != 0:
        _reject("WIRE_INVALID", "$.bid")
    if envelope["spec_version"] != SPEC_VERSION:
        _reject("WIRE_INVALID", "$.spec_version")
    _sha(envelope["candidate_digest"], "$.candidate_digest")
    scope_ids = _validate_scope(envelope["scope"])
    _validate_manifest(envelope["source_manifest"])
    if envelope["write_set"] != []:
        _reject("WIRE_INVALID", "$.write_set")
    if envelope["preimage"] != "N/A":
        _reject("WIRE_INVALID", "$.preimage")
    if envelope["fin_order"] != "DENY":
        _reject("WIRE_INVALID", "$.fin_order")
    if type(envelope["extensions"]) is not dict:
        _reject("WIRE_INVALID", "$.extensions")
    if type(envelope["entries"]) is not list or type(envelope["errors"]) is not list:
        _reject("WIRE_INVALID", "$.entries/errors")
    entry_ids = [
        _validate_entry(entry, index)[0]
        for index, entry in enumerate(envelope["entries"])
    ]
    error_ids = [
        _validate_error(error, index)
        for index, error in enumerate(envelope["errors"])
    ]
    all_ids = entry_ids + error_ids
    if (
        not all_ids
        or entry_ids != sorted(entry_ids)
        or error_ids != sorted(error_ids)
        or len(all_ids) != len(set(all_ids))
        or sorted(all_ids) != list(scope_ids)
    ):
        _reject("WIRE_INVALID", "$.entries/errors")
    return envelope


def validate_tuple(
    envelope: dict[str, Any],
    *,
    candidate_digest: str,
    scope_id: str,
    source_pins: dict[str, str],
    source_owners: dict[str, str],
    required_fields: dict[str, list[str]],
) -> None:
    if envelope["candidate_digest"] != candidate_digest:
        _reject("TUPLE_MISMATCH", "$.candidate_digest")
    if envelope["scope"]["scope_id"] != scope_id:
        _reject("TUPLE_MISMATCH", "$.scope.scope_id")
    if envelope["scope"]["source_ids"] != sorted(source_pins):
        _reject("TUPLE_MISMATCH", "$.scope.source_ids")
    error_ids = {error["source_id"] for error in envelope["errors"]}
    entries = {
        entry["source_ref"]["source_id"]: entry
        for entry in envelope["entries"]
    }
    for source_id, expected_sha in source_pins.items():
        if source_id in error_ids:
            continue
        entry = entries.get(source_id)
        if (
            entry is None
            or entry["sha"] != expected_sha
            or entry["authority"]["source_owner"] != source_owners[source_id]
            or entry["required_fields"] != sorted(required_fields[source_id])
        ):
            _reject("TUPLE_MISMATCH", f"$.entries[{source_id}]")


def validate_for_consumer(document: dict[str, Any], consumer: str) -> None:
    envelope = validate_envelope(document)
    required = {"source_ref", "sha", "authority"}
    if consumer == "B3":
        required.add("missing")
    if consumer not in {"B1", "B2", "B3"}:
        _reject("WIRE_INVALID", "$.consumer")
    for index, entry in enumerate(envelope["entries"]):
        if not required.issubset(entry):
            _reject("WIRE_INVALID", f"$.entries[{index}]")


class ContractProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = IsolatedProductHarness(self)
        self.artifacts = self.harness.add_source("S1", raw_baseline())
        self.context = self.harness.resolve()
        self.request = self.harness.request(self.context)
        self.envelope, self.exit_code = read_sources(
            self.request,
            trusted_context=self.context,
        )
        self.assertEqual(self.exit_code, 0)
        self.payload = json.dumps(
            self.envelope,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")

    def assert_wire_code(
        self,
        document: dict[str, Any],
        code: str,
        validator: Callable[[dict[str, Any]], Any] = validate_envelope,
    ) -> None:
        with self.assertRaises(WireRejected) as raised:
            validator(copy.deepcopy(document))
        self.assertEqual(raised.exception.code, code)

    def test_N06_product_envelope_passes_independent_validator(self) -> None:
        parsed = parse_wire(self.payload)
        validate_envelope(parsed)
        self.assertEqual(set(parsed), TOP_KEYS)
        self.assertEqual(parsed["wire_version"], WIRE_VERSION)
        self.assertEqual(parsed["entries"][0]["missing"], [])

    def test_N06_utf8_json_is_one_object_without_bom_or_chatter(self) -> None:
        self.assertFalse(self.payload.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(parse_wire(self.payload), self.envelope)
        decoder = json.JSONDecoder()
        _, end = decoder.raw_decode(self.payload.decode("utf-8"))
        self.assertEqual(end, len(self.payload.decode("utf-8")))

    def test_N06_wrong_wire_version_is_distinct(self) -> None:
        changed = copy.deepcopy(self.envelope)
        changed["wire_version"] = "SST.B0.SourceReadSet/1"
        self.assert_wire_code(changed, "WIRE_VERSION_UNSUPPORTED")

    def test_N06_missing_required_and_wrong_type_are_wire_invalid(self) -> None:
        missing = copy.deepcopy(self.envelope)
        del missing["errors"]
        self.assert_wire_code(missing, "WIRE_INVALID")
        changed = copy.deepcopy(self.envelope)
        changed["entries"][0]["byte_length"] = "78"
        self.assert_wire_code(changed, "WIRE_INVALID")

    def test_N06_duplicate_key_nan_and_infinity_are_rejected(self) -> None:
        duplicate = self.payload.replace(
            b'{"wire_version"',
            b'{"wire_version":"duplicate","wire_version"',
            1,
        )
        for payload in (
            duplicate,
            self.payload.replace(
                str(self.envelope["entries"][0]["byte_length"]).encode(),
                b"NaN",
                1,
            ),
            self.payload.replace(
                str(self.envelope["entries"][0]["byte_length"]).encode(),
                b"Infinity",
                1,
            ),
        ):
            with self.subTest(payload=payload[:80]):
                with self.assertRaises(WireRejected) as raised:
                    parse_wire(payload)
                self.assertEqual(raised.exception.code, "WIRE_INVALID")

    def test_N06_unknown_normative_fields_are_rejected(self) -> None:
        top = copy.deepcopy(self.envelope)
        top["authority"] = True
        self.assert_wire_code(top, "WIRE_INVALID")
        entry = copy.deepcopy(self.envelope)
        entry["entries"][0]["verified_by_source"] = True
        self.assert_wire_code(entry, "WIRE_INVALID")
        authority = copy.deepcopy(self.envelope)
        authority["entries"][0]["authority"]["trusted"] = True
        self.assert_wire_code(authority, "WIRE_INVALID")

    def test_N06_integer_bool_span_and_sha_types_are_closed(self) -> None:
        bool_bid = copy.deepcopy(self.envelope)
        bool_bid["bid"] = False
        self.assert_wire_code(bool_bid, "WIRE_INVALID")
        bad_span = copy.deepcopy(self.envelope)
        bad_span["entries"][0]["clause_span"] = [2, 1]
        self.assert_wire_code(bad_span, "WIRE_INVALID")
        uppercase_sha = copy.deepcopy(self.envelope)
        uppercase_sha["entries"][0]["sha"] = uppercase_sha["entries"][0]["sha"].upper()
        self.assert_wire_code(uppercase_sha, "WIRE_INVALID")

    def test_N06_source_partition_is_sorted_unique_and_total(self) -> None:
        duplicate = copy.deepcopy(self.envelope)
        duplicate["entries"].append(copy.deepcopy(duplicate["entries"][0]))
        self.assert_wire_code(duplicate, "WIRE_INVALID")
        missing = copy.deepcopy(self.envelope)
        missing["entries"] = []
        self.assert_wire_code(missing, "WIRE_INVALID")
        unknown_scope = copy.deepcopy(self.envelope)
        unknown_scope["scope"]["source_ids"] = ["S1", "S2"]
        self.assert_wire_code(unknown_scope, "WIRE_INVALID")

    def test_N06_scope_candidate_and_source_tuple_mismatch(self) -> None:
        expected = {
            "candidate_digest": self.envelope["candidate_digest"],
            "scope_id": self.context.scope_id,
            "source_pins": {"S1": self.artifacts.source_sha},
            "source_owners": {"S1": self.context.sources[0].source_owner},
            "required_fields": {"S1": ["read"]},
        }
        validate_tuple(self.envelope, **expected)
        for mutate in (
            lambda doc: doc.__setitem__("candidate_digest", "0" * 64),
            lambda doc: doc["scope"].__setitem__("scope_id", "other"),
            lambda doc: doc["entries"][0].__setitem__("sha", "0" * 64),
        ):
            changed = copy.deepcopy(self.envelope)
            mutate(changed)
            with self.assertRaises(WireRejected) as raised:
                validate_tuple(changed, **expected)
            self.assertEqual(raised.exception.code, "TUPLE_MISMATCH")

    def test_N06_raw_sha_authority_and_r_p_m_match_fixture_oracle(self) -> None:
        entry = self.envelope["entries"][0]
        source = self.artifacts.source.read_bytes()
        authority = self.context.sources[0]
        self.assertEqual(entry["sha"], hashlib.sha256(source).hexdigest())
        self.assertEqual(entry["byte_length"], len(source))
        self.assertEqual(entry["clause_sha"], hashlib.sha256(source).hexdigest())
        self.assertEqual(entry["authority"]["source_owner"], authority.source_owner)
        self.assertEqual(
            entry["authority"]["usage_evidence_sha"],
            authority.usage_evidence_sha,
        )
        self.assertEqual(entry["required_fields"], ["read"])
        self.assertEqual(set(entry["observed"]), {"read"})
        self.assertEqual(entry["missing"], [])
        self.assertEqual(
            set(entry["observed"]) | {item["field"] for item in entry["missing"]},
            set(entry["required_fields"]),
        )

    def test_N06_b1_b2_b3_each_accept_v2_and_reject_own_missing(self) -> None:
        for consumer in ("B1", "B2", "B3"):
            with self.subTest(consumer=consumer):
                validate_for_consumer(self.envelope, consumer)
                required = {"source_ref", "sha", "authority"}
                if consumer == "B3":
                    required.add("missing")
                for field in required:
                    changed = copy.deepcopy(self.envelope)
                    del changed["entries"][0][field]
                    self.assert_wire_code(changed, "WIRE_INVALID")

    def test_N06_error_tuple_is_fixed_and_retry_semantics_hold(self) -> None:
        error_envelope = copy.deepcopy(self.envelope)
        error_envelope["entries"] = []
        error_envelope["errors"] = [
            {
                "source_id": "S1",
                "op": "ROOT",
                "code": "RIGHTS_UNVERIFIED",
                "first_fail": "RIGHTS_UNVERIFIED",
                "affected_locator": None,
                "retryable": False,
                "attempt": 1,
                "resume": "取得真 Owner 權利並重新核實",
            }
        ]
        validate_envelope(error_envelope)
        retryable = copy.deepcopy(error_envelope)
        retryable["errors"][0].update(
            code="SOURCE_UNAVAILABLE",
            first_fail="SOURCE_UNAVAILABLE",
            retryable=True,
        )
        validate_envelope(retryable)
        bad_retry = copy.deepcopy(retryable)
        bad_retry["errors"][0]["attempt"] = 3
        self.assert_wire_code(bad_retry, "WIRE_INVALID")

    def test_N06_expired_authority_is_rejected_before_consumer_use(self) -> None:
        expired = copy.deepcopy(self.envelope)
        authority = expired["entries"][0]["authority"]
        authority["valid_from"] = "2026-01-01T00:00:00+08:00"
        authority["checked_at"] = "2026-01-02T00:00:00+08:00"
        authority["expires_at"] = "2026-01-01T12:00:00+08:00"
        self.assert_wire_code(expired, "RIGHTS_EXPIRED")


if __name__ == "__main__":
    unittest.main()
