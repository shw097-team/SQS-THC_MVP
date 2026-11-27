"""Shared isolated trust fixtures for the production resolver.

AUTHOR_CANDIDATE_NOT_PRODUCT_ADMITTED

The fixture redirects only the fixed descriptor location and pin. All trust
contexts are sealed by the real production resolver. The test-only deployment
root receives a sealed Windows DACL, and the ordinary filesystem checks,
reparse checks, handle identity, and revalidation behavior remain real.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import b0_reader.native_entry as native_entry
from b0_reader.native_entry import TrustedContext
from b0_reader.return_ import ORIGINAL_WAVE, REQUEST_VERSION, SUBJECT
from b0_reader.winio import current_principal


DEV_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = DEV_ROOT / ".tmp_tests"
LABEL = "- **How／Predicate**："


@dataclass(frozen=True)
class SourceArtifacts:
    source_id: str
    source: Path
    required_set: Path
    payload: bytes
    source_sha: str


def raw_baseline() -> bytes:
    return (
        "\ufeff標題\r\n"
        f"{LABEL}<LOCAL_ONLY_REDACTED>\n"
        "末行（無結尾換行）"
    ).encode("utf-8")


def empty_acl_probe() -> tuple[dict[str, Any], int]:
    """Return the fixed no-output invocation result without granting content."""

    return {}, 64


class IsolatedProductHarness:
    """Invoke the production resolver against a contained test deployment."""

    def __init__(self, testcase: unittest.TestCase) -> None:
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)
        testcase.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name) / "root"
        self.root.mkdir()
        self._seal_test_root()
        self.owner = self.root / "owner-window.json"
        self.authorization = self.root / "authorization.json"
        self.authorization.write_text(
            '{"kind":"isolated-test-authorization","window_id":"WIN-test-0001",'
            '"owner_fingerprint":"test-fingerprint"}\n',
            encoding="utf-8",
        )
        self._set_owner_state("OPEN")
        self.sources: dict[str, SourceArtifacts] = {}
        self._descriptor_sources: list[dict[str, Any]] = []
        self.descriptor = self.root / "context.json"
        self._patchers = [
            patch.object(native_entry, "_TRUST_ROOT", str(self.root)),
            patch.object(
                native_entry,
                "EXPECTED_DESCRIPTOR_PATH",
                str(self.descriptor),
            ),
            patch.object(native_entry, "EXPECTED_DESCRIPTOR_SHA", ""),
            patch.object(native_entry, "EXPECTED_DESCRIPTOR_BYTES", 0),
            patch.object(native_entry, "current_principal", current_principal),
        ]
        for patcher in self._patchers:
            patcher.start()
            testcase.addCleanup(patcher.stop)

    def _seal_test_root(self) -> None:
        """Remove inherited grants and allow only this user plus system admins."""

        principal = current_principal()
        completed = subprocess.run(
            [
                "icacls",
                str(self.root),
                "/inheritance:r",
                "/grant:r",
                f"{principal}:(OI)(CI)F",
                "/grant:r",
                "NT AUTHORITY\\SYSTEM:(OI)(CI)F",
                "/grant:r",
                "BUILTIN\\Administrators:(OI)(CI)F",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
            shell=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.decode("mbcs", errors="replace")
            raise RuntimeError(f"icacls failed to seal test root: {detail}")

    @property
    def authorization_sha(self) -> str:
        return hashlib.sha256(self.authorization.read_bytes()).hexdigest()

    def _set_owner_state(self, state: str) -> None:
        now = int(datetime.now(timezone.utc).timestamp())
        if state == "OPEN":
            payload = {
                "schema": "OwnerSigningWindow@1",
                "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
                "scope": [
                    "b0_source_read_authority",
                    "sqs_thc_ph01_e00",
                ],
                "expires_at": now + 1800,
                "max_ops": 100,
                "ops_used": 0,
                "effect_class_ceiling": "READ_ONLY_PROBE",
                "state": state,
                "window_id": "WIN-test-0001",
                "owner_fingerprint": "test-fingerprint",
            }
        elif state == "EXPIRED":
            payload = {
                "schema": "OwnerSigningWindow@1",
                "task_id": "SST_PLP_PH01_W0_B0_SOURCE_READ_AUTH",
                "scope": [
                    "b0_source_read_authority",
                    "sqs_thc_ph01_e00",
                ],
                "expires_at": now - 1,
                "max_ops": 100,
                "ops_used": 0,
                "effect_class_ceiling": "READ_ONLY_PROBE",
                "state": "OPEN",
                "window_id": "WIN-test-0001",
                "owner_fingerprint": "test-fingerprint",
            }
        else:
            payload = {"state": state}
        self.owner.write_text(
            json.dumps(payload, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def set_owner_window(self, payload: bytes | str | dict[str, Any]) -> None:
        if isinstance(payload, dict):
            encoded = (
                json.dumps(payload, separators=(",", ":")) + "\n"
            ).encode("utf-8")
        elif isinstance(payload, str):
            encoded = payload.encode("utf-8")
        else:
            encoded = payload
        self.owner.write_bytes(encoded)

    def add_source(
        self,
        source_id: str,
        payload: bytes,
        *,
        required_fields: tuple[str, ...] = ("read",),
        rules: list[dict[str, Any]] | None = None,
        requirement_span: tuple[int, int] | None = None,
        context_span: tuple[int, int] | None = None,
        expected_sha: str | None = None,
        usage_evidence_ref: str | None = None,
        usage_evidence_sha: str | None = None,
        required_set_payload: bytes | None = None,
    ) -> SourceArtifacts:
        source = self.root / f"{source_id}.md"
        source.write_bytes(payload)
        source_sha = hashlib.sha256(payload).hexdigest()
        line_count = len(payload.splitlines()) or 1
        if rules is None:
            rules = [
                {
                    "field": "read",
                    "method": "MD_LABEL",
                    "source_id": source_id,
                    "span": [2, 2],
                    "prefix": LABEL,
                    "expected_literal": (
                        "<LOCAL_ONLY_REDACTED>"
                    ),
                }
            ]
        required_document = {
            "child_id": "REQ-12::AUTHOR-SPLIT-01",
            "original_id": "REQ-12",
            "owner": "isolated-test-owner",
            "polarity": "POSITIVE_READ_AND_DEV_DENY",
            "required_fields": list(required_fields),
            "required_set_spec_version": "B0RequiredSetSpec/1",
            "requiredness": "ISOLATED_TEST_ONLY",
            "requirement_ref": str(source),
            "requirement_sha": source_sha,
            "requirement_span": list(requirement_span or (1, line_count)),
            "rules": rules,
        }
        required_path = self.root / f"{source_id}.required-set.json"
        required_payload = required_set_payload or (
            json.dumps(
                required_document,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        required_path.write_bytes(required_payload)
        required_sha = hashlib.sha256(required_payload).hexdigest()
        artifacts = SourceArtifacts(
            source_id=source_id,
            source=source,
            required_set=required_path,
            payload=payload,
            source_sha=source_sha,
        )
        self.sources[source_id] = artifacts
        self._descriptor_sources = [
            item
            for item in self._descriptor_sources
            if item["source_id"] != source_id
        ]
        self._descriptor_sources.append(
            {
                "allowed_root": str(self.root),
                "expected_sha": expected_sha or source_sha,
                "locator": str(source),
                "namespace": "isolated/SST",
                "required_set": {
                    "ref": str(required_path),
                    "sha": required_sha,
                    "span": list(
                        context_span or requirement_span or (1, line_count)
                    ),
                },
                "revocation_check_ref": str(self.owner),
                "source_id": source_id,
                "source_owner": "isolated-test-owner",
                "source_version": "v-isolated",
                "usage_evidence_ref": usage_evidence_ref
                or str(self.authorization),
                "usage_evidence_sha": usage_evidence_sha
                or self.authorization_sha,
            }
        )
        return artifacts

    def publish_descriptor(
        self,
        *,
        expires_delta: timedelta = timedelta(minutes=30),
        state: str = "OPEN",
        source_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> bytes:
        now = datetime.now(timezone.utc)
        sources = json.loads(json.dumps(self._descriptor_sources))
        for source_id, changes in (source_overrides or {}).items():
            source = next(
                item for item in sources if item["source_id"] == source_id
            )
            source.update(changes)
        if state != "OPEN":
            self._set_owner_state(state)
        descriptor = {
            "allowed_principal": current_principal(),
            "authorization_note": "isolated test authority; not a real Owner grant",
            "authorization_ref": str(self.authorization),
            "authorization_sha": self.authorization_sha,
            "context_version": "B0TrustedContext/1",
            "epoch_note": "isolated LIVE_REVALIDATE fixture",
            "epoch_strategy": "LIVE_REVALIDATE",
            "expires_at": (now + expires_delta).isoformat(),
            "revocation_ref": str(self.owner),
            "scope": {
                "consumer_ids": ["B1", "B2", "B3"],
                "purpose": "B0 isolated SOURCE_READ test",
                "scope_id": "isolated-scope",
                "source_ids": sorted(
                    item["source_id"] for item in sources
                ),
            },
            "sources": sorted(sources, key=lambda item: item["source_id"]),
            "valid_from": (now - timedelta(minutes=1)).isoformat(),
        }
        payload = (
            json.dumps(
                descriptor,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        self.descriptor.write_bytes(payload)
        native_entry.EXPECTED_DESCRIPTOR_SHA = hashlib.sha256(
            payload
        ).hexdigest()
        native_entry.EXPECTED_DESCRIPTOR_BYTES = len(payload)
        return payload

    def resolve(self, **kwargs: Any) -> TrustedContext:
        self.publish_descriptor(**kwargs)
        return native_entry.resolve_context_for_current_principal()

    def source_override(
        self,
        source_id: str,
        **changes: Any,
    ) -> TrustedContext:
        return self.resolve(source_overrides={source_id: changes})

    def request(
        self,
        context: TrustedContext,
        source_ids: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        selected = source_ids or tuple(sorted(self.sources))
        return {
            "request_version": REQUEST_VERSION,
            "subject": SUBJECT,
            "original_wave": ORIGINAL_WAVE,
            "bid": 0,
            "effect": "SOURCE_READ",
            "write_set": [],
            "scope_id": context.scope_id,
            "sources": [
                {
                    "source_id": source_id,
                    "expected_sha": context.source(
                        source_id
                    ).expected_sha,
                    "clause_span": list(
                        context.source(source_id).required_set_span
                    ),
                }
                for source_id in sorted(selected)
            ],
        }
